from pprint import pprint  # funktion (pæn udskrift)
import os  # modul (miljø)
from dotenv import load_dotenv  # funktion (indlæser .env)

from q_datafordeleren_api.functionality.datafordeler_client import DatafordelerClient  # klasse (API klient)

# -------------------------------------------------
# Load .env
# -------------------------------------------------
load_dotenv()

TEST_CPR = os.getenv("cpr1")  # variabel (CPR fra .env)

print("\n🚀 TEST: FULL CPR DATA\n")
print(f"🔍 CPR: {TEST_CPR}\n")

try:
    client = DatafordelerClient()  # objekt (instans af klasse)

    # ✅ Options (du kan ændre disse)
    options = {
        "navn": True,
        "adresse": True,
        "beskyttelser": True,
        "civilstand": True,
        "boern": True
    }

    result = client.lookup_cpr_full(TEST_CPR)

    
    data = result.get("data", {}).get("CPRCustom_PublicSectorPerson", {})

    print("\n✅ RESULTAT (nodes):\n")
    pprint(data.get("nodes", []), width=120)


except Exception as e:
    print("\n❌ FEJL I FULL CPR TEST\n")
    print(e)
