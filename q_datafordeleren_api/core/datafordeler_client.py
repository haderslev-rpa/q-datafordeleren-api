import requests
from q_datafordeleren_api.core.datafordeler_auth import get_token


class DatafordelerClient:

    def __init__(self):
        self.base_url = "https://graphql.datafordeler.dk/CPR/custom/PublicSector/v1"

    def get_aktuel_navn_og_adresse(self, cpr_number, client_id, cert_path, key_path):

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
                  vejnavn
                  husnummer
                  etage
                  postnummer
                  bynavn
                }
                status
                virkningfra
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
            "variables": {"cpr": [cpr_number]}
        }

        r = requests.post(self.base_url, headers=headers, json=body)

        r.raise_for_status()

        data = r.json()

        node = data["data"]["CPRCustom_PublicSectorPerson"]["nodes"][0]

        navn = next((n for n in node["navne"] if n["status"] == "aktuel"), None)
        adresse = next((a for a in node["adresseoplysninger"] if a["status"] == "aktuel"), None)

        postnr_og_by = None
        if adresse:
            postnr_og_by = f"{adresse['cprAdresse']['postnummer']} {adresse['cprAdresse']['bynavn']}"

        return {
            "fornavn": navn["fornavne"] if navn else None,
            "mellemnavn": navn["mellemnavn"] if navn else None,
            "efternavn": navn["efternavn"] if navn else None,
            "vej": adresse["cprAdresse"]["vejnavn"] if adresse else None,
            "husnummer": adresse["cprAdresse"]["husnummer"] if adresse else None,
            "postnummer": adresse["cprAdresse"]["postnummer"] if adresse else None,
            "bynavn": adresse["cprAdresse"]["bynavn"] if adresse else None,
            "postnr_og_by": postnr_og_by
        }

    def lookup_cpr_full(self, cpr_number, client_id, cert_path, key_path):

        token = get_token(client_id, cert_path, key_path)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # ✅ SAMME STABILE QUERY SOM DU HAVDE FØR
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
                  vejnavn
                  husnummer
                  etage
                  postnummer
                  bynavn
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
            "variables": {"cpr": [cpr_number]}
        }

        r = requests.post(self.base_url, headers=headers, json=body)

        print("🔍 DEBUG FULL STATUS:", r.status_code)
        print("🔍 DEBUG FULL RESPONSE:", r.text)

        r.raise_for_status()

        return r.json()