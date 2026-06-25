### OBS OBS OBS###
#FILER ER LAVET TIL ATS HVOR INDHOLDET ER LAGT IND IND OG KØRER I DOCKER.
#DENNE KODE ER DERFOR KUN TIL AT FÅ DATA OP PÅ GITHUB

import requests  # bibliotek (HTTP-kald)
import time  # modul (tid)

_cached_token = None  # variabel (cache)
_expires_at = 0  # variabel (udløbstid)


def get_token(client_id, cert_path, key_path):
    """Henter og cacher Datafordeler token (funktion: genbrugelig kodeblok)"""

    global _cached_token, _expires_at

    now = int(time.time())

    if _cached_token and now < _expires_at - 60:
        return _cached_token

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id
    }

    cert = (
        cert_path,  # .pem
        key_path    # .key
    )

    print("🔍 DEBUG: Sender request til token endpoint...")

    r = requests.post(
        "https://auth-oces.datafordeler.dk/realms/distribution/protocol/openid-connect/token",
        data=data,
        cert=cert,
        verify=True
    )

    print("🔍 DEBUG: Status code:", r.status_code)

    r.raise_for_status()

    token_data = r.json()

    _cached_token = token_data["access_token"]
    _expires_at = now + token_data.get("expires_in", 3600)

    print("✅ DEBUG: Token hentet")

    return _cached_token