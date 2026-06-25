### OBS OBS OBS###
#FILER ER LAVET TIL ATS HVOR INDHOLDET ER LAGT IND IND OG KØRER I DOCKER.
#DENNE KODE ER DERFOR KUN TIL AT FÅ DATA OP PÅ GITHUB

import requests  # bibliotek (HTTP-kald)
from q_datafordeleren_api.app_internal_api.gamle_app_auth import get_token  # funktion (token)


class DatafordelerClient:
    """Klient til CPR GraphQL (klasse – skabelon for API klient)"""

    def __init__(self):
        self.base_url = "https://graphql.datafordeler.dk/CPR/custom/PublicSector/v1"

    # -------------------------------------------------
    # FULL CPR DATA (samme struktur)
    # -------------------------------------------------
    def lookup_cpr_full(self, cpr_number, client_id, cert_path, key_path):

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

        print("🔍 DEBUG FULL REQUEST:", body)

        r = requests.post(
            self.base_url,
            headers=headers,
            json=body
        )

        print("🔍 DEBUG status:", r.status_code)
        print("🔍 DEBUG response:", r.text)

        r.raise_for_status()

        return r.json()

    # -------------------------------------------------
    # AKTUEL NAVN OG ADRESSE (samme struktur)
    # -------------------------------------------------
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

        print("🔍 DEBUG SIMPLE REQUEST:", body)

        r = requests.post(
            self.base_url,
            headers=headers,
            json=body
        )

        print("🔍 DEBUG status:", r.status_code)
        print("🔍 DEBUG response:", r.text)

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