# -------------------------------------------------
# NOTE OM CPRPublicSector GraphQL
# -------------------------------------------------
# Fundet ved test mod Datafordeler:
#
# 1. Datafordeler kræver, at beskyttelser altid er med i query
#    (forespørgsel), ellers kommer fejl:
#    "Required fields are missing in query selection: beskyttelser"
#
# 2. Datafordeler tillader ikke aliases (alternative feltnavne).
#    Man må derfor ikke skrive:
#        testField: boern
#
# 3. Følgende topfelter på CPRCustom_PublicSectorPerson er bekræftet:
#    - navne
#    - adresseoplysninger
#    - civilstande
#    - foraeldremyndighedsoplysninger
#    - boern
#    - udrejseIndrejser
#    - forsvindinger
#    - statsborgerskaber
#    - personnumre
#    - kontaktadresse
#    - vaergemaal
#    - kommunaleForhold
#    - folkekirke
#    - notater
#
# 4. Følgende topfelter findes ikke med disse navne:
#    - foraelderoplysninger
#    - foraelderoplysning
#    - foraeldre
#    - foraelder
#    - barn
#    - born
#    - deltbopael
#
# 5. Direkte forældreopslag ser derfor ikke ud til at ligge som
#    foraelderoplysninger på Person i GraphQL.
#    Børn findes derimod via feltet boern.
#
# 6. Næste skridt er at finde underfelter på boern, så vi kan hente
#    barnets CPR-nummer.
# -------------------------------------------------



from pprint import pprint  # funktion (pæn udskrift)
import os  # modul (miljøvariabler)

import requests  # bibliotek (HTTP-kald)
from dotenv import load_dotenv  # funktion (læser .env)

from automation_server_client import AutomationServer, Credential  # klasser (API-adgang)
from q_datafordeleren_api.core.datafordeler_auth import get_token  # funktion (henter token)


BASE_URL = "https://graphql.datafordeler.dk/CPR/custom/PublicSector/v1"


# -------------------------------------------------
# NOTE OM DENNE TESTFIL
# -------------------------------------------------
# Denne testfil (kodefil) tester underfelter (felter inde i felter)
# på de GraphQL-felter (API-felter), vi allerede har bekræftet virker:
#
# - boern
# - foraeldremyndighedsoplysninger
#
# Datafordeler kræver beskyttelser i alle queries (forespørgsler).
# Datafordeler tillader ikke aliases (alternative feltnavne).
# Derfor bruges ingen aliases i denne fil.
# -------------------------------------------------


TESTS = [
    # -------------------------------------------------
    # BØRN - basis
    # -------------------------------------------------
    {
        "name": "1 - boern kun typename",
        "block": """
          boern {
            __typename
          }
        """
    },

    {
        "name": "2 - boern med status/virkning",
        "block": """
          boern {
            status
            virkningfra
            virkningtil
          }
        """
    },

    {
        "name": "3 - boern med personnummer direkte",
        "block": """
          boern {
            personnummer
          }
        """
    },

    {
        "name": "4 - boern med barn direkte",
        "block": """
          boern {
            barn
          }
        """
    },

    {
        "name": "5 - boern med barn personnumre",
        "block": """
          boern {
            barn {
              personnumre {
                personnummer
                status
                virkningfra
                virkningtil
              }
            }
          }
        """
    },

    {
        "name": "6 - boern med barn id/status",
        "block": """
          boern {
            barn {
              id
              status
              koen
            }
          }
        """
    },

    {
        "name": "7 - boern med barn navne",
        "block": """
          boern {
            barn {
              navne {
                fornavne
                mellemnavn
                efternavn
                status
              }
            }
          }
        """
    },

    {
        "name": "8 - boern med barn personnummer objekt",
        "block": """
          boern {
            barn {
              personnummer {
                personnummer
              }
            }
          }
        """
    },

    {
        "name": "9 - boern med relationstype/rolle",
        "block": """
          boern {
            relationstype
            rolle
            status
          }
        """
    },

    {
        "name": "10 - boern med alle sandsynlige simple felter",
        "block": """
          boern {
            status
            virkningfra
            virkningtil
            registreringfra
          }
        """
    },

    # -------------------------------------------------
    # FORÆLDREMYNDIGHED - basis
    # -------------------------------------------------
    {
        "name": "11 - foraeldremyndighedsoplysninger kun typename",
        "block": """
          foraeldremyndighedsoplysninger {
            __typename
          }
        """
    },

    {
        "name": "12 - foraeldremyndighedsoplysninger med rolle",
        "block": """
          foraeldremyndighedsoplysninger {
            foraeldremyndighedsindehaverrolle
          }
        """
    },

    {
        "name": "13 - foraeldremyndighedsoplysninger med virkning",
        "block": """
          foraeldremyndighedsoplysninger {
            virkningfra
            virkningtil
          }
        """
    },

    {
        "name": "14 - foraeldremyndighedsoplysninger med haver direkte",
        "block": """
          foraeldremyndighedsoplysninger {
            foraeldremyndighedshaver {
              id
              status
              koen
            }
          }
        """
    },

    {
        "name": "15 - foraeldremyndighedsoplysninger med haver personnumre",
        "block": """
          foraeldremyndighedsoplysninger {
            foraeldremyndighedshaver {
              personnumre {
                personnummer
                status
                virkningfra
                virkningtil
              }
            }
          }
        """
    },

    {
        "name": "16 - foraeldremyndighedsoplysninger over barn",
        "block": """
          foraeldremyndighedsoplysninger {
            foraeldremyndighedOver {
              id
              status
              koen
            }
          }
        """
    },

    {
        "name": "17 - foraeldremyndighedsoplysninger over barn personnumre",
        "block": """
          foraeldremyndighedsoplysninger {
            foraeldremyndighedOver {
              personnumre {
                personnummer
                status
                virkningfra
                virkningtil
              }
            }
          }
        """
    },
]


