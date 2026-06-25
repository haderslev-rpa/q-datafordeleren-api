from q_datafordeleren_api.core.datafordeler_client import DatafordelerClient


def get_aktuel_navn_og_adresse(cpr, client_id, cert_path, key_path):

    client = DatafordelerClient()

    return client.get_aktuel_navn_og_adresse(
        cpr,
        client_id,
        cert_path,
        key_path
    )