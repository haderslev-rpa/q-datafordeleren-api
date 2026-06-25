### OBS OBS OBS###
#FILER ER LAVET TIL ATS HVOR INDHOLDET ER LAGT IND IND OG KØRER I DOCKER.


from flask import Flask, request, jsonify
from q_datafordeleren_api.docker_service_api.to_blue_prism_use import get_aktuel_navn_og_adresse
import os

app = Flask(__name__)

API_KEY = os.getenv("INTERN_APP_API_KEY")


def check_api_key(req):
    return req.headers.get("x-api-key") == API_KEY


@app.route("/cpr", methods=["POST"])
def cpr():

    if not check_api_key(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json

    try:
        result = get_aktuel_navn_og_adresse(
            data["cpr"],
            data["client_id"],
            data["cert_path"],
            data["key_path"]
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)