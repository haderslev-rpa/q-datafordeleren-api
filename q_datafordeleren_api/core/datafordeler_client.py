import requests  # bibliotek (HTTP-kald)
from q_datafordeleren_api.core.datafordeler_auth import get_token  # funktion (genbrugelig kodeblok)


class DatafordelerClient:
    """Klient (klasse (skabelon for objekter)) til CPR GraphQL"""

    def __init__(self):
        self.base_url = "https://graphql.datafordeler.dk/CPR/custom/PublicSector/v1"

    # -------------------------------------------------
    # Hjælpefunktioner
    # -------------------------------------------------
    def _txt(self, value):
        """Konverterer None til tom tekst (funktion (genbrugelig kodeblok))"""
        return value if value is not None else ""

    def _normaliser_cpr(self, cpr_number):
        """
        Normaliserer CPR-nummer.

        Fjerner:
        - bindestreg
        - mellemrum

        Eksempler:
        - "123456-7890" bliver "1234567890"
        - "123456 7890" bliver "1234567890"
        - "1234567890" forbliver "1234567890"
        """

        if cpr_number is None:
            return ""

        return str(cpr_number).replace("-", "").replace(" ", "").strip()

    def _format_etage(self, etage):
        """
        Formaterer etage til dansk adresseformat.

        Eksempler:
        - "2" bliver "2."
        - "1" bliver "1."
        - "st" bliver "st."
        - "stue" bliver "st."
        - "kl" bliver "kl."
        - "2." forbliver "2."
        """

        etage = self._txt(etage).strip()

        if not etage:
            return ""

        etage_lower = etage.lower()

        # Hvis Datafordeleren allerede sender punktum, beholdes værdien
        if etage.endswith("."):
            return etage

        # Stueetage
        if etage_lower in ["st", "stue", "stuen"]:
            return "st."

        # Kælder
        if etage_lower in ["kl", "kld", "kælder", "kaelder"]:
            return "kl."

        # Almindelige etager som tal
        if etage.isdigit():
            return f"{etage}."

        # Fallback: returnér som modtaget
        return etage

    def _cpr_format_ok(self, cpr_number):
        """Tjekker CPR-format (funktion (genbrugelig kodeblok))"""

        cpr_number = self._normaliser_cpr(cpr_number)

        return bool(cpr_number) and cpr_number.isdigit() and len(cpr_number) == 10

    def _empty_aktuel_result(self):
        """Standard output (dictionary (nøgler/værdier))"""

        return {
            "findes": False,
            "cpr_format_ok": False,

            "person_status": "",
            "er_doed": False,
            "er_udrejst": False,
            "er_bopael_i_danmark": False,

            "har_aktuel_navn": False,
            "har_aktuel_adresse": False,

            "kan_sendes_brev": False,
            "kan_sendes_brev_aarsag": "",

            "fornavn": "",
            "mellemnavn": "",
            "efternavn": "",
            "navn": "",

            "vejnavn": "",
            "vejadresseringsnavn": "",
            "husnummer": "",
            "etage": "",
            "sidedoer": "",
            "postnummer": "",
            "postdistrikt": "",
            "bynavn": "",

            "cprkommunekode": "",
            "cprkommunenavn": "",
            "cprvejkode": "",
            "daradresse": "",
            "bygningsnummer": "",

            "adresse_linje": "",
            "by_postnr": ""
        }

    def _build_status_flags(self, person_status):
        """Bygger statusfelter (funktion (genbrugelig kodeblok))"""

        status = (person_status or "").lower()

        er_doed = (
            "doed" in status
            or "død" in status
            or "afgaaet" in status
            or "afgået" in status
        )

        er_udrejst = (
            "udrejst" in status
            or "udrejse" in status
            or "bopael_i_udlandet" in status
            or "bopæl_i_udlandet" in status
        )

        return {
            "person_status": person_status or "",
            "er_doed": er_doed,
            "er_udrejst": er_udrejst,
            "er_bopael_i_danmark": person_status == "bopael_i_danmark"
        }

    def _build_kan_sendes_brev(self, result):
        """
        Sætter kan_sendes_brev (boolsk værdi) og kan_sendes_brev_aarsag (tekst).

        kan_sendes_brev bliver False når:
        - CPR-format er forkert
        - CPR ikke findes
        - personen er død
        - personen er udrejst
        - personen ikke har aktuel adresse
        """

        if not result["cpr_format_ok"]:
            result["kan_sendes_brev"] = False
            result["kan_sendes_brev_aarsag"] = "CPR-format er ugyldigt"
            return result

        if not result["findes"]:
            result["kan_sendes_brev"] = False
            result["kan_sendes_brev_aarsag"] = "CPR findes ikke"
            return result

        if result["er_doed"]:
            result["kan_sendes_brev"] = False
            result["kan_sendes_brev_aarsag"] = "Person er død"
            return result

        if result["er_udrejst"]:
            result["kan_sendes_brev"] = False
            result["kan_sendes_brev_aarsag"] = "Person er udrejst"
            return result

        if not result["har_aktuel_adresse"]:
            result["kan_sendes_brev"] = False
            result["kan_sendes_brev_aarsag"] = "Person har ingen aktuel adresse"
            return result

        result["kan_sendes_brev"] = True
        result["kan_sendes_brev_aarsag"] = ""

        return result

    def _build_aktuel_result(self, node):
        """Bygger standardresultat (funktion (genbrugelig kodeblok))"""

        result = self._empty_aktuel_result()

        result["findes"] = True
        result["cpr_format_ok"] = True

        # -----------------------------
        # Personstatus
        # -----------------------------
        status_flags = self._build_status_flags(node.get("status"))

        result.update(status_flags)

        # -----------------------------
        # Navn
        # -----------------------------
        navn = next(
            (n for n in node.get("navne", []) if n.get("status") == "aktuel"),
            None
        )

        if navn:
            fornavn = self._txt(navn.get("fornavne"))
            mellemnavn = self._txt(navn.get("mellemnavn"))
            efternavn = self._txt(navn.get("efternavn"))

            result["fornavn"] = fornavn
            result["mellemnavn"] = mellemnavn
            result["efternavn"] = efternavn
            result["har_aktuel_navn"] = True

            navn_dele = [fornavn, mellemnavn, efternavn]
            result["navn"] = " ".join([delnavn for delnavn in navn_dele if delnavn])

        # -----------------------------
        # Adresse
        # -----------------------------
        adresse = next(
            (a for a in node.get("adresseoplysninger", []) if a.get("status") == "aktuel"),
            None
        )

        if not adresse:
            return self._build_kan_sendes_brev(result)

        cpr_adresse = adresse.get("cprAdresse") or {}

        vejnavn = self._txt(cpr_adresse.get("vejnavn"))
        vejadresseringsnavn = self._txt(cpr_adresse.get("vejadresseringsnavn"))
        husnummer = self._txt(cpr_adresse.get("husnummer"))
        etage = self._txt(cpr_adresse.get("etage"))
        sidedoer = self._txt(cpr_adresse.get("sidedoer"))
        postnummer = self._txt(cpr_adresse.get("postnummer"))
        postdistrikt = self._txt(cpr_adresse.get("postdistrikt"))
        bynavn = self._txt(cpr_adresse.get("bynavn"))

        result["vejnavn"] = vejnavn
        result["vejadresseringsnavn"] = vejadresseringsnavn
        result["husnummer"] = husnummer
        result["etage"] = etage
        result["sidedoer"] = sidedoer
        result["postnummer"] = postnummer
        result["postdistrikt"] = postdistrikt
        result["bynavn"] = bynavn

        result["cprkommunekode"] = self._txt(cpr_adresse.get("cprkommunekode"))
        result["cprkommunenavn"] = self._txt(cpr_adresse.get("cprkommunenavn"))
        result["cprvejkode"] = self._txt(cpr_adresse.get("cprvejkode"))
        result["daradresse"] = self._txt(cpr_adresse.get("daradresse"))
        result["bygningsnummer"] = self._txt(cpr_adresse.get("bygningsnummer"))

        # -----------------------------
        # Adresseformat til postadresse
        # -----------------------------
        # Brug vejadresseringsnavn hvis det findes, ellers brug vejnavn
        adresse_vejnavn = vejadresseringsnavn or vejnavn

        adresse_linje = f"{adresse_vejnavn} {husnummer}".strip()

        formateret_etage = self._format_etage(etage)

        if formateret_etage and sidedoer:
            adresse_linje += f", {formateret_etage} {sidedoer}"
        elif formateret_etage:
            adresse_linje += f", {formateret_etage}"
        elif sidedoer:
            adresse_linje += f", {sidedoer}"

        result["adresse_linje"] = adresse_linje

        # -----------------------------
        # Postnummer og by
        # -----------------------------
        if postnummer and postdistrikt:
            result["by_postnr"] = f"{postnummer} {postdistrikt}"
        elif postnummer:
            result["by_postnr"] = postnummer
        elif postdistrikt:
            result["by_postnr"] = postdistrikt

        result["har_aktuel_adresse"] = bool(adresse_vejnavn or husnummer or postnummer)

        return self._build_kan_sendes_brev(result)

    # -------------------------------------------------
    # Aktuel navn og adresse
    # -------------------------------------------------
    def get_aktuel_navn_og_adresse(self, cpr_number, client_id, cert_path, key_path):
        """Henter aktuelt navn og adresse (funktion (genbrugelig kodeblok))"""

        # Fjerner bindestreg og mellemrum fra CPR før validering og opslag
        cpr_number = self._normaliser_cpr(cpr_number)

        if not self._cpr_format_ok(cpr_number):
            result = self._empty_aktuel_result()
            result["cpr_format_ok"] = False
            return self._build_kan_sendes_brev(result)

        token = get_token(client_id, cert_path, key_path)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        query = """
        query ($cpr: [String!]!) {
          CPRCustom_PublicSectorPerson(
            input: {
              personnummer: {
                personnummer: {
                  in: $cpr
                }
              }
            }
          ) {
            nodes {
              id
              status
              koen

              navne {
                fornavne
                mellemnavn
                efternavn
                status
              }

              adresseoplysninger {
                cprAdresse {
                  daradresse
                  bygningsnummer
                  bynavn
                  cprkommunekode
                  cprkommunenavn
                  cprvejkode
                  etage
                  husnummer
                  postdistrikt
                  postnummer
                  sidedoer
                  vejadresseringsnavn
                  vejnavn
                }
                status
                virkningfra
                virkningtil
              }

              beskyttelser {
                beskyttelsestype
                status
                virkningfra
                virkningtil
              }
            }
          }
        }
        """

        body = {
            "query": query,
            "variables": {
                "cpr": [cpr_number]
            }
        }

        r = requests.post(
            self.base_url,
            headers=headers,
            json=body
        )


        r.raise_for_status()

        data = r.json()

        nodes = data["data"]["CPRCustom_PublicSectorPerson"]["nodes"]

        if not nodes:
            result = self._empty_aktuel_result()
            result["cpr_format_ok"] = True
            result["findes"] = False
            return self._build_kan_sendes_brev(result)

        return self._build_aktuel_result(nodes[0])

    # -------------------------------------------------
    # Full CPR data
    # -------------------------------------------------
    def lookup_cpr_full(
        self,
        cpr_number,
        client_id,
        cert_path,
        key_path
    ):
        """
        Henter fulde CPR-data.

        Outputtet er JSON-kompatibelt og indeholder:

        - opslag_status
        - personnumre
        - statsborgerskab
        - boern
        - foraeldre
        - det rå GraphQL-resultat

        statsborgerskab indeholder:
        - aktuelt statsborgerskab
        - alle registrerede statsborgerskaber
        - landekode
        - landets navn
        - status
        - virkningsdatoer

        Der gemmes ingen filer.
        """

        # Fjerner bindestreg og mellemrum fra CPR.
        cpr_number = self._normaliser_cpr(
            cpr_number
        )

        # -------------------------------------------------
        # Ugyldigt CPR-format
        # -------------------------------------------------

        if not self._cpr_format_ok(
            cpr_number
        ):
            return {
                "opslag_status": (
                    self._build_kan_sendes_brev(
                        {
                            **self._empty_aktuel_result(),
                            "cpr_format_ok": False
                        }
                    )
                ),
                "personnumre": {
                    "opslaaet_cpr": cpr_number,
                    "aktuelt_cpr": "",
                    "har_skiftet_cpr": False,
                    "alle_personnumre": []
                },
                "statsborgerskab": {
                    "har_statsborgerskab": False,
                    "aktuelt_statsborgerskab": None,
                    "antal_statsborgerskaber": 0,
                    "alle_statsborgerskaber": []
                },
                "boern": {
                    "antal_boern": 0,
                    "boern": []
                },
                "foraeldre": {
                    "antal_foraeldre": 0,
                    "foraeldre": []
                },
                "data": None
            }

        token = get_token(
            client_id,
            cert_path,
            key_path
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": (
                "application/graphql-response+json, "
                "application/json"
            )
        }

        query = """
        query ($cpr: [String!]!) {
          CPRCustom_PublicSectorPerson(
            input: {
              personnummer: {
                personnummer: {
                  in: $cpr
                }
              }
            }
          ) {
            nodes {
              id
              status
              statusdato
              foedselsdato
              koen

              personnumre {
                personnummer
                status
                virkningfra
                virkningtil
              }

              navne {
                adresseringsnavn
                fornavne
                mellemnavn
                efternavn
                status
                virkningfra
                virkningtil
              }

              statsborgerskaber {
                cprland {
                  kode
                  navn
                  landekode

                  administrativEnhedType {
                    typeKode
                    typeNavn
                  }
                }

                status
                virkningFra
                virkningFraUsikkerhedsmarkering
                virkningTil
                virkningTilUsikkerhedsmarkering
              }

              adresseoplysninger {
                status
                virkningfra
                virkningtil

                cprAdresse {
                  daradresse
                  bygningsnummer
                  bynavn
                  cprkommunekode
                  cprkommunenavn
                  cprvejkode
                  etage
                  husnummer
                  postdistrikt
                  postnummer
                  sidedoer
                  vejadresseringsnavn
                  vejnavn
                }
              }

              beskyttelser {
                beskyttelsestype
                status
                virkningfra
                virkningtil
              }

              civilstande {
                civilstandstype
                status
                virkningfra
                virkningtil
              }

              boern {
                virkningfra

                barn {
                  personid
                  personnummer

                  beskyttelser {
                    beskyttelsestype
                    status
                    virkningfra
                    virkningtil
                  }

                  navn {
                    adresseringsnavn
                    fornavne
                    mellemnavn
                    efternavn
                    status
                  }
                }
              }

              foraeldreoplysninger {
                virkningfra
                foraelderrolle

                foraelder {
                  personid
                  personnummer

                  beskyttelser {
                    beskyttelsestype
                    status
                    virkningfra
                    virkningtil
                  }

                  navn {
                    adresseringsnavn
                    fornavne
                    mellemnavn
                    efternavn
                    status
                  }
                }

                foraelderUdenCpr {
                  personid
                  navn
                  foedselsdato
                }

                ikkeValidRelationsForaelder {
                  personid
                  personnummer
                  navn
                  foedselsdato
                }
              }
            }
          }
        }
        """

        body = {
            "query": query,
            "variables": {
                "cpr": [
                    cpr_number
                ]
            }
        }

        response = requests.post(
            self.base_url,
            headers=headers,
            json=body,
            timeout=60
        )

        try:
            data = response.json()

        except ValueError as error:
            raise RuntimeError(
                "CPR returnerede ikke gyldig JSON. "
                f"HTTP-status: {response.status_code}. "
                f"Svar: {response.text[:1000]}"
            ) from error

        if data.get("errors"):
            error_messages = [
                error.get(
                    "message",
                    "Ukendt GraphQL-fejl"
                )
                for error in data["errors"]
            ]

            raise RuntimeError(
                "CPR GraphQL-fejl: "
                + " | ".join(error_messages)
            )

        response.raise_for_status()

        nodes = (
            data
            .get("data", {})
            .get(
                "CPRCustom_PublicSectorPerson",
                {}
            )
            .get("nodes", [])
            or []
        )

        # -------------------------------------------------
        # CPR blev ikke fundet
        # -------------------------------------------------

        if not nodes:
            status = self._empty_aktuel_result()

            status["cpr_format_ok"] = True
            status["findes"] = False

            data["opslag_status"] = (
                self._build_kan_sendes_brev(
                    status
                )
            )

            data["personnumre"] = {
                "opslaaet_cpr": cpr_number,
                "aktuelt_cpr": "",
                "har_skiftet_cpr": False,
                "alle_personnumre": []
            }

            data["statsborgerskab"] = {
                "har_statsborgerskab": False,
                "aktuelt_statsborgerskab": None,
                "antal_statsborgerskaber": 0,
                "alle_statsborgerskaber": []
            }

            data["boern"] = {
                "antal_boern": 0,
                "boern": []
            }

            data["foraeldre"] = {
                "antal_foraeldre": 0,
                "foraeldre": []
            }

            return data

        # -------------------------------------------------
        # CPR blev fundet
        # -------------------------------------------------

        node = nodes[0]

        # Aktuel status, navn og adresse.
        data["opslag_status"] = (
            self._build_aktuel_result(
                node
            )
        )

        # Aktuelt og historiske CPR-numre.
        data["personnumre"] = (
            self._build_personnumre(
                personnumre=node.get(
                    "personnumre",
                    []
                ),
                opslaaet_cpr=cpr_number
            )
        )

        # Aktuelt og historiske statsborgerskaber.
        data["statsborgerskab"] = (
            self._build_statsborgerskaber(
                node.get(
                    "statsborgerskaber",
                    []
                )
            )
        )

        # Børn.
        data["boern"] = (
            self._build_boern(
                node.get(
                    "boern",
                    []
                )
            )
        )

        # Forældre.
        data["foraeldre"] = (
            self._build_foraeldre(
                node.get(
                    "foraeldreoplysninger",
                    []
                )
            )
        )

        return data

    # -------------------------------------------------
    # Byg personnummeroplysninger
    # -------------------------------------------------
    def _build_personnumre(self, personnumre, opslaaet_cpr):
        """
        Bygger en fast struktur med personnumre.

        Returnerer:
        - det CPR-nummer der blev slået op
        - det aktuelle CPR-nummer
        - om personen har skiftet CPR-nummer
        - alle registrerede CPR-numre med status og datoer

        har_skiftet_cpr bliver True når:
        - personen har mere end ét registreret CPR-nummer
        - eller det aktuelle CPR-nummer er forskelligt
          fra det CPR-nummer, der blev slået op
        """

        personnumre = personnumre or []

        aktuelt_cpr = ""

        for personnummer_oplysning in personnumre:

            status = self._txt(
                personnummer_oplysning.get("status")
            ).lower()

            if status == "aktuel":
                aktuelt_cpr = self._txt(
                    personnummer_oplysning.get("personnummer")
                )
                break

        har_skiftet_cpr = bool(
            len(personnumre) > 1
            or (
                aktuelt_cpr
                and aktuelt_cpr != opslaaet_cpr
            )
        )

        return {
            "opslaaet_cpr": opslaaet_cpr,
            "aktuelt_cpr": aktuelt_cpr,
            "har_skiftet_cpr": har_skiftet_cpr,
            "alle_personnumre": personnumre
        }

    # -------------------------------------------------
    # Byg statsborgerskabsoplysninger
    # -------------------------------------------------

    def _build_statsborgerskaber(
        self,
        statsborgerskaber
    ):
        """
        Bygger en fast struktur med statsborgerskaber.

        Outputtet er JSON-kompatibelt og indeholder:

        {
            "har_statsborgerskab": true,
            "aktuelt_statsborgerskab": {
                "kode": "",
                "land": "",
                "landekode": "",
                "status": "aktuel",
                "virkning_fra": "",
                "virkning_fra_usikker": false,
                "virkning_til": "",
                "virkning_til_usikker": false
            },
            "antal_statsborgerskaber": 1,
            "alle_statsborgerskaber": []
        }

        Det aktuelle statsborgerskab findes først via
        status = "aktuel". Hvis ingen post har denne
        status, vælges en post uden virkningTil.
        """

        normaliserede_statsborgerskaber = []

        for statsborgerskab in (
            statsborgerskaber or []
        ):
            cpr_land = (
                statsborgerskab.get(
                    "cprland"
                )
                or {}
            )

            administrativ_enhedstype = (
                cpr_land.get(
                    "administrativEnhedType"
                )
                or {}
            )

            normaliseret_statsborgerskab = {
                "kode": self._txt(
                    cpr_land.get("kode")
                ),
                "land": self._txt(
                    cpr_land.get("navn")
                ),
                "landekode": self._txt(
                    cpr_land.get("landekode")
                ),
                "administrativ_enhed_type_kode": (
                    self._txt(
                        administrativ_enhedstype.get(
                            "typeKode"
                        )
                    )
                ),
                "administrativ_enhed_type_navn": (
                    self._txt(
                        administrativ_enhedstype.get(
                            "typeNavn"
                        )
                    )
                ),
                "status": self._txt(
                    statsborgerskab.get(
                        "status"
                    )
                ),
                "virkning_fra": self._txt(
                    statsborgerskab.get(
                        "virkningFra"
                    )
                ),
                "virkning_fra_usikker": bool(
                    statsborgerskab.get(
                        "virkningFraUsikkerhedsmarkering",
                        False
                    )
                ),
                "virkning_til": self._txt(
                    statsborgerskab.get(
                        "virkningTil"
                    )
                ),
                "virkning_til_usikker": bool(
                    statsborgerskab.get(
                        "virkningTilUsikkerhedsmarkering",
                        False
                    )
                )
            }

            normaliserede_statsborgerskaber.append(
                normaliseret_statsborgerskab
            )

        aktuelt_statsborgerskab = next(
            (
                statsborgerskab
                for statsborgerskab
                in normaliserede_statsborgerskaber
                if (
                    statsborgerskab.get(
                        "status",
                        ""
                    ).lower()
                    == "aktuel"
                )
            ),
            None
        )

        # Fallback hvis status ikke er "aktuel".
        if aktuelt_statsborgerskab is None:
            aktuelt_statsborgerskab = next(
                (
                    statsborgerskab
                    for statsborgerskab
                    in normaliserede_statsborgerskaber
                    if not statsborgerskab.get(
                        "virkning_til"
                    )
                ),
                None
            )

        return {
            "har_statsborgerskab": bool(
                normaliserede_statsborgerskaber
            ),
            "aktuelt_statsborgerskab": (
                aktuelt_statsborgerskab
            ),
            "antal_statsborgerskaber": len(
                normaliserede_statsborgerskaber
            ),
            "alle_statsborgerskaber": (
                normaliserede_statsborgerskaber
            )
        }
    
    # -------------------------------------------------
    # Byg børneoplysninger
    # -------------------------------------------------
    def _build_boern(self, boern):
        """
        Bygger en fast struktur med børn.

        Returnerer:
        - antal børn
        - person-id
        - CPR-nummer
        - navn
        - virkningsdato
        - om barnet har CPR-nummer
        """

        resultat = []

        for barn_oplysning in boern or []:

            barn = barn_oplysning.get("barn") or {}

            personnummer = self._txt(
                barn.get("personnummer")
            )

            navn_data = barn.get("navn") or {}

            adresseringsnavn = self._txt(
                navn_data.get("adresseringsnavn")
            )

            if adresseringsnavn:
                navn = adresseringsnavn
            else:
                navn_dele = [
                    self._txt(navn_data.get("fornavne")),
                    self._txt(navn_data.get("mellemnavn")),
                    self._txt(navn_data.get("efternavn"))
                ]

                navn = " ".join(
                    navn_del
                    for navn_del in navn_dele
                    if navn_del
                )

            resultat.append(
                {
                    "personid": self._txt(
                        barn.get("personid")
                    ),
                    "personnummer": personnummer,
                    "navn": navn,
                    "virkningfra": self._txt(
                        barn_oplysning.get("virkningfra")
                    ),
                    "har_cpr": bool(personnummer)
                }
            )

        return {
            "antal_boern": len(resultat),
            "boern": resultat
        }

    # -------------------------------------------------
    # Byg forældreoplysninger
    # -------------------------------------------------
    def _build_foraeldre(self, foraeldreoplysninger):
        """
        Bygger en fast struktur med forældre.

        Understøtter:
        - forælder med CPR-nummer
        - forælder uden CPR-nummer
        - ikke-valid forældrerelation

        Feltet relationstype fortæller, hvilken type
        relation Datafordeleren returnerede.
        """

        resultat = []

        for relation in foraeldreoplysninger or []:

            foraelder = relation.get("foraelder")
            foraelder_uden_cpr = relation.get(
                "foraelderUdenCpr"
            )
            ikke_valid_foraelder = relation.get(
                "ikkeValidRelationsForaelder"
            )

            standard = {
                "foraelderrolle": self._txt(
                    relation.get("foraelderrolle")
                ),
                "virkningfra": self._txt(
                    relation.get("virkningfra")
                ),
                "relationstype": "",
                "personid": "",
                "personnummer": "",
                "navn": "",
                "foedselsdato": "",
                "har_cpr": False
            }

            # -----------------------------------------
            # Forælder med CPR-nummer
            # -----------------------------------------
            if foraelder:

                navn_data = foraelder.get("navn") or {}

                adresseringsnavn = self._txt(
                    navn_data.get("adresseringsnavn")
                )

                if adresseringsnavn:
                    navn = adresseringsnavn
                else:
                    navn_dele = [
                        self._txt(
                            navn_data.get("fornavne")
                        ),
                        self._txt(
                            navn_data.get("mellemnavn")
                        ),
                        self._txt(
                            navn_data.get("efternavn")
                        )
                    ]

                    navn = " ".join(
                        navn_del
                        for navn_del in navn_dele
                        if navn_del
                    )

                personnummer = self._txt(
                    foraelder.get("personnummer")
                )

                standard.update(
                    {
                        "relationstype": "person_med_cpr",
                        "personid": self._txt(
                            foraelder.get("personid")
                        ),
                        "personnummer": personnummer,
                        "navn": navn,
                        "har_cpr": bool(personnummer)
                    }
                )

            # -----------------------------------------
            # Forælder uden CPR-nummer
            # -----------------------------------------
            elif foraelder_uden_cpr:

                standard.update(
                    {
                        "relationstype": "person_uden_cpr",
                        "personid": self._txt(
                            foraelder_uden_cpr.get(
                                "personid"
                            )
                        ),
                        "personnummer": "",
                        "navn": self._txt(
                            foraelder_uden_cpr.get("navn")
                        ),
                        "foedselsdato": self._txt(
                            foraelder_uden_cpr.get(
                                "foedselsdato"
                            )
                        ),
                        "har_cpr": False
                    }
                )

            # -----------------------------------------
            # Ikke-valid forældrerelation
            # -----------------------------------------
            elif ikke_valid_foraelder:

                personnummer = self._txt(
                    ikke_valid_foraelder.get(
                        "personnummer"
                    )
                )

                standard.update(
                    {
                        "relationstype": "ikke_valid_relation",
                        "personid": self._txt(
                            ikke_valid_foraelder.get(
                                "personid"
                            )
                        ),
                        "personnummer": personnummer,
                        "navn": self._txt(
                            ikke_valid_foraelder.get("navn")
                        ),
                        "foedselsdato": self._txt(
                            ikke_valid_foraelder.get(
                                "foedselsdato"
                            )
                        ),
                        "har_cpr": bool(personnummer)
                    }
                )

            # -----------------------------------------
            # Relation uden personoplysninger
            # -----------------------------------------
            else:
                standard["relationstype"] = "ukendt_relation"

            resultat.append(standard)

        return {
            "antal_foraeldre": len(resultat),
            "foraeldre": resultat
        }