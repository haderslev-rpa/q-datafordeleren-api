from pprint import pprint

import os
import requests

from dotenv import load_dotenv

from automation_server_client import AutomationServer, Credential

from q_datafordeleren_api.core.datafordeler_auth import get_token


BASE_URL = "https://graphql.datafordeler.dk/CPR/custom/PublicSector/v1"


def get_credentials():
    """Henter credentials (hemmelige oplysninger)"""

    AutomationServer.from_environment()

    cred = Credential.get_credential("API_DATAFORDELEREN")

    return cred.data


def build_query():
    """Bygger GraphQL query (forespørgsel)"""

    return """
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

          beskyttelser {
            beskyttelsestype
            status
            virkningfra
            virkningtil
          }

          personnumre {
            personnummer
            status
            virkningfra
            virkningtil
          }
        }
      }
    }
    """


def main():

    load_dotenv()

    cpr = os.getenv("cpr1")

    if not cpr:
        print("❌ Mangler cpr1 i .env")
        return

    cfg = get_credentials()

    token = get_token(
        cfg["client_id"],
        cfg["cert_path"],
        cfg["key_path"]
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    body = {
        "query": build_query(),
        "variables": {
            "cpr": [cpr]
        }
    }

    response = requests.post(
        BASE_URL,
        headers=headers,
        json=body
    )

    print("HTTP STATUS:", response.status_code)

    data = response.json()

    pprint(data, width=180)


if __name__ == "__main__":
    main()