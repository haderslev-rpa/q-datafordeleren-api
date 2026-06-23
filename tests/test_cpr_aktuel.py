from pprint import pprint  # funktion (pæn udskrift)
import os  # modul (miljø)
from dotenv import load_dotenv  # funktion (indlæser .env)

from q_datafordeleren_api.functionality.datafordeler_client import DatafordelerClient  # klasse (API klient)

# -------------------------------------------------
# Load .env
# -------------------------------------------------
load_dotenv()

TEST_CPR = os.getenv("cpr1")  # variabel (CPR fra .env)

print("\n🚀 TEST: AKTUEL NAVN OG ADRESSE\n")
print(f"🔍 CPR: {TEST_CPR}\n")

try:
    client = DatafordelerClient()  # objekt (instans af klasse)

    result = client.get_aktuel_navn_og_adresse(TEST_CPR)

    print("✅ AKTUELT RESULTAT:\n")
    pprint(result, width=120)

except Exception as e:
    print("\n❌ FEJL I AKTUEL CPR TEST\n")
    print(e)