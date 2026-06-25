from pprint import pprint
import os
from dotenv import load_dotenv

from q_datafordeleren_api.functionality.datafordeler_use import get_aktuel_navn_og_adresse

load_dotenv()

TEST_CPR = os.getenv("cpr1")

print("\n🚀 TEST: AKTUEL NAVN OG ADRESSE\n")

try:
    result = get_aktuel_navn_og_adresse(TEST_CPR)

    pprint(result, width=120)

except Exception as e:
    print("\n❌ FEJL\n")
    print(e)
