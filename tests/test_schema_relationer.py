# -------------------------------------------------
# TEST: FULL CPR MED BØRN, FORÆLDRE OG CPR-SKIFT
# -------------------------------------------------
#
# Schemaet har bekræftet:
#
# Hovedperson:
# - personnumre
# - adresseoplysninger
# - navne
# - beskyttelser
# - civilstande
#
# Relationer:
# - boern
# - foraeldreoplysninger
# - foraeldremyndighedsoplysninger
# - foraeldremyndighedOver
#
# Vigtige regler:
#
# 1. Datafordeleren kræver beskyttelser på hovedpersonen.
#
# 2. CPRCustom_PublicSectorSimpelPerson kræver også
#    beskyttelser, når objektet bruges under børn,
#    forældre eller forældremyndighed.
#
# 3. Det korrekte GraphQL-felt er:
#       foraeldreoplysninger
#
#    Ikke:
#       foraelderoplysninger
#
# 4. Relationer kan være:
#    - almindelig person med CPR
#    - person uden CPR
#    - ikke-valid relation
#
# Derfor testes alle tre muligheder.
# -------------------------------------------------

from pprint import pprint
import os

import requests
from dotenv import load_dotenv

from automation_server_client import AutomationServer, Credential

from q_datafordeleren_api.core.datafordeler_auth import get_token


BASE_URL = (
    "https://graphql.datafordeler.dk/"
    "CPR/custom/PublicSector/v1"
)


# -------------------------------------------------
# Hent credentials
# -------------------------------------------------
def get_credentials():
    """Henter adgangsoplysninger fra Automation Server."""

    AutomationServer.from_environment()

    credential = Credential.get_credential(
        "API_DATAFORDELEREN"
    )

    return credential.data


# -------------------------------------------------
# Normalisering af CPR
# -------------------------------------------------
def normaliser_cpr(cpr_number):
    """Fjerner bindestreg og mellemrum fra CPR."""

    if cpr_number is None:
        return ""

    return (
        str(cpr_number)
        .replace("-", "")
        .replace(" ", "")
        .strip()
    )


