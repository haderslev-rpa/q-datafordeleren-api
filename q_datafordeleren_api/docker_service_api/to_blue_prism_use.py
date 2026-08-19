from q_datafordeleren_api.core.datafordeler_client import DatafordelerClient


def get_aktuel_navn_og_adresse(cpr, client_id, cert_path, key_path):

    client = DatafordelerClient()

    return client.get_aktuel_navn_og_adresse(
        cpr,
        client_id,
        cert_path,
        key_path
    )

from q_datafordeleren_api.core.datafordeler_client import DatafordelerClient
from q_datafordeleren_api.core.cvr_client import (
    CvrClient
)


def get_aktuel_navn_og_adresse(
    cpr,
    client_id,
    cert_path,
    key_path
):
    """
    Henter aktuel adresse.
    """

    client = DatafordelerClient()

    return client.get_aktuel_navn_og_adresse(
        cpr,
        client_id,
        cert_path,
        key_path
    )


def lookup_cpr_full(
    cpr,
    client_id,
    cert_path,
    key_path
):
    """
    Henter alle CPR-oplysninger.
    """

    client = DatafordelerClient()

    return client.lookup_cpr_full(
        cpr,
        client_id,
        cert_path,
        key_path
    )

def lookup_cvr_basic(
    cvr,
    client_id,
    cert_path,
    key_path
):
    """
    Henter grundlæggende virksomhedsoplysninger.
    """

    client = CvrClient()

    return client.lookup_cvr_basic(
        cvr,
        client_id,
        cert_path,
        key_path
    )

def lookup_cpr_in_cvr(
    cpr,
    client_id,
    cert_path,
    key_path
):
    """
    Undersøger om personen findes i CVR.

    Returnerer:
    - cvrperson_id
    - status
    - virkning_fra
    - virkning_til
    - registrering_fra
    - registrering_til

    Returnerer ikke:
    - virksomhed
    - CVR-nummer
    """

    client = CvrClient()

    return client.lookup_cpr_in_cvr(
        cpr,
        client_id,
        cert_path,
        key_path
    )