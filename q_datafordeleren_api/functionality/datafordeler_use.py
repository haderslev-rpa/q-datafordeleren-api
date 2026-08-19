from automation_server_client import (
    AutomationServer,
    Credential
)

from q_datafordeleren_api.core.cvr_client import (
    CvrClient
)

from q_datafordeleren_api.core.datafordeler_client import (
    DatafordelerClient
)


# -------------------------------------------------
# Fælles adgangsoplysninger
# -------------------------------------------------

def _get_cfg():
    """
    Henter Datafordeler-adgangsoplysninger.
    """

    AutomationServer.from_environment()

    credential = Credential.get_credential(
        "API_DATAFORDELEREN"
    )

    return credential.data


def _get_required_value(
    config,
    key
):
    """
    Henter en påkrævet credential-værdi.
    """

    value = config.get(key)

    if not value:
        raise RuntimeError(
            "Credential API_DATAFORDELEREN "
            f"mangler værdien: {key}"
        )

    return value


def _get_datafordeler_credentials():
    """
    Returnerer de nødvendige adgangsoplysninger.
    """

    config = _get_cfg()

    return {
        "client_id": _get_required_value(
            config,
            "client_id"
        ),
        "cert_path": _get_required_value(
            config,
            "cert_path"
        ),
        "key_path": _get_required_value(
            config,
            "key_path"
        )
    }


# -------------------------------------------------
# CPR-register
# -------------------------------------------------

def get_aktuel_navn_og_adresse(cpr):
    """
    Henter aktuelt navn og adresse fra CPR.

    Resultatet er JSON-kompatibelt.
    """

    credentials = (
        _get_datafordeler_credentials()
    )

    client = DatafordelerClient()

    return client.get_aktuel_navn_og_adresse(
        cpr_number=cpr,
        client_id=credentials["client_id"],
        cert_path=credentials["cert_path"],
        key_path=credentials["key_path"]
    )


def lookup_cpr_full(cpr):
    """
    Henter det eksisterende fulde CPR-resultat.

    Resultatet er JSON-kompatibelt.
    """

    credentials = (
        _get_datafordeler_credentials()
    )

    client = DatafordelerClient()

    return client.lookup_cpr_full(
        cpr_number=cpr,
        client_id=credentials["client_id"],
        cert_path=credentials["cert_path"],
        key_path=credentials["key_path"]
    )


# -------------------------------------------------
# CVR-register: virksomhed
# -------------------------------------------------

def lookup_cvr_basic(cvr):
    """
    Henter grundlæggende virksomhedsoplysninger.

    Eksempel:
        result = lookup_cvr_basic(
            "29189757"
        )

    Resultatet er JSON-kompatibelt.
    Der gemmes ingen filer.
    """

    credentials = (
        _get_datafordeler_credentials()
    )

    client = CvrClient()

    return client.lookup_cvr_basic(
        cvr_number=cvr,
        client_id=credentials["client_id"],
        cert_path=credentials["cert_path"],
        key_path=credentials["key_path"]
    )
    """
    Bagudkompatibelt navn til CVR-opslag.

    Funktionen returnerer samme resultat som
    lookup_cvr_basic.
    """

    return lookup_cvr_basic(
        cvr=cvr
    )


# -------------------------------------------------
# CVR-register: CPR til CVRPerson
# -------------------------------------------------

def lookup_cpr_in_cvr(cpr):
    """
    Undersøger, om personen findes i CVR.

    Funktionen returnerer CVRPerson-id,
    status og datooplysninger.

    Funktionen returnerer ikke virksomhed
    eller CVR-nummer.

    Eksempel:
        result = lookup_cpr_in_cvr(
            cpr_number
        )

    Resultatet er JSON-kompatibelt.
    Der gemmes ingen filer.
    """

    credentials = (
        _get_datafordeler_credentials()
    )

    client = CvrClient()

    return client.lookup_cpr_in_cvr(
        cpr_number=cpr,
        client_id=credentials["client_id"],
        cert_path=credentials["cert_path"],
        key_path=credentials["key_path"]
    )


    """
    Tydeligt alternativt navn til CVRPerson-opslaget.

    Funktionen er identisk med
    lookup_cpr_in_cvr.
    """

    return lookup_cpr_in_cvr(
        cpr=cpr
    )