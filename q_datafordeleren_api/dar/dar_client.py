#DAR bruges ikke længere, det var en nødløsning til at få adresseoplysninger, men datafordeleren ser ud til at have det hele.

import requests


class DarServiceError(Exception):
    """Fejl (custom exception)"""
    pass


class DarClient:

    def __init__(self):
        self.base_url = "https://api.dataforsyningen.dk"
        self._cache = {}

    def get_adresse_info(self, vejnavn, husnummer, postnummer):
        """Fuld lookup (funktion (genbrugelig kodeblok))"""

        key = f"{vejnavn}-{husnummer}-{postnummer}"

        if key in self._cache:
            return self._cache[key]

        # ✅ tomt resultat (fallback struktur)
        empty = {
            "etage": "",
            "sidedoer": "",
            "postdistrikt": "",
            "kommune": "",
            "kommunenr": ""
        }

        if not postnummer:
            return empty

        # -------------------------------------------------
        # ✅ 1. prøv ENHEDSADRESSE (giver etage/dør)
        # -------------------------------------------------
        try:
            r = requests.get(
                f"{self.base_url}/adresser",
                params={
                    "vejnavn": vejnavn,
                    "husnr": husnummer,
                    "postnr": postnummer
                },
                timeout=3
            )

            if r.status_code == 200:
                data = r.json()

                # ✅ kun hvis præcis én adresse
                if len(data) == 1:
                    adr = data[0]

                    result = {
                        "etage": adr.get("etage", "") or "",
                        "sidedoer": adr.get("dør", "") or "",
                        "postdistrikt": adr.get("postnummer", {}).get("navn", ""),
                        "kommune": adr.get("kommune", {}).get("navn", ""),
                        "kommunenr": adr.get("kommune", {}).get("kode", "")
                    }

                    self._cache[key] = result
                    return result

        except Exception:
            pass

        # -------------------------------------------------
        # ✅ 2. fallback til ADGANGSADRESSE
        # -------------------------------------------------
        try:
            r = requests.get(
                f"{self.base_url}/adgangsadresser",
                params={
                    "vejnavn": vejnavn,
                    "husnr": husnummer,
                    "postnr": postnummer
                },
                timeout=3
            )

            if r.status_code == 200:
                data = r.json()

                if data:
                    adr = data[0]

                    result = {
                        "etage": "",   # findes ikke her
                        "sidedoer": "",
                        "postdistrikt": adr.get("postnummer", {}).get("navn", ""),
                        "kommune": adr.get("kommune", {}).get("navn", ""),
                        "kommunenr": adr.get("kommune", {}).get("kode", "")
                    }

                    self._cache[key] = result
                    return result

        except Exception:
            pass

        return empty