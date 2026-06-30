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

    def _cpr_format_ok(self, cpr_number):
        """Tjekker CPR-format (funktion (genbrugelig kodeblok))"""
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

        adresse_linje = f"{vejnavn} {husnummer}".strip()

        if etage:
            adresse_linje += f", {etage}"

        if sidedoer:
            adresse_linje += f" {sidedoer}"

        result["adresse_linje"] = adresse_linje

        if postnummer and postdistrikt:
            result["by_postnr"] = f"{postnummer} {postdistrikt}"
        elif postnummer:
            result["by_postnr"] = postnummer
        elif postdistrikt:
            result["by_postnr"] = postdistrikt

        result["har_aktuel_adresse"] = bool(vejnavn or husnummer or postnummer)

        return self._build_kan_sendes_brev(result)

    # -------------------------------------------------
    # Aktuel navn og adresse
    # -------------------------------------------------
    def get_aktuel_navn_og_adresse(self, cpr_number, client_id, cert_path, key_path):
        """Henter aktuelt navn og adresse (funktion (genbrugelig kodeblok))"""

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

        print("🔍 DEBUG AKTUEL STATUS:", r.status_code)
        print("🔍 DEBUG AKTUEL RESPONSE:", r.text)

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
    def lookup_cpr_full(self, cpr_number, client_id, cert_path, key_path):
        """Henter fulde CPR data (funktion (genbrugelig kodeblok))"""

        if not self._cpr_format_ok(cpr_number):
            return {
                "opslag_status": self._build_kan_sendes_brev({
                    **self._empty_aktuel_result(),
                    "cpr_format_ok": False
                }),
                "data": None
            }

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

              civilstande {
                civilstandstype
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

        print("🔍 DEBUG FULL STATUS:", r.status_code)
        print("🔍 DEBUG FULL RESPONSE:", r.text)

        r.raise_for_status()

        data = r.json()
        nodes = data["data"]["CPRCustom_PublicSectorPerson"]["nodes"]

        if not nodes:
            status = self._empty_aktuel_result()
            status["cpr_format_ok"] = True
            status["findes"] = False
            data["opslag_status"] = self._build_kan_sendes_brev(status)
            return data

        data["opslag_status"] = self._build_aktuel_result(nodes[0])

        return data