def get_credentials():
    """Henter credentials (hemmelige oplysninger)"""

    AutomationServer.from_environment()

    cred = Credential.get_credential("API_DATAFORDELEREN")
    return cred.data


def build_query(block):
    """Bygger GraphQL query (API-forespørgsel)"""

    return f"""
    query ($cpr: [String!]!) {{
      CPRCustom_PublicSectorPerson(
        input: {{
          personnummer: {{
            personnummer: {{
              in: $cpr
            }}
          }}
        }}
      ) {{
        nodes {{
          id
          status
          koen

          beskyttelser {{
            beskyttelsestype
            status
            virkningfra
            virkningtil
          }}

          {block}
        }}
      }}
    }}
    """


def run_test(test, cpr, headers):
    """Kører én test (funktion (genbrugelig kodeblok))"""

    query = build_query(test["block"])

    body = {
        "query": query,
        "variables": {
            "cpr": [cpr]
        }
    }

    response = requests.post(
        BASE_URL,
        headers=headers,
        json=body
    )

    try:
        response_json = response.json()
    except Exception:
        response_json = {
            "raw_text": response.text
        }

    return {
        "name": test["name"],
        "status_code": response.status_code,
        "response": response_json,
        "query": query
    }


def print_result(result):
    """Printer resultat (funktion (genbrugelig kodeblok))"""

    print("\n" + "=" * 100)
    print(result["name"])
    print("=" * 100)

    print("HTTP status:", result["status_code"])

    response = result["response"]
    errors = response.get("errors")

    if result["status_code"] == 200 and not errors:
        print("✅ VIRKER")
        pprint(response, width=160)
        return True

    print("❌ FEJLER")

    if errors:
        for error in errors:
            print("- Fejlbesked:", error.get("message"))

            extensions = error.get("extensions")
            if extensions:
                print("  Extensions:", extensions)
    else:
        pprint(response, width=160)

    return False


def main():
    """Starter testen (funktion (genbrugelig kodeblok))"""

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

    print("\n🚀 Tester børn og forældremyndighed")
    print("🔍 CPR:", cpr)
    print("🔍 Antal tests:", len(TESTS))

    virker = []
    fejler = []

    for test in TESTS:
        result = run_test(test, cpr, headers)
        ok = print_result(result)

        if ok:
            virker.append(test["name"])
        else:
            fejler.append(test["name"])

    print("\n" + "#" * 100)
    print("✅ TESTS DER VIRKER")
    print("#" * 100)

    for item in virker:
        print("✅", item)

    print("\n" + "#" * 100)
    print("❌ TESTS DER FEJLER")
    print("#" * 100)

    for item in fejler:
        print("❌", item)


if __name__ == "__main__":
    main()