Formål
Dette projekt indeholder en Python‑løsning (program i Python), som bruges til at hente CPR‑data fra Datafordeleren (ekstern API for offentlige data).
Løsningen er lavet sådan, at den kan bruges på to måder:

Fra almindelig Python (lokalt eller i Automation Server)
Via et API (webservice (HTTP endpoint)), som kaldes fra Blue Prism


Struktur
Projektet er delt op i tre hoveddele:
core
Indeholder al den rigtige logik (forretningslogik):

datafordeler_auth.py → henter token (adgangsnøgle)
datafordeler_client.py → kalder Datafordeleren API

Denne del genbruges overalt og skal ikke ændres afhængigt af miljø.

functionality
Bruges når man kører Python direkte (lokalt eller i Automation Server).
Fil:

datafordeler_use.py

Her sker:

credentials (hemmelige data) hentes fra Automation Server
core‑funktionerne kaldes korrekt

Eksempel på brug:
Pythonfrom q_datafordeleren_api.functionality.datafordeler_use import get_aktuel_navn_og_adresseresult = get_aktuel_navn_og_adresse("0101701234")``Vis flere linjer

docker_service_api
Bruges når løsningen kører som API i Docker.
Filer:

internal_api.py → Flask app (webserver (program der svarer HTTP))
to_blue_prism_use.py → funktioner til API‑kald

Denne del bruges af Blue Prism.
