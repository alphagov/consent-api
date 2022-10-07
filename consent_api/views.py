from flask import render_template, jsonify, json, request
from flask_cors import cross_origin
from consent_api import app
from consent_api.models import User, ConsentStatus


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
    user.consent_status = ConsentStatus(**json.loads(request.form["status"]))
    return "", 204


@app.route("/")
def home() -> str:
    return render_template("index.html", users=User.get_all())


@app.get("/<uid>")
def user(uid) -> str:
    user = User(uid)
    return render_template("user.html", user=user)
