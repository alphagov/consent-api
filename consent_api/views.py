"""Views."""
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
    """
    Return a JSON object of the consent status for the specified user.

    If the user is not specified, create a new user ID and return it with a null consent
    status.
    """
    user = User(uid)
    return jsonify(uid=user.uid, status=user.consent_status)


@app.post("/consent/<uid>")
@cross_origin(origins="*")
def set_consent(uid):
    """
    Set the consent status of the specified user to the value in the request body.

    The request body must be application/x-www-form-urlencoded to avoid triggering a
    CORS preflight request.

    The body must contain a single name/value pair, with the name `status`, and the
    value must be a JSON object encoded as a string.
    """
    user = User(uid)
    # Use application/x-www-form-urlencoded body to keep the CORS request simple
    # status field contains stringified JSON object
    user.consent_status = ConsentStatus(**json.loads(request.form["status"]))
    return "", 204


@app.route("/")
def home() -> str:
    """Display the contents of the consent status database table."""
    return render_template("index.html", users=User.get_all())
