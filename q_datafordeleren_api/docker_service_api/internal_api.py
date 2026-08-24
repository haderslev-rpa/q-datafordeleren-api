### OBS OBS OBS ###
# FILER ER LAVET TIL ATS, HVOR INDHOLDET
# ER LAGT IND OG KORER I DOCKER.

import os

from flask import Flask, request, jsonify

from q_datafordeleren_api.docker_service_api.to_blue_prism_use import (
    get_aktuel_navn_og_adresse,
    lookup_cpr_full,
    lookup_cpr_in_cvr,
    lookup_cvr_basic
)


app = Flask(__name__)

API_KEY = os.getenv(
    "INTERN_APP_API_KEY"
)


def check_api_key(req):
    """
    Kontrollerer den interne API-nogle.
    """

    return (
        req.headers.get("x-api-key")
        == API_KEY
    )


# -------------------------------------------------
# CPR: aktuelt navn og adresse
# -------------------------------------------------

@app.route("/cpr", methods=["POST"])
def cpr():
    """
    Henter aktuelt navn og adresse fra CPR.

    Forventet JSON-input:

    {
        "cpr": "DDMMAAXXXX",
        "client_id": "...",
        "cert_path": "...",
        "key_path": "..."
    }
    """

    if not check_api_key(request):
        return jsonify(
            {
                "error": "Unauthorized"
            }
        ), 401

    data = request.json

    try:
        result = get_aktuel_navn_og_adresse(
            data["cpr"],
            data["client_id"],
            data["cert_path"],
            data["key_path"]
        )

        return jsonify(result)

    except Exception as error:
        return jsonify(
            {
                "error": str(error)
            }
        ), 500


# -------------------------------------------------
# CPR: fuldt opslag
# -------------------------------------------------

@app.route("/cpr/full", methods=["POST"])
def cpr_full():
    """
    Henter fulde CPR-oplysninger.

    Resultatet indeholder blandt andet:

    - navn
    - adresse
    - personstatus
    - personnumre
    - statsborgerskab
    - civilstand
    - born
    - foraeldre
    """

    if not check_api_key(request):
        return jsonify(
            {
                "error": "Unauthorized"
            }
        ), 401

    data = request.json

    try:
        result = lookup_cpr_full(
            data["cpr"],
            data["client_id"],
            data["cert_path"],
            data["key_path"]
        )

        return jsonify(result)

    except Exception as error:
        return jsonify(
            {
                "error": str(error)
            }
        ), 500


# -------------------------------------------------
# CVR: grundlaeggende virksomhedsopslag
# -------------------------------------------------

@app.route("/cvr", methods=["POST"])
def cvr():
    """
    Henter grundlaeggende CVR-oplysninger.

    Forventet JSON-input:

    {
        "cvr": "12345678",
        "client_id": "...",
        "cert_path": "...",
        "key_path": "..."
    }

    Resultatet indeholder blandt andet:

    - virksomhedsnavn
    - virksomhedsstatus
    - virksomhedsform
    - branche
    - adresse
    - telefonnummer
    - e-mailadresse
    """

    if not check_api_key(request):
        return jsonify(
            {
                "error": "Unauthorized"
            }
        ), 401

    data = request.json

    try:
        result = lookup_cvr_basic(
            data["cvr"],
            data["client_id"],
            data["cert_path"],
            data["key_path"]
        )

        return jsonify(result)

    except Exception as error:
        return jsonify(
            {
                "error": str(error)
            }
        ), 500


# -------------------------------------------------
# CVR: CPR til CVRPerson
# -------------------------------------------------

@app.route("/cvr/person", methods=["POST"])
def cvr_person():
    """
    Undersoger, om et CPR-nummer findes i CVR.

    Forventet JSON-input:

    {
        "cpr": "DDMMAAXXXX",
        "client_id": "...",
        "cert_path": "...",
        "key_path": "..."
    }

    Resultatet indeholder:

    - om personen findes i CVR
    - CVRPerson-id
    - status
    - virkningsdatoer
    - registreringsdatoer

    Resultatet indeholder ikke virksomhedens
    CVR-nummer.
    """

    if not check_api_key(request):
        return jsonify(
            {
                "error": "Unauthorized"
            }
        ), 401

    data = request.json

    try:
        result = lookup_cpr_in_cvr(
            data["cpr"],
            data["client_id"],
            data["cert_path"],
            data["key_path"]
        )

        return jsonify(result)

    except Exception as error:
        return jsonify(
            {
                "error": str(error)
            }
        ), 500


# -------------------------------------------------
# Health check
# -------------------------------------------------

@app.route("/health")
def health():
    """
    Kontrollerer, om API'et korer.
    """

    return jsonify(
        {
            "status": "ok"
        }
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )