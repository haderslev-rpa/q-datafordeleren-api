import requests  # bibliotek (HTTP-kald)
import time  # modul (tid)
from automation_server_client import Credential  # klasse (credential-adgang)


_df_cred = Credential.get_credential("DATAFORDELER_API")
_cfg = _df_cred.data

_cached_token = None  # variabel (cache)
_expires_at = 0  # variabel (udløbstid)


def get_token():
    """Hent og cache Datafordeler token (funktion: genbrugelig kodeblok)"""
    global _cached_token, _expires_at

    now = int(time.time())
    if _cached_token and now < _expires_at - 60:
        return _cached_token

    data = {
        "grant_type": "client_credentials",
        "client_id": _cfg["client_id"]
    }

    r = requests.post(
        _cfg["token_url"],
        data=data,
        cert=(_cfg["cert_path"], _cfg["cert_password"]),  # certifikat + password
        verify=True
    )
    r.raise_for_status()

    token_data = r.json()

    _cached_token = token_data["access_token"]
    _expires_at = now + token_data.get("expires_in", 3600)

    return _cached_token