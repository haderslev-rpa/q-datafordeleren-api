# test_api_call.py
# Simulerer API-kald som Blue Prism.

import os

import requests
from automation_server_client import (
    AutomationServer,
    Credential
)
from dotenv import load_dotenv


# -------------------------------------------------
# Indlæs .env
# -------------------------------------------------

load_dotenv()


# -------------------------------------------------
# Initialisér Automation Server
# -------------------------------------------------

AutomationServer.from_environment()


# -------------------------------------------------
# Hent credentials
# -------------------------------------------------

credential = Credential.get_credential(
    "API_DATAFORDELEREN"
)

config = credential.data

CLIENT_ID = config["client_id"]
CERT_PATH = config["cert_path"]
KEY_PATH = config["key_path"]
API_KEY = config["intern_app_api_key"]


# -------------------------------------------------
# Hent testdata fra .env
# -------------------------------------------------

CPR = os.getenv("cpr1")
CVR = os.getenv("cvr1")
CPR_CVR = os.getenv("cprcvr1")
URL = os.getenv("URL")


# -------------------------------------------------
# Vælg payload ud fra URL
# -------------------------------------------------

if not URL:
    raise RuntimeError(
        "URL mangler i .env"
    )

if URL.rstrip("/").endswith("/cvr"):
    payload = {
        "cvr": CVR,
        "client_id": CLIENT_ID,
        "cert_path": CERT_PATH,
        "key_path": KEY_PATH
    }

elif URL.rstrip("/").endswith("/cvr/person"):
    payload = {
        "cpr": CPR_CVR,
        "client_id": CLIENT_ID,
        "cert_path": CERT_PATH,
        "key_path": KEY_PATH
    }

else:
    payload = {
        "cpr": CPR,
        "client_id": CLIENT_ID,
        "cert_path": CERT_PATH,
        "key_path": KEY_PATH
    }


# -------------------------------------------------
# Headers
# -------------------------------------------------

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}


# -------------------------------------------------
# Send request
# -------------------------------------------------

print("🚀 Sender API request...\n")
print("URL:", URL)

try:
    response = requests.post(
        URL,
        json=payload,
        headers=headers,
        timeout=120
    )

except requests.RequestException as error:
    print("\n❌ Kunne ikke kontakte API'et")
    print("Fejl:", str(error))
    raise SystemExit(1)


print("🔍 Statuskode:", response.status_code)

if response.status_code != 200:
    print("\n❌ FEJL:")
    print(response.text)

else:
    print("\n✅ Der er hul igennem")
    print("✅ RESULTAT:")
    print(response.json())