# test_api_call.py
# simulerer API kald (som Blue Prism)

import requests  # bibliotek (HTTP kald)
import os  # modul (miljøvariabler)

from automation_server_client import AutomationServer, Credential  # klasser (API-adgang)
from dotenv import load_dotenv  # funktion (indlæser .env)

# -------------------------------------------------
# Init automation server (påkrævet)
# -------------------------------------------------
AutomationServer.from_environment()

# -------------------------------------------------
# Hent credentials (ALT fra samme)
# -------------------------------------------------
cred = Credential.get_credential("API_DATAFORDELEREN")
cfg = cred.data  # dict (nøgler/værdier)

CLIENT_ID = cfg["client_id"]
CERT_PATH = cfg["cert_path"]
KEY_PATH = cfg["key_path"]

# ✅ HER ER FIXET 👇
API_KEY = cfg["intern_app_api_key"]

# -------------------------------------------------
# CPR fra .env
# -------------------------------------------------
load_dotenv()
CPR = os.getenv("cpr1")
URL = os.getenv("URL")

# -------------------------------------------------
# Payload
# -------------------------------------------------
payload = {
    "cpr": CPR,
    "client_id": CLIENT_ID,
    "cert_path": CERT_PATH,
    "key_path": KEY_PATH
}

# -------------------------------------------------
# Headers (✅ med API KEY)
# -------------------------------------------------
headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

# -------------------------------------------------
# Send request
# -------------------------------------------------
print("🚀 Sender API request...\n")

response = requests.post(URL, json=payload, headers=headers)

print("🔍 Status kode:", response.status_code)

if response.status_code != 200:
    print("\n❌ FEJL:")
    print(response.text)
else:
    print("\n✅ RESULTAT:")
    print(response.json())