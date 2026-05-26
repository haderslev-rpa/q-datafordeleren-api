# datafordeler_client.py
import requests
from datafordeler_auth import get_token


class DatafordelerClient:
    """Klient til CPR GraphQL (klasse: skabelon for objekter)"""

    def __init__(self):
        self.base_url = "https://graphql.datafordeler.dk/CPR/custom/PublicSector/v1"

    def lookup_cpr(self, cpr_number):
        """Slå borger op via CPR (metode: funktion i klasse)"""
        token = get_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        query = f"""
        query {{
          CPRCustom_PublicSectorPerson(
            input: {{
              personnummer: {{
                personnummer: {{
                  in: "{cpr_number}"
                }}
              }}
            }}
          ) {{
            nodes {{
              id
              status
              koen
              navne {{
                fornavne
                efternavn
              }}
            }}
          }}
        }}
        """

        body = {"query": query}

        r = requests.post(
            self.base_url,
            headers=headers,
            json=body
        )
        r.raise_for_status()

        return r.json()