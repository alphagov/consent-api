from flask import json
from flask import jsonify
from flask import render_template
from flask import request
from flask_cors import cross_origin

from consent_api import app
from consent_api.models import ConsentStatus
from consent_api.models import User


@app.get("/consent", defaults={"uid": None})
@app.get("/consent/<uid>")
@cross_origin(origins="*")
def get_consent(uid):
    user = User(uid)
    return jsonify(uid=user.uid, status=user.consent_status)


@app.post("/consent/<uid>")
@cross_origin(origins="*")
def set_consent(uid):
    user = User(uid)
    # Use application/x-www-form-urlencoded body to keep the CORS request simple
    # status field contains stringified JSON object
    user.consent_status = ConsentStatus(**json.loads(request.form["status"]))
    return "", 204


@app.route("/")
def home() -> str:
    return render_template("index.html", users=User.get_all())
