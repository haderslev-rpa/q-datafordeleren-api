import json
import os

from dotenv import load_dotenv

from q_datafordeleren_api.functionality.datafordeler_use import (
    lookup_cpr_in_cvr,
    lookup_cvr_basic
)


# -------------------------------------------------
# Hjælpefunktioner
# -------------------------------------------------

def format_json(value):
    """
    Formaterer Python-data som læsbar JSON.

    default=str sikrer, at eksempelvis datoobjekter
    også kan udskrives.
    """

    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        default=str,
        sort_keys=False
    )


def print_json_section(title, value):
    """
    Udskriver en overskrift og et JSON-resultat.
    """

    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)

    print(
        format_json(value)
    )


def normaliser_cvr(cvr_number):
    """
    Fjerner mellemrum og bindestreg fra CVR.
    """

    if cvr_number is None:
        return ""

    return (
        str(cvr_number)
        .replace(" ", "")
        .replace("-", "")
        .strip()
    )


def normaliser_cpr(cpr_number):
    """
    Fjerner mellemrum og bindestreg fra CPR.
    """

    if cpr_number is None:
        return ""

    return (
        str(cpr_number)
        .replace(" ", "")
        .replace("-", "")
        .strip()
    )


def cvr_format_ok(cvr_number):
    """
    Kontrollerer CVR-formatet.
    """

    return (
        bool(cvr_number)
        and cvr_number.isdigit()
        and len(cvr_number) == 8
    )


def cpr_format_ok(cpr_number):
    """
    Kontrollerer CPR-formatet.
    """

    return (
        bool(cpr_number)
        and cpr_number.isdigit()
        and len(cpr_number) == 10
    )


def print_company_summary(result):
    """
    Udskriver den korte CVR-opsummering.
    """

    print("\n" + "-" * 100)
    print("KORT CVR-OPSUMMERING")
    print("-" * 100)

    print(
        "CVR-format gyldigt:",
        result.get("cvr_format_ok", False)
    )

    print(
        "Virksomhed fundet:",
        result.get("findes", False)
    )

    if not result.get("findes"):
        return

    print(
        "CVR-nummer:",
        result.get("cvr_nummer", "")
    )

    print(
        "Internt CVR-enheds-id:",
        result.get("cvr_enheds_id", "")
    )

    print(
        "Virksomhedsnavn:",
        result.get("virksomhedsnavn", "")
    )

    print(
        "Status:",
        result.get("status", "")
    )

    print(
        "Er aktiv:",
        result.get("er_aktiv", False)
    )

    print(
        "Startdato:",
        result.get(
            "virksomhed_startdato",
            ""
        )
    )

    print(
        "Ophørsdato:",
        result.get(
            "virksomhed_ophoersdato",
            ""
        )
    )

    print(
        "Virksomhedsform:",
        result.get(
            "virksomhedsform",
            {}
        )
    )

    print(
        "Hovedbranche:",
        result.get(
            "hovedbranche",
            {}
        )
    )

    print(
        "Bibrancher:",
        result.get(
            "bibrancher",
            []
        )
    )

    address = result.get(
        "aktuel_adresse",
        {}
    )

    print(
        "Adresse:",
        address.get("adresse", "")
    )

    print(
        "Postnummer:",
        address.get("postnummer", "")
    )

    print(
        "Postdistrikt:",
        address.get("postdistrikt", "")
    )

    print(
        "Telefonnumre:",
        result.get(
            "telefonnumre",
            []
        )
    )

    print(
        "E-mailadresser:",
        result.get(
            "emailadresser",
            []
        )
    )

    print(
        "Reklamebeskyttet:",
        result.get(
            "reklamebeskyttet",
            False
        )
    )

    print(
        "Legale ejere:",
        result.get(
            "legale_ejere",
            []
        )
    )


def print_cvr_person_summary(result):
    """
    Udskriver den korte CPR-i-CVR-opsummering.

    Selve CPR-nummeret udskrives ikke.
    """

    print("\n" + "-" * 100)
    print("KORT CPR-I-CVR-OPSUMMERING")
    print("-" * 100)

    print(
        "CPR-format gyldigt:",
        result.get(
            "cpr_format_ok",
            False
        )
    )

    print(
        "Person findes i CVR:",
        result.get(
            "findes_i_cvr",
            False
        )
    )

    print(
        "Antal CVRPerson-poster:",
        result.get(
            "antal_cvrperson_poster",
            0
        )
    )

    print(
        "Aktuel CVRPerson:",
        result.get(
            "aktuel_cvrperson"
        )
    )

    print(
        "Antal virksomheder:",
        result.get(
            "antal_virksomheder",
            0
        )
    )

    print(
        "Virksomheder:",
        result.get(
            "virksomheder",
            []
        )
    )


