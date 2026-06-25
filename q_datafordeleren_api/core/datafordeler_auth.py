import requests
import time

_cached_token = None
_expires_at = 0


def get_token(client_id, cert_path, key_path):
    global _cached_token, _expires_at

    now = int(time.time())

    if _cached_token and now < _expires_at - 60:
        return _cached_token

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id
    }

    cert = (cert_path, key_path)

    r = requests.post(
        "https://auth-oces.datafordeler.dk/realms/distribution/protocol/openid-connect/token",
        data=data,
        cert=cert
    )

    r.raise_for_status()

    token_data = r.json()

    _cached_token = token_data["access_token"]
    _expires_at = now + token_data.get("expires_in", 3600)

    return _cached_token
