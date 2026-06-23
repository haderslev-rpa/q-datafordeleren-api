from pprint import pprint  # funktion (pæn udskrift)

from q_datafordeleren_api.datafordeler_auth import get_token  # funktion (hent token)


print("\n🚀 TEST: HENT TOKEN FRA DATAFORDELER\n")

try:
    token = get_token()  # funktion kaldes

    print("✅ TOKEN HENTET!\n")

    print("🔐 Token (forkortet):")
    pprint(token[:80] + "...", width=120)  # viser første del

except Exception as e:
    print("\n❌ FEJL VED TOKEN KALD\n")
    print("Fejlbesked:")
    print(e)