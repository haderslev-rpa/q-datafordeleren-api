from pprint import pprint
import os
from q_datafordeleren_api.functionality.datafordeler_use import (
    lookup_cpr_in_cvr
)

cpr =os.getenv("cprcvr1")

result = lookup_cpr_in_cvr(
    cpr
)

print()

pprint(
    result,
    width=150,
    sort_dicts=False
)