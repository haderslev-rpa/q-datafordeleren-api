import requests  # bibliotek (HTTP-kald)
import time  # modul (tid)
from automation_server_client import AutomationServer, Credential  # klasser (API-adgang)

# initialiser automation server (påkrævet)
AutomationServer.from_environment()

# hent credential (hemmelig konfig)
_df_cred = Credential.get_credential("API_DATAFORDELEREN")

_cfg = _df_cred.data  # dict (nøgler/værdier)

_cached_token = None  # variabel (cache)
_expires_at = 0  # variabel (udløbstid)


def get_token():
    """Henter og cacher Datafordeler token (funktion: genbrugelig kodeblok)"""
    global _cached_token, _expires_at

    now = int(time.time())

    #print("🔍 DEBUG: Starter get_token()")
    #print("🔍 DEBUG: Cert:", _cfg["cert_path"])
    #print("🔍 DEBUG: Key:", _cfg["key_path"])
    #print("🔍 DEBUG CLIENT ID:", _cfg["client_id"])

    # brug cache hvis muligt
    if _cached_token and now < _expires_at - 60:
       # print("✅ DEBUG: Bruger cached token")
        return _cached_token

    data = {
        "grant_type": "client_credentials",
        "client_id": _cfg["client_id"]
    }

    cert = (
        _cfg["cert_path"],  # .pem
        _cfg["key_path"]    # .key
    )

    print("🔍 DEBUG: Sender request til token endpoint...")

    try:
        r = requests.post(
            "https://auth-oces.datafordeler.dk/realms/distribution/protocol/openid-connect/token",
            data=data,
            cert=cert,
            verify=True
        )

        print("🔍 DEBUG: Status code:", r.status_code)
       # print("🔍 DEBUG: Response:", r.text)

        r.raise_for_status()

    except Exception as e:
        print("❌ DEBUG FEJL:", str(e))
        raise

    token_data = r.json()

    _cached_token = token_data["access_token"]
    _expires_at = now + token_data.get("expires_in", 3600)

    print("✅ DEBUG: Token hentet")

    return _cached_token