# -------------------------------------------------
# Test CVR-nummer
# -------------------------------------------------

def run_cvr_test(cvr_number):
    """
    Tester CVR-nummer til virksomhedsoplysninger.

    Funktionen kalder det samme offentlige lag,
    som en rigtig proces skal bruge.
    """

    print("\n" + "#" * 100)
    print("TEST 1: CVR-NUMMER TIL VIRKSOMHED")
    print("#" * 100)

    if not cvr_number:
        print(
            "⏭️ Testen springes over, "
            "fordi cvr1 mangler i .env"
        )

        return None

    if not cvr_format_ok(
        cvr_number
    ):
        print(
            "❌ cvr1 skal bestå af "
            "præcis otte cifre"
        )

        return None

    try:
        result = lookup_cvr_basic(
            cvr_number
        )

    except Exception as error:
        print(
            "❌ CVR-opslaget fejlede"
        )

        print(
            "Fejltype:",
            type(error).__name__
        )

        print(
            "Fejlbesked:",
            str(error)
        )

        return None

    print(
        "✅ CVR-opslaget blev gennemført"
    )

    print_company_summary(
        result
    )

    print_json_section(
        title=(
            "HELE JSON-RESULTATET FRA "
            "lookup_cvr_basic()"
        ),
        value=result
    )

    return result


# -------------------------------------------------
# Test CPR-nummer i CVR
# -------------------------------------------------

def run_cpr_in_cvr_test(cpr_number):
    """
    Tester CPR-nummer til CVRPerson.

    Funktionen kalder det samme offentlige lag,
    som en rigtig proces skal bruge.
    """

    print("\n" + "#" * 100)
    print("TEST 2: CPR-NUMMER TIL CVRPERSON")
    print("#" * 100)

    if not cpr_number:
        print(
            "⏭️ Testen springes over, "
            "fordi cprcvr1 mangler i .env"
        )

        return None

    if not cpr_format_ok(
        cpr_number
    ):
        print(
            "❌ cprcvr1 skal bestå af "
            "præcis ti cifre"
        )

        return None

    try:
        result = lookup_cpr_in_cvr(
            cpr_number
        )

    except Exception as error:
        print(
            "❌ CPR-i-CVR-opslaget fejlede"
        )

        print(
            "Fejltype:",
            type(error).__name__
        )

        print(
            "Fejlbesked:",
            str(error)
        )

        print(
            "\nHvis fejlen handler om adgang, "
            "skal IT-systemet være godkendt "
            "til CVRPerson."
        )

        return None

    print(
        "✅ CPR-i-CVR-opslaget blev gennemført"
    )

    print_cvr_person_summary(
        result
    )

    print_json_section(
        title=(
            "HELE JSON-RESULTATET FRA "
            "lookup_cpr_in_cvr()"
        ),
        value=result
    )

    return result


# -------------------------------------------------
# Start testen
# -------------------------------------------------

def main():
    """
    Kører begge offentlige CVR-tests.
    """

    load_dotenv()

    cvr_number = normaliser_cvr(
        os.getenv("cvr1")
    )

    cpr_number = normaliser_cpr(
        os.getenv("cprcvr1")
    )

    print(
        "\n🚀 TEST: OFFENTLIGE "
        "DATAFORDELER-CVR-FUNKTIONER\n"
    )

    print(
        "Denne test bruger kun funktioner fra "
        "datafordeler_use.py."
    )

    print(
        "CPR-nummeret bliver ikke udskrevet."
    )

    company_result = run_cvr_test(
        cvr_number
    )

    cvr_person_result = (
        run_cpr_in_cvr_test(
            cpr_number
        )
    )

    # ---------------------------------------------
    # Samlet resultat uden at gemme en fil
    # ---------------------------------------------

    combined_result = {
        "cvr_opslag": company_result,
        "cpr_i_cvr_opslag": (
            cvr_person_result
        )
    }

    print_json_section(
        title="SAMLET JSON-RESULTAT",
        value=combined_result
    )

    print("\n✅ Alle CVR-tests er afsluttet")


if __name__ == "__main__":
    main()