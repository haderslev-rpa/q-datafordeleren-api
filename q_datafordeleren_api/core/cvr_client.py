import requests

from q_datafordeleren_api.core.datafordeler_auth import (
    get_token
)


class CvrClient:
    """
    Klient til CVR GraphQL.

    Klienten understøtter:

    1. Grundlæggende virksomhedsopslag via CVR.
    2. CVRPerson-opslag via CPR.

    Datafordelerens entitetsbaserede CVR GraphQL
    tillader kun ét root field pr. forespørgsel.

    Virksomhedsopslaget sender derfor separate
    forespørgsler til:

    - CVR_Virksomhed
    - CVR_Navn
    - CVR_Adressering
    - CVR_Branche
    - CVR_Virksomhedsform
    - CVR_Telefonnummer
    - CVR_e_mailadresse
    - CVR_Reklamebeskyttelse

    CPR-opslaget returnerer kun de dokumenterede
    CVRPerson-oplysninger.

    CPR-opslaget forsøger ikke at udlede:

    - CVR-nummer
    - virksomhed
    - ejerandel
    - direktørroller
    - bestyrelsesroller
    """

    def __init__(self):
        """
        Opretter CVR-klienten.
        """

        self.base_url = (
            "https://graphql.datafordeler.dk/CVR/v2"
        )

    # -------------------------------------------------
    # Generelle hjælpefunktioner
    # -------------------------------------------------

    def _txt(self, value):
        """
        Konverterer None til tom tekst.
        """

        if value is None:
            return ""

        return value

    def _escape_graphql_string(self, value):
        """
        Gør tekst sikker til GraphQL.
        """

        return (
            str(value)
            .replace("\\", "\\\\")
            .replace('"', '\\"')
        )

    def _normaliser_cvr(self, cvr_number):
        """
        Normaliserer CVR-nummeret.

        Fjerner:
        - mellemrum
        - bindestreg
        """

        if cvr_number is None:
            return ""

        return (
            str(cvr_number)
            .replace(" ", "")
            .replace("-", "")
            .strip()
        )

    def _cvr_format_ok(self, cvr_number):
        """
        Kontrollerer, om CVR består af otte cifre.
        """

        cvr_number = self._normaliser_cvr(
            cvr_number
        )

        return (
            bool(cvr_number)
            and cvr_number.isdigit()
            and len(cvr_number) == 8
        )

    def _normaliser_cpr(self, cpr_number):
        """
        Normaliserer CPR-nummeret.

        Fjerner:
        - mellemrum
        - bindestreg
        """

        if cpr_number is None:
            return ""

        return (
            str(cpr_number)
            .replace(" ", "")
            .replace("-", "")
            .strip()
        )

    def _cpr_format_ok(self, cpr_number):
        """
        Kontrollerer, om CPR består af ti cifre.
        """

        cpr_number = self._normaliser_cpr(
            cpr_number
        )

        return (
            bool(cpr_number)
            and cpr_number.isdigit()
            and len(cpr_number) == 10
        )

    def _get_headers(
        self,
        client_id,
        cert_path,
        key_path
    ):
        """
        Henter token og bygger HTTP-headere.
        """

        token = get_token(
            client_id,
            cert_path,
            key_path
        )

        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": (
                "application/graphql-response+json, "
                "application/json"
            )
        }

    # -------------------------------------------------
    # Send GraphQL-query
    # -------------------------------------------------

    def _send_query(self, query, headers):
        """
        Sender én GraphQL-query.

        Funktionen kontrollerer:

        - HTTP-svar
        - JSON-format
        - GraphQL-fejl
        """

        response = requests.post(
            self.base_url,
            headers=headers,
            json={
                "query": query
            },
            timeout=60
        )

        try:
            response_data = response.json()

        except ValueError as error:
            raise RuntimeError(
                "CVR returnerede ikke gyldig JSON. "
                f"HTTP-status: {response.status_code}. "
                f"Svar: {response.text[:1000]}"
            ) from error

        if response_data.get("errors"):
            error_messages = [
                error.get(
                    "message",
                    "Ukendt GraphQL-fejl"
                )
                for error in response_data["errors"]
            ]

            raise RuntimeError(
                "CVR GraphQL-fejl: "
                + " | ".join(error_messages)
            )

        response.raise_for_status()

        return response_data

    def _get_nodes(
        self,
        response_data,
        root_field
    ):
        """
        Henter nodes-listen fra GraphQL-svaret.
        """

        return (
            response_data
            .get("data", {})
            .get(root_field, {})
            .get("nodes", [])
            or []
        )

    def _send_optional_query(
        self,
        query,
        headers,
        root_field
    ):
        """
        Sender et valgfrit relateret opslag.

        Hvis eksempelvis et telefonopslag fejler,
        kan virksomhedens øvrige oplysninger stadig
        returneres.
        """

        try:
            response_data = self._send_query(
                query=query,
                headers=headers
            )

            return {
                "ok": True,
                "nodes": self._get_nodes(
                    response_data,
                    root_field
                ),
                "error": ""
            }

        except Exception as error:
            return {
                "ok": False,
                "nodes": [],
                "error": str(error)
            }

    # -------------------------------------------------
    # Aktuelle poster
    # -------------------------------------------------

    def _find_current_items(self, items):
        """
        Finder poster uden virkningTil.

        En tom virkningTil betyder normalt,
        at posten fortsat er gældende.
        """

        return [
            item
            for item in items or []
            if not item.get("virkningTil")
        ]

    def _find_current_item(self, items):
        """
        Finder den nyeste aktuelle post.
        """

        current_items = self._find_current_items(
            items
        )

        candidates = (
            current_items
            or items
            or []
        )

        if not candidates:
            return {}

        return sorted(
            candidates,
            key=lambda item: (
                item.get("virkningFra")
                or ""
            ),
            reverse=True
        )[0]

    # -------------------------------------------------
    # Standardresultat for CVR
    # -------------------------------------------------

    def _empty_cvr_result(self, cvr_number=""):
        """
        Returnerer en fast CVR-resultatstruktur.
        """

        return {
            "findes": False,
            "cvr_format_ok": False,

            "cvr_nummer": cvr_number,
            "cvr_enheds_id": "",

            "virksomhedsnavn": "",
            "status": "",
            "er_aktiv": False,

            "virksomhed_startdato": "",
            "virksomhed_ophoersdato": "",

            "virksomhedsform": {
                "kode": "",
                "tekst": ""
            },

            "hovedbranche": {
                "kode": "",
                "tekst": ""
            },

            "bibrancher": [],

            "aktuel_adresse": {
                "adresse": "",
                "dar_adresse_id": "",
                "co_navn": "",
                "vejnavn": "",
                "husnummer_fra": "",
                "husnummer_til": "",
                "etage": "",
                "doer": "",
                "postnummer": "",
                "postdistrikt": "",
                "kommune_kode": "",
                "kommune_navn": "",
                "landekode": ""
            },

            "telefonnumre": [],
            "emailadresser": [],

            "reklamebeskyttet": False,

            "historik": {
                "navne": [],
                "adresser": [],
                "brancher": [],
                "virksomhedsformer": [],
                "telefonnumre": [],
                "emailadresser": [],
                "reklamebeskyttelse": []
            },

            "opslag_status": {
                "navne": {
                    "ok": False,
                    "error": ""
                },
                "adresser": {
                    "ok": False,
                    "error": ""
                },
                "brancher": {
                    "ok": False,
                    "error": ""
                },
                "virksomhedsformer": {
                    "ok": False,
                    "error": ""
                },
                "telefonnumre": {
                    "ok": False,
                    "error": ""
                },
                "emailadresser": {
                    "ok": False,
                    "error": ""
                },
                "reklamebeskyttelse": {
                    "ok": False,
                    "error": ""
                }
            },

            "raadata": {
                "virksomhed": [],
                "relationer": {}
            }
        }

    # -------------------------------------------------
    # CVR-query: virksomhed
    # -------------------------------------------------

    def _build_virksomhed_query(
        self,
        cvr_number
    ):
        """
        Bygger virksomhedsopslag via CVR-nummer.
        """

        return f"""
        query {{
          CVR_Virksomhed(
            first: 10
            where: {{
              CVRNummer: {{
                eq: {int(cvr_number)}
              }}
            }}
          ) {{
            pageInfo {{
              hasNextPage
              endCursor
            }}

            nodes {{
              CVRNummer
              datafordelerOpdateringstid
              id
              registreringFra
              registreringTil
              status
              virkningFra
              virkningTil
              virksomhedStartdato
              virksomhedOphoersdato
            }}
          }}
        }}
        """

    # -------------------------------------------------
    # CVR-query: navn
    # -------------------------------------------------

    def _build_navn_query(
        self,
        cvr_enheds_id
    ):
        """
        Bygger opslag på virksomhedsnavne.
        """

        safe_id = self._escape_graphql_string(
            cvr_enheds_id
        )

        return f"""
        query {{
          CVR_Navn(
            first: 100
            where: {{
              CVREnhedsId: {{
                eq: "{safe_id}"
              }}
            }}
          ) {{
            nodes {{
              CVREnhedsId
              sekvens
              vaerdi
              virkningFra
              virkningTil
              registreringFra
              registreringTil
            }}
          }}
        }}
        """

    # -------------------------------------------------
    # CVR-query: adresser
    # -------------------------------------------------

    def _build_adressering_query(
        self,
        cvr_enheds_id
    ):
        """
        Bygger opslag på virksomhedens adresser.
        """

        safe_id = self._escape_graphql_string(
            cvr_enheds_id
        )

        return f"""
        query {{
          CVR_Adressering(
            first: 100
            where: {{
              CVREnhedsId: {{
                eq: "{safe_id}"
              }}
            }}
          ) {{
            nodes {{
              Adresse
              AdresseringAnvendelse
              coNavn

              CVRAdresse_adresseFritekst
              CVRAdresse_doerbetegnelse
              CVRAdresse_etagebetegnelse
              CVRAdresse_husnummerFra
              CVRAdresse_husnummerTil
              CVRAdresse_kommunekode
              CVRAdresse_kommunenavn
              CVRAdresse_landekode
              CVRAdresse_postboks
              CVRAdresse_postdistrikt
              CVRAdresse_postnummer
              CVRAdresse_supplerendeBynavn
              CVRAdresse_vejkode
              CVRAdresse_vejnavn

              CVREnhedsId
              virkningFra
              virkningTil
              registreringFra
              registreringTil
            }}
          }}
        }}
        """

    # -------------------------------------------------
    # CVR-query: brancher
    # -------------------------------------------------

    def _build_branche_query(
        self,
        cvr_enheds_id
    ):
        """
        Bygger opslag på virksomhedens brancher.
        """

        safe_id = self._escape_graphql_string(
            cvr_enheds_id
        )

        return f"""
        query {{
          CVR_Branche(
            first: 100
            where: {{
              CVREnhedsId: {{
                eq: "{safe_id}"
              }}
            }}
          ) {{
            nodes {{
              CVREnhedsId
              sekvens
              vaerdi
              vaerdiTekst
              virkningFra
              virkningTil
              registreringFra
              registreringTil
            }}
          }}
        }}
        """

    # -------------------------------------------------
    # CVR-query: virksomhedsform
    # -------------------------------------------------

    def _build_virksomhedsform_query(
        self,
        cvr_enheds_id
    ):
        """
        Bygger opslag på virksomhedsformer.
        """

        safe_id = self._escape_graphql_string(
            cvr_enheds_id
        )

        return f"""
        query {{
          CVR_Virksomhedsform(
            first: 100
            where: {{
              CVREnhedsId: {{
                eq: "{safe_id}"
              }}
            }}
          ) {{
            nodes {{
              CVREnhedsId
              vaerdi
              vaerdiTekst
              virkningFra
              virkningTil
              registreringFra
              registreringTil
            }}
          }}
        }}
        """

    # -------------------------------------------------
    # CVR-query: telefonnumre
    # -------------------------------------------------

    def _build_telefon_query(
        self,
        cvr_enheds_id
    ):
        """
        Bygger opslag på telefonnumre.
        """

        safe_id = self._escape_graphql_string(
            cvr_enheds_id
        )

        return f"""
        query {{
          CVR_Telefonnummer(
            first: 100
            where: {{
              CVREnhedsId: {{
                eq: "{safe_id}"
              }}
            }}
          ) {{
            nodes {{
              CVREnhedsId
              vaerdi
              virkningFra
              virkningTil
              registreringFra
              registreringTil
            }}
          }}
        }}
        """

    # -------------------------------------------------
    # CVR-query: e-mailadresser
    # -------------------------------------------------

    def _build_email_query(
        self,
        cvr_enheds_id
    ):
        """
        Bygger opslag på e-mailadresser.
        """

        safe_id = self._escape_graphql_string(
            cvr_enheds_id
        )

        return f"""
        query {{
          CVR_e_mailadresse(
            first: 100
            where: {{
              CVREnhedsId: {{
                eq: "{safe_id}"
              }}
            }}
          ) {{
            nodes {{
              CVREnhedsId
              vaerdi
              virkningFra
              virkningTil
              registreringFra
              registreringTil
            }}
          }}
        }}
        """

    # -------------------------------------------------
    # CVR-query: reklamebeskyttelse
    # -------------------------------------------------

    def _build_reklamebeskyttelse_query(
        self,
        cvr_enheds_id
    ):
        """
        Bygger opslag på reklamebeskyttelse.
        """

        safe_id = self._escape_graphql_string(
            cvr_enheds_id
        )

        return f"""
        query {{
          CVR_Reklamebeskyttelse(
            first: 100
            where: {{
              CVREnhedsId: {{
                eq: "{safe_id}"
              }}
            }}
          ) {{
            nodes {{
              CVREnhedsId
              vaerdi
              virkningFra
              virkningTil
              registreringFra
              registreringTil
            }}
          }}
        }}
        """

    # -------------------------------------------------
    # Byg virksomhedsnavn
    # -------------------------------------------------

    def _build_company_name(self, names):
        """
        Finder virksomhedens aktuelle navn.
        """

        current_name = self._find_current_item(
            names
        )

        return self._txt(
            current_name.get("vaerdi")
        )

    # -------------------------------------------------
    # Byg brancher
    # -------------------------------------------------

    def _build_branches(self, branches):
        """
        Bygger hovedbranche og bibrancher.

        Sekvens 0 behandles som hovedbranche.
        """

        current_branches = (
            self._find_current_items(
                branches
            )
        )

        main_branch = next(
            (
                item
                for item in current_branches
                if item.get("sekvens") == 0
            ),
            {}
        )

        secondary_branches = [
            {
                "sekvens": item.get(
                    "sekvens"
                ),
                "kode": self._txt(
                    item.get("vaerdi")
                ),
                "tekst": self._txt(
                    item.get("vaerdiTekst")
                )
            }
            for item in current_branches
            if item.get("sekvens") != 0
        ]

        return {
            "hovedbranche": {
                "kode": self._txt(
                    main_branch.get("vaerdi")
                ),
                "tekst": self._txt(
                    main_branch.get(
                        "vaerdiTekst"
                    )
                )
            },
            "bibrancher": secondary_branches
        }

    # -------------------------------------------------
    # Byg læsbar adresse
    # -------------------------------------------------

    def _build_address_line(
        self,
        address
    ):
        """
        Bygger en læsbar adresselinje.

        Feltet Adresse fra CVR kan indeholde et
        DAR-id frem for en læsbar adresse.
        Derfor bygges adressen fra de strukturerede
        adressefelter.
        """

        free_text_address = self._txt(
            address.get(
                "CVRAdresse_adresseFritekst"
            )
        ).strip()

        if free_text_address:
            return free_text_address

        road_name = self._txt(
            address.get(
                "CVRAdresse_vejnavn"
            )
        ).strip()

        house_number_from = self._txt(
            address.get(
                "CVRAdresse_husnummerFra"
            )
        ).strip()

        house_number_to = self._txt(
            address.get(
                "CVRAdresse_husnummerTil"
            )
        ).strip()

        floor = self._txt(
            address.get(
                "CVRAdresse_etagebetegnelse"
            )
        ).strip()

        door = self._txt(
            address.get(
                "CVRAdresse_doerbetegnelse"
            )
        ).strip()

        house_number = house_number_from

        if (
            house_number_from
            and house_number_to
        ):
            house_number = (
                f"{house_number_from}"
                f"-{house_number_to}"
            )

        address_line = " ".join(
            value
            for value in [
                road_name,
                house_number
            ]
            if value
        )

        floor_and_door = " ".join(
            value
            for value in [
                floor,
                door
            ]
            if value
        )

        if floor_and_door:
            if address_line:
                address_line = (
                    f"{address_line}, "
                    f"{floor_and_door}"
                )
            else:
                address_line = floor_and_door

        return address_line

    def _build_address(self, addresses):
        """
        Bygger den aktuelle beliggenhedsadresse.
        """

        current_addresses = (
            self._find_current_items(
                addresses
            )
        )

        location_addresses = [
            item
            for item in current_addresses
            if (
                item.get(
                    "AdresseringAnvendelse"
                )
                or ""
            ).lower() == "beliggenhedsadresse"
        ]

        current_address = self._find_current_item(
            location_addresses
            or current_addresses
            or addresses
        )

        if not current_address:
            return (
                self
                ._empty_cvr_result()
                ["aktuel_adresse"]
            )

        return {
            "adresse": self._build_address_line(
                current_address
            ),
            "dar_adresse_id": self._txt(
                current_address.get("Adresse")
            ),
            "co_navn": self._txt(
                current_address.get("coNavn")
            ),
            "vejnavn": self._txt(
                current_address.get(
                    "CVRAdresse_vejnavn"
                )
            ),
            "husnummer_fra": self._txt(
                current_address.get(
                    "CVRAdresse_husnummerFra"
                )
            ),
            "husnummer_til": self._txt(
                current_address.get(
                    "CVRAdresse_husnummerTil"
                )
            ),
            "etage": self._txt(
                current_address.get(
                    "CVRAdresse_etagebetegnelse"
                )
            ),
            "doer": self._txt(
                current_address.get(
                    "CVRAdresse_doerbetegnelse"
                )
            ),
            "postnummer": self._txt(
                current_address.get(
                    "CVRAdresse_postnummer"
                )
            ),
            "postdistrikt": self._txt(
                current_address.get(
                    "CVRAdresse_postdistrikt"
                )
            ),
            "kommune_kode": self._txt(
                current_address.get(
                    "CVRAdresse_kommunekode"
                )
            ),
            "kommune_navn": self._txt(
                current_address.get(
                    "CVRAdresse_kommunenavn"
                )
            ),
            "landekode": self._txt(
                current_address.get(
                    "CVRAdresse_landekode"
                )
            )
        }

    # -------------------------------------------------
    # Byg reklamebeskyttelse
    # -------------------------------------------------

    def _build_ad_protection(
        self,
        ad_protection_items
    ):
        """
        Finder den aktuelle reklamebeskyttelse.
        """

        current_item = self._find_current_item(
            ad_protection_items
        )

        value = current_item.get("vaerdi")

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().lower() in {
                "true",
                "1",
                "ja",
                "yes"
            }

        return bool(value)

    # -------------------------------------------------
    # Offentlig funktion: CVR-opslag
    # -------------------------------------------------

    def lookup_cvr_basic(
        self,
        cvr_number,
        client_id,
        cert_path,
        key_path
    ):
        """
        Henter grundlæggende virksomhedsdata.

        Resultatet er JSON-kompatibelt.
        Der gemmes ingen filer.
        """

        cvr_number = self._normaliser_cvr(
            cvr_number
        )

        result = self._empty_cvr_result(
            cvr_number
        )

        if not self._cvr_format_ok(
            cvr_number
        ):
            return result

        result["cvr_format_ok"] = True

        headers = self._get_headers(
            client_id=client_id,
            cert_path=cert_path,
            key_path=key_path
        )

        # ---------------------------------------------
        # 1. Hent virksomhed
        # ---------------------------------------------

        company_response = self._send_query(
            query=self._build_virksomhed_query(
                cvr_number
            ),
            headers=headers
        )

        companies = self._get_nodes(
            response_data=company_response,
            root_field="CVR_Virksomhed"
        )

        if not companies:
            return result

        company = self._find_current_item(
            companies
        )

        if not company:
            company = companies[0]

        cvr_entity_id = self._txt(
            company.get("id")
        )

        result["findes"] = True
        result["cvr_enheds_id"] = (
            cvr_entity_id
        )

        result["status"] = self._txt(
            company.get("status")
        )

        result["er_aktiv"] = (
            result["status"].lower()
            == "aktiv"
        )

        result["virksomhed_startdato"] = (
            self._txt(
                company.get(
                    "virksomhedStartdato"
                )
            )
        )

        result["virksomhed_ophoersdato"] = (
            self._txt(
                company.get(
                    "virksomhedOphoersdato"
                )
            )
        )

        result["raadata"]["virksomhed"] = (
            companies
        )

        if not cvr_entity_id:
            return result

        # ---------------------------------------------
        # 2. Hent relaterede entiteter separat
        # ---------------------------------------------

        query_definitions = {
            "navne": {
                "root_field": "CVR_Navn",
                "query": self._build_navn_query(
                    cvr_entity_id
                )
            },
            "adresser": {
                "root_field": "CVR_Adressering",
                "query": (
                    self._build_adressering_query(
                        cvr_entity_id
                    )
                )
            },
            "brancher": {
                "root_field": "CVR_Branche",
                "query": self._build_branche_query(
                    cvr_entity_id
                )
            },
            "virksomhedsformer": {
                "root_field": (
                    "CVR_Virksomhedsform"
                ),
                "query": (
                    self
                    ._build_virksomhedsform_query(
                        cvr_entity_id
                    )
                )
            },
            "telefonnumre": {
                "root_field": (
                    "CVR_Telefonnummer"
                ),
                "query": self._build_telefon_query(
                    cvr_entity_id
                )
            },
            "emailadresser": {
                "root_field": (
                    "CVR_e_mailadresse"
                ),
                "query": self._build_email_query(
                    cvr_entity_id
                )
            },
            "reklamebeskyttelse": {
                "root_field": (
                    "CVR_Reklamebeskyttelse"
                ),
                "query": (
                    self
                    ._build_reklamebeskyttelse_query(
                        cvr_entity_id
                    )
                )
            }
        }

        related_results = {}

        for name, definition in (
            query_definitions.items()
        ):
            query_result = (
                self._send_optional_query(
                    query=definition["query"],
                    headers=headers,
                    root_field=(
                        definition["root_field"]
                    )
                )
            )

            related_results[name] = (
                query_result
            )

            result["opslag_status"][name] = {
                "ok": query_result["ok"],
                "error": query_result["error"]
            }

        # ---------------------------------------------
        # 3. Hent lister fra svar
        # ---------------------------------------------

        names = related_results[
            "navne"
        ]["nodes"]

        addresses = related_results[
            "adresser"
        ]["nodes"]

        branches = related_results[
            "brancher"
        ]["nodes"]

        company_forms = related_results[
            "virksomhedsformer"
        ]["nodes"]

        phone_numbers = related_results[
            "telefonnumre"
        ]["nodes"]

        email_addresses = related_results[
            "emailadresser"
        ]["nodes"]

        ad_protection = related_results[
            "reklamebeskyttelse"
        ]["nodes"]

        # ---------------------------------------------
        # 4. Byg normaliseret resultat
        # ---------------------------------------------

        branch_result = self._build_branches(
            branches
        )

        current_company_form = (
            self._find_current_item(
                company_forms
            )
        )

        result["virksomhedsnavn"] = (
            self._build_company_name(
                names
            )
        )

        result["virksomhedsform"] = {
            "kode": self._txt(
                current_company_form.get(
                    "vaerdi"
                )
            ),
            "tekst": self._txt(
                current_company_form.get(
                    "vaerdiTekst"
                )
            )
        }

        result["hovedbranche"] = (
            branch_result["hovedbranche"]
        )

        result["bibrancher"] = (
            branch_result["bibrancher"]
        )

        result["aktuel_adresse"] = (
            self._build_address(
                addresses
            )
        )

        result["telefonnumre"] = [
            item.get("vaerdi")
            for item in self._find_current_items(
                phone_numbers
            )
            if item.get("vaerdi")
        ]

        result["emailadresser"] = [
            item.get("vaerdi")
            for item in self._find_current_items(
                email_addresses
            )
            if item.get("vaerdi")
        ]

        result["reklamebeskyttet"] = (
            self._build_ad_protection(
                ad_protection
            )
        )

        # ---------------------------------------------
        # 5. Historik og rådata
        # ---------------------------------------------

        result["historik"] = {
            "navne": names,
            "adresser": addresses,
            "brancher": branches,
            "virksomhedsformer": company_forms,
            "telefonnumre": phone_numbers,
            "emailadresser": email_addresses,
            "reklamebeskyttelse": (
                ad_protection
            )
        }

        result["raadata"]["relationer"] = {
            name: {
                "ok": query_result["ok"],
                "error": query_result["error"],
                "nodes": query_result["nodes"]
            }
            for name, query_result
            in related_results.items()
        }

        return result

    # -------------------------------------------------
    # Standardresultat for CVRPerson
    # -------------------------------------------------

    def _empty_cvr_person_result(self):
        """
        Returnerer en fast CVRPerson-struktur.

        CPR-nummeret returneres ikke.
        """

        return {
            "findes_i_cvr": False,
            "cpr_format_ok": False,
            "antal_cvrperson_poster": 0,
            "aktuel_cvrperson": None,
            "cvrpersoner": []
        }

    # -------------------------------------------------
    # CVRPerson-query
    # -------------------------------------------------

    def _build_cvr_person_query(
        self,
        cpr_number
    ):
        """
        Bygger CVRPerson-opslag via CPR-nummer.

        CVRPerson kræver godkendt adgang.
        """

        safe_cpr = self._escape_graphql_string(
            cpr_number
        )

        return f"""
        query {{
          CVR_CVRPerson(
            first: 100
            where: {{
              CPRPerson: {{
                eq: "{safe_cpr}"
              }}
            }}
          ) {{
            pageInfo {{
              hasNextPage
              endCursor
            }}

            nodes {{
              id
              status
              virkningFra
              virkningTil
              registreringFra
              registreringTil
            }}
          }}
        }}
        """

    # -------------------------------------------------
    # Normaliser CVRPerson-post
    # -------------------------------------------------

    def _normalise_cvr_person(
        self,
        person
    ):
        """
        Normaliserer én CVRPerson-post.

        CPR-nummeret medtages ikke.
        """

        return {
            "cvrperson_id": self._txt(
                person.get("id")
            ),
            "status": self._txt(
                person.get("status")
            ),
            "virkning_fra": self._txt(
                person.get("virkningFra")
            ),
            "virkning_til": self._txt(
                person.get("virkningTil")
            ),
            "registrering_fra": self._txt(
                person.get("registreringFra")
            ),
            "registrering_til": self._txt(
                person.get("registreringTil")
            )
        }

    # -------------------------------------------------
    # Offentlig funktion: CPR til CVRPerson
    # -------------------------------------------------

    def lookup_cpr_in_cvr(
        self,
        cpr_number,
        client_id,
        cert_path,
        key_path
    ):
        """
        Undersøger, om et CPR-nummer findes i CVR.

        Funktionen returnerer:

        - om personen findes i CVR
        - personens interne CVRPerson-id
        - status
        - virkningsdatoer
        - registreringsdatoer

        Funktionen returnerer ikke:

        - selve CPR-nummeret
        - CVR-nummer
        - virksomheder
        - ejerandele
        - direktørroller
        - bestyrelsesroller

        Resultatet er JSON-kompatibelt.
        Der gemmes ingen filer.
        """

        result = self._empty_cvr_person_result()

        cpr_number = self._normaliser_cpr(
            cpr_number
        )

        if not self._cpr_format_ok(
            cpr_number
        ):
            return result

        result["cpr_format_ok"] = True

        headers = self._get_headers(
            client_id=client_id,
            cert_path=cert_path,
            key_path=key_path
        )

        response_data = self._send_query(
            query=self._build_cvr_person_query(
                cpr_number
            ),
            headers=headers
        )

        raw_cvr_persons = self._get_nodes(
            response_data=response_data,
            root_field="CVR_CVRPerson"
        )

        normalised_persons = [
            self._normalise_cvr_person(
                person
            )
            for person in raw_cvr_persons
        ]

        result["findes_i_cvr"] = bool(
            normalised_persons
        )

        result["antal_cvrperson_poster"] = len(
            normalised_persons
        )

        result["cvrpersoner"] = (
            normalised_persons
        )

        current_raw_person = (
            self._find_current_item(
                raw_cvr_persons
            )
        )

        if current_raw_person:
            result["aktuel_cvrperson"] = (
                self._normalise_cvr_person(
                    current_raw_person
                )
            )

        return result