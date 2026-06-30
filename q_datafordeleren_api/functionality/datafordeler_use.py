from automation_server_client import AutomationServer, Credential
from q_datafordeleren_api.core.datafordeler_client import DatafordelerClient

def _get_cfg():
    AutomationServer.from_environment()
    cred = Credential.get_credential("API_DATAFORDELEREN")
    return cred.data


def get_aktuel_navn_og_adresse(cpr):

    cfg = _get_cfg()

    client = DatafordelerClient()

    return client.get_aktuel_navn_og_adresse(
        cpr,
        cfg["client_id"],
        cfg["cert_path"],
        cfg["key_path"]
    )


def lookup_cpr_full(cpr):

    cfg = _get_cfg()

    client = DatafordelerClient()

    return client.lookup_cpr_full(
        cpr,
        cfg["client_id"],
        cfg["cert_path"],
        cfg["key_path"]
    )