# -------------------------------------------------
# GraphQL-query
# -------------------------------------------------
def build_query():
    """Bygger GraphQL-query (API-forespørgsel)."""

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
          statusdato
          foedselsdato
          koen

          personnumre {
            personnummer
            status
            virkningfra
            virkningfrausikkerhedsmarkering
            virkningtil
            virkningtilusikkerhedsmarkering
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

          adresseoplysninger {
            conavn
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

            supplerendeAdresse {
              virkningfra
              virkningtil
              adresselinie1
              adresselinie2
              adresselinie3
              adresselinie4
              adresselinie5
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
            virkningfrausikkerhedsmarkering

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
                virkningfra
                virkningtil
              }
            }
          }

          foraeldreoplysninger {
            virkningfra
            virkningfrausikkerhedsmarkering
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
                virkningfra
                virkningtil
              }
            }

            foraelderUdenCpr {
              personid
              navn
              navnemarkering
              foedselsdato
              foedselsdatousikkerhedsmarkering
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


# -------------------------------------------------
# Udled CPR-skift
# -------------------------------------------------
def build_personnummer_summary(
    opslaaet_cpr,
    personnumre
):
    """
    Udleder aktuelt og historiske CPR-numre.

    Returnerer samme struktur hver gang.
    """

    aktuelle = [
        item
        for item in personnumre
        if item.get("status") == "aktuel"
    ]

    historiske = [
        item
        for item in personnumre
        if item.get("status") != "aktuel"
    ]

    aktuelt_cpr = ""

    if aktuelle:
        aktuelt_cpr = (
            aktuelle[0].get("personnummer")
            or ""
        )

    historiske_cpr_numre = [
        item.get("personnummer")
        for item in historiske
        if item.get("personnummer")
    ]

    har_skiftet_cpr = bool(
        historiske_cpr_numre
        or (
            aktuelt_cpr
            and aktuelt_cpr != opslaaet_cpr
        )
    )

    return {
        "opslaaet_cpr": opslaaet_cpr,
        "aktuelt_cpr": aktuelt_cpr,
        "har_skiftet_cpr": har_skiftet_cpr,
        "tidligere_cpr_numre": historiske_cpr_numre,
        "alle_personnumre": personnumre
    }


# -------------------------------------------------
# Udled børn
# -------------------------------------------------
def build_boern_summary(boern):
    """
    Laver en fast struktur med børn.

    Barnets CPR findes under:
    boern -> barn -> personnummer
    """

    resultater = []

    for barn_oplysning in boern or []:
        barn = barn_oplysning.get("barn")

        # Relation kan være tom
        if not barn:
            resultater.append(
                {
                    "personid": "",
                    "personnummer": "",
                    "navn": "",
                    "virkningfra": (
                        barn_oplysning.get(
                            "virkningfra"
                        )
                        or ""
                    ),
                    "har_cpr": False
                }
            )
            continue

        navn_data = barn.get("navn") or {}

        navn = (
            navn_data.get("adresseringsnavn")
            or " ".join(
                [
                    value
                    for value in [
                        navn_data.get("fornavne"),
                        navn_data.get("mellemnavn"),
                        navn_data.get("efternavn")
                    ]
                    if value
                ]
            )
        )

        personnummer = (
            barn.get("personnummer")
            or ""
        )

        resultater.append(
            {
                "personid": (
                    barn.get("personid")
                    or ""
                ),
                "personnummer": personnummer,
                "navn": navn,
                "virkningfra": (
                    barn_oplysning.get(
                        "virkningfra"
                    )
                    or ""
                ),
                "har_cpr": bool(personnummer)
            }
        )

    return {
        "antal_boern": len(resultater),
        "boern": resultater
    }


# -------------------------------------------------
# Udled forældre
# -------------------------------------------------
def build_foraeldre_summary(
    foraeldreoplysninger
):
    """
    Laver en fast struktur med forældre.

    En relation kan pege på:
    - forælder med CPR
    - forælder uden CPR
    - ikke-valid relationsperson
    """

    resultater = []

    for oplysning in foraeldreoplysninger or []:
        foraelder = oplysning.get("foraelder")
        foraelder_uden_cpr = (
            oplysning.get(
                "foraelderUdenCpr"
            )
        )
        ikke_valid = (
            oplysning.get(
                "ikkeValidRelationsForaelder"
            )
        )

        result = {
            "foraelderrolle": (
                oplysning.get(
                    "foraelderrolle"
                )
                or ""
            ),
            "virkningfra": (
                oplysning.get(
                    "virkningfra"
                )
                or ""
            ),
            "relationstype": "",
            "personid": "",
            "personnummer": "",
            "navn": "",
            "foedselsdato": "",
            "har_cpr": False
        }

        if foraelder:
            navn_data = (
                foraelder.get("navn")
                or {}
            )

            result["relationstype"] = (
                "person_med_cpr"
            )
            result["personid"] = (
                foraelder.get("personid")
                or ""
            )
            result["personnummer"] = (
                foraelder.get("personnummer")
                or ""
            )
            result["navn"] = (
                navn_data.get(
                    "adresseringsnavn"
                )
                or " ".join(
                    [
                        value
                        for value in [
                            navn_data.get(
                                "fornavne"
                            ),
                            navn_data.get(
                                "mellemnavn"
                            ),
                            navn_data.get(
                                "efternavn"
                            )
                        ]
                        if value
                    ]
                )
            )
            result["har_cpr"] = bool(
                result["personnummer"]
            )

        elif foraelder_uden_cpr:
            result["relationstype"] = (
                "person_uden_cpr"
            )
            result["personid"] = (
                foraelder_uden_cpr.get(
                    "personid"
                )
                or ""
            )
            result["navn"] = (
                foraelder_uden_cpr.get(
                    "navn"
                )
                or ""
            )
            result["foedselsdato"] = (
                foraelder_uden_cpr.get(
                    "foedselsdato"
                )
                or ""
            )

        elif ikke_valid:
            result["relationstype"] = (
                "ikke_valid_relation"
            )
            result["personid"] = (
                ikke_valid.get("personid")
                or ""
            )
            result["personnummer"] = (
                ikke_valid.get(
                    "personnummer"
                )
                or ""
            )
            result["navn"] = (
                ikke_valid.get("navn")
                or ""
            )
            result["foedselsdato"] = (
                ikke_valid.get(
                    "foedselsdato"
                )
                or ""
            )
            result["har_cpr"] = bool(
                result["personnummer"]
            )

        resultater.append(result)

    return {
        "antal_foraeldre": len(resultater),
        "foraeldre": resultater
    }


# -------------------------------------------------
# Kør test
# -------------------------------------------------
def main():
    """Kører samlet relationstest."""

    load_dotenv()

    cpr = normaliser_cpr(
        os.getenv("cpr1")
    )

    if not cpr:
        print("❌ Mangler cpr1 i .env")
        return

    credentials = get_credentials()

    token = get_token(
        credentials["client_id"],
        credentials["cert_path"],
        credentials["key_path"]
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

    print(
        "\n🚀 TEST: CPR FULL MED RELATIONER\n"
    )
    print("🔍 Opslået CPR:", cpr)

    response = requests.post(
        BASE_URL,
        headers=headers,
        json=body,
        timeout=60
    )

    print(
        "🔍 HTTP status:",
        response.status_code
    )

    try:
        data = response.json()
    except ValueError:
        print("\n❌ Svaret er ikke gyldig JSON")
        print(response.text)
        return

    if data.get("errors"):
        print("\n❌ GraphQL fejl:\n")

        for error in data["errors"]:
            print(
                "-",
                error.get(
                    "message",
                    "Ukendt GraphQL-fejl"
                )
            )

            extensions = error.get(
                "extensions"
            )

            if extensions:
                pprint(
                    extensions,
                    width=160
                )

        return

    response.raise_for_status()

    nodes = (
        data
        .get("data", {})
        .get(
            "CPRCustom_PublicSectorPerson",
            {}
        )
        .get("nodes", [])
    )

    if not nodes:
        print("\n❌ CPR blev ikke fundet")
        return

    node = nodes[0]

    personnummer_summary = (
        build_personnummer_summary(
            opslaaet_cpr=cpr,
            personnumre=node.get(
                "personnumre",
                []
            )
        )
    )

    boern_summary = build_boern_summary(
        node.get("boern", [])
    )

    foraeldre_summary = (
        build_foraeldre_summary(
            node.get(
                "foraeldreoplysninger",
                []
            )
        )
    )

    samlet_resultat = {
        "person": {
            "id": node.get("id", ""),
            "status": node.get(
                "status",
                ""
            ),
            "statusdato": node.get(
                "statusdato",
                ""
            ),
            "foedselsdato": node.get(
                "foedselsdato",
                ""
            ),
            "koen": node.get(
                "koen",
                ""
            )
        },
        "personnumre": (
            personnummer_summary
        ),
        "boern": boern_summary,
        "foraeldre": foraeldre_summary,
        "navne": node.get(
            "navne",
            []
        ),
        "adresseoplysninger": node.get(
            "adresseoplysninger",
            []
        ),
        "beskyttelser": node.get(
            "beskyttelser",
            []
        ),
        "civilstande": node.get(
            "civilstande",
            []
        )
    }

    print("\n✅ SAMLET STANDARDRESULTAT:\n")

    pprint(
        samlet_resultat,
        width=180,
        sort_dicts=False
    )

    print("\n✅ KORT OPSUMMERING:\n")

    print(
        "Aktuelt CPR:",
        personnummer_summary[
            "aktuelt_cpr"
        ]
    )
    print(
        "Har skiftet CPR:",
        personnummer_summary[
            "har_skiftet_cpr"
        ]
    )
    print(
        "Tidligere CPR-numre:",
        personnummer_summary[
            "tidligere_cpr_numre"
        ]
    )
    print(
        "Antal børn:",
        boern_summary[
            "antal_boern"
        ]
    )
    print(
        "Antal forældre:",
        foraeldre_summary[
            "antal_foraeldre"
        ]
    )


if __name__ == "__main__":
    main()