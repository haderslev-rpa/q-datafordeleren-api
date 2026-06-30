import requests  # bibliotek (HTTP-kald)
from q_datafordeleren_api.core.datafordeler_auth import get_token  # funktion (genbrugelig kodeblok)


class DatafordelerClient:
    """Klient (klasse (skabelon for objekter)) til CPR GraphQL"""

    def __init__(self):
        self.base_url = "https://graphql.datafordeler.dk/CPR/custom/PublicSector/v1"

    # -------------------------------------------------
    # Tom standardstruktur til Blue Prism
    # -------------------------------------------------
    def _empty_aktuel_result(self):
        """Tom struktur (ens output hver gang)"""

        return {
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
            "by_postnr": "",

            "har_adresse": False,
            "har_navn": False
        }

    # -------------------------------------------------
    # Hjælpefunktion til at undgå None
    # -------------------------------------------------
    def _txt(self, value):
        """Konverterer None til tom tekst"""

        return value if value is not None else ""

    # -------------------------------------------------
    # Byg brev-klar adresse
    # -------------------------------------------------
    def _build_aktuel_result(self, navn, adresse):
        """Bygger output (samlet resultat) til aktuel navn og adresse"""

        result = self._empty_aktuel_result()

        # -----------------------------
        # Navn
        # -----------------------------
        if navn:
            fornavn = self._txt(navn.get("fornavne"))
            mellemnavn = self._txt(navn.get("mellemnavn"))
            efternavn = self._txt(navn.get("efternavn"))

            result["fornavn"] = fornavn
            result["mellemnavn"] = mellemnavn
            result["efternavn"] = efternavn
            result["har_navn"] = True

            navn_dele = [fornavn, mellemnavn, efternavn]
            result["navn"] = " ".join([delnavn for delnavn in navn_dele if delnavn])

        # -----------------------------
        # Adresse
        # -----------------------------
        if not adresse:
            return result

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
        # Brev-klar adresselinje
        # -----------------------------
        adresse_linje = f"{vejnavn} {husnummer}".strip()

        if etage:
            adresse_linje += f", {etage}"

        if sidedoer:
            adresse_linje += f" {sidedoer}"

        result["adresse_linje"] = adresse_linje

        # -----------------------------
        # Postnummer + postdistrikt
        # -----------------------------
        if postnummer and postdistrikt:
            result["by_postnr"] = f"{postnummer} {postdistrikt}"
        elif postnummer:
            result["by_postnr"] = postnummer
        elif postdistrikt:
            result["by_postnr"] = postdistrikt
        else:
            result["by_postnr"] = ""

        result["har_adresse"] = bool(vejnavn or husnummer or postnummer)

        return result

    # -------------------------------------------------
    # Aktuel navn og adresse
    # -------------------------------------------------
    def get_aktuel_navn_og_adresse(self, cpr_number, client_id, cert_path, key_path):
        """Henter aktuelt navn og adresse (funktion (genbrugelig kodeblok))"""

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
            return self._empty_aktuel_result()

        node = nodes[0]

        navn = next(
            (n for n in node.get("navne", []) if n.get("status") == "aktuel"),
            None
        )

        adresse = next(
            (a for a in node.get("adresseoplysninger", []) if a.get("status") == "aktuel"),
            None
        )

        return self._build_aktuel_result(navn, adresse)

    # -------------------------------------------------
    # Full CPR data
    # -------------------------------------------------
    def lookup_cpr_full(self, cpr_number, client_id, cert_path, key_path):
        """Henter fulde CPR data (funktion (genbrugelig kodeblok))"""

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

        return r.json()