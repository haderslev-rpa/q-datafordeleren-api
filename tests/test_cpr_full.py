from pprint import pprint
import os
from dotenv import load_dotenv

from q_datafordeleren_api.functionality.datafordeler_use import lookup_cpr_full

load_dotenv()

TEST_CPR = os.getenv("cpr_doed")

print("\n🚀 TEST: FULL CPR DATA\n")

try:
    result = lookup_cpr_full(TEST_CPR)

    pprint(result, width=120)

except Exception as e:
    print("\n❌ FEJL\n")
    print(e)