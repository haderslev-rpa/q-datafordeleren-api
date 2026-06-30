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
# Mulige felter på CPRCustom_PublicSectorPerson
# -------------------------------------------------
# OBS:
# Datafordeler tillader IKKE aliases.
# Derfor må vi IKKE skrive:
# testField: navne
#
# Vi skriver kun feltets rigtige navn direkte.
# -------------------------------------------------

CANDIDATE_FIELDS = [
    # Kendte felter
    "navne",
    "adresseoplysninger",
    "civilstande",

    # Forældre / børn / relationer
    "foraelderoplysninger",
    "foraelderoplysning",
    "foraeldre",
    "foraelder",

    # Forældremyndighed
    "foraeldremyndighedsoplysninger",
    "foraeldremyndighedsoplysning",
    "foraeldremyndighed",
    "foraeldremyndigheder",
    "foraeldremyndighedshavere",

    # Børn
    "boern",
    "boerneoplysninger",
    "barn",
    "born",

    # Delt bopæl
    "deltbopael",
    "deltbopaele",
    "deltebopaele",

    # Udrejse / indrejse
    "udrejseIndrejser",
    "udrejseIndrejse",
    "udrejseindrejser",

    # Forsvinding
    "forsvindinger",
    "forsvinding",

    # Statsborgerskab
    "statsborgerskaber",
    "statsborgerskab",

    # Personnummer
    "personnumre",
    "personnummer",

    # Kontaktadresse
    "kontaktadresser",
    "kontaktadresse",

    # Værgemål
    "vaergemaal",
    "vaergemaaler",

    # Kommunale forhold
    "kommunaleForhold",

    # Folkekirke
    "folkekirke",

    # Notater
    "notater",
    "notat",
]


def get_credentials():
    """Henter credentials (hemmelige oplysninger)"""

    AutomationServer.from_environment()

    cred = Credential.get_credential("API_DATAFORDELEREN")
    return cred.data


def build_query_for_field(field_name):
    """Bygger GraphQL-query (API-forespørgsel) uden aliases"""

    query = f"""
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

          {field_name} {{
            __typename
          }}
        }}
      }}
    }}
    """

    return query


def run_single_field_test(field_name, cpr, headers):
    """Tester ét felt (funktion (genbrugelig kodeblok))"""

    query = build_query_for_field(field_name)

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
        "field_name": field_name,
        "status_code": response.status_code,
        "response": response_json,
        "query": query
    }


def print_field_result(result):
    """Printer resultat (funktion (genbrugelig kodeblok))"""

    field_name = result["field_name"]
    status_code = result["status_code"]
    response = result["response"]

    print("\n" + "=" * 100)
    print(f"Tester felt: {field_name}")
    print("=" * 100)
    print("HTTP status:", status_code)

    errors = response.get("errors")

    if status_code == 200 and not errors:
        print("✅ FELT FINDES")
        pprint(response, width=140)
        return True

    print("❌ FELT FEJLER")

    if errors:
        for error in errors:
            print("- Fejlbesked:", error.get("message"))

            extensions = error.get("extensions")
            if extensions:
                print("  Extensions:", extensions)
    else:
        pprint(response, width=140)

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

    print("\n🚀 Tester GraphQL-felter på CPRCustom_PublicSectorPerson")
    print("🔍 CPR:", cpr)
    print("🔍 Antal felter:", len(CANDIDATE_FIELDS))

    fields_that_exist = []
    fields_that_fail = []

    for field_name in CANDIDATE_FIELDS:
        result = run_single_field_test(
            field_name=field_name,
            cpr=cpr,
            headers=headers
        )

        ok = print_field_result(result)

        if ok:
            fields_that_exist.append(field_name)
        else:
            fields_that_fail.append(field_name)

    print("\n" + "#" * 100)
    print("✅ FELTER DER FINDES")
    print("#" * 100)

    for field_name in fields_that_exist:
        print("✅", field_name)

    print("\n" + "#" * 100)
    print("❌ FELTER DER FEJLER")
    print("#" * 100)

    for field_name in fields_that_fail:
        print("❌", field_name)


if __name__ == "__main__":
    main()