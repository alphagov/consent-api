"""Views."""
from flask import json
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask.typing import ResponseReturnValue
from flask_cors import cross_origin

from consent_api import app
from consent_api.forms import ServiceForm
from consent_api.forms import SignInForm
from consent_api.forms import SignUpForm
from consent_api.models import CookieConsent
from consent_api.models import UserConsent


@app.get("/api/v1/consent/", defaults={"uid": None})
@app.get("/api/v1/consent/<uid>")
@cross_origin(origins="*")
def get_consent(uid):
    """
    Return a JSON object of the consent status for the specified user.

    If the user is not specified, create a new user ID and return it with a null consent
    status.
    """
    consent = UserConsent.get(uid)
    return jsonify(consent.json)


@app.post("/api/v1/consent/", defaults={"uid": None})
@app.post("/api/v1/consent/<uid>")
@cross_origin(origins="*")
def set_consent(uid):
    """
    Set the consent status of the specified user to the value in the request body.

    The request body must be application/x-www-form-urlencoded to avoid triggering a
    CORS preflight request.

    The body must contain a single name/value pair, with the name `status`, and the
    value must be a JSON object encoded as a string.
    """
    user = UserConsent.get(uid)
    # application/x-www-form-urlencoded body to keep the CORS request simple
    status = request.form["status"]
    # status field contains stringified JSON object
    status = json.loads(status)
    # TODO validation
    consent = CookieConsent(**status)
    user.update(consent=consent)
    return jsonify(user.json)


@app.get("/")
def home() -> str:
    """Display a welcome page and self-service sign up CTA."""
    return render_template(
        "welcome.html",
        **{
            "num_orgs": 1234,
            "num_services": 2468,
        },
    )


@app.route("/create_account", methods=["GET", "POST"])
def create_account() -> ResponseReturnValue:
    """Show a signup form."""
    form = SignUpForm()
    if form.validate_on_submit():
        return redirect(url_for("signup_continue"))
    return render_template("create-account.html", form=form)


@app.route("/signup-continue")
def signup_continue() -> str:
    """Let the user know their signup confirmation email is sent."""
    return render_template("signup_continue.html")


@app.route("/login", methods=["GET", "POST"])
def login() -> ResponseReturnValue:
    """Show a login form."""
    form = SignInForm()
    if form.validate_on_submit():
        return redirect(url_for("dashboard"))
    return render_template("signin.html", form=form)


@app.get("/forgot_password")
def forgot_password() -> str:
    """Show a password reset request form."""
    return "Password reset coming soon"


services = {
    "haas": {
        "name": "Hexagrams as a Service",
        "domain": "haas-j4f7bdslta-nw.a.run.app",
    },
    "juggling_licence": {
        "name": "Apply for a Juggling Licence",
        "domain": "apply-juggling-licence-j4f7bdslta-nw.a.run.app",
    },
}


@app.get("/dashboard")
def dashboard() -> str:
    """Show dashboard."""
    return render_template("dashboard.html", services=services)


@app.get("/services/<service_id>")
def service(service_id) -> str:
    """Show service details."""
    service = services[service_id]
    return render_template("service.html", service=service)


@app.route("/add-service", methods=["GET", "POST"])
def add_service() -> ResponseReturnValue:
    """Add a service."""
    form = ServiceForm()
    if form.validate_on_submit():
        service_id = 1
        return redirect(url_for("service", service_id=service_id))
    return render_template("add-service.html", form=form)


@app.get("/clients")
def list_clients() -> str:
    """Show a list of existing client services and organisations."""
    return "Client list coming soon"


@app.get("/contact")
def contact_us() -> str:
    """Show a contact form."""
    return "Contact form coming soon"


@app.get("/status")
def statuses() -> str:
    """Display the contents of the consent status database table."""
    return render_template("statuses.html", users=UserConsent.get_all())


@app.get("/health")
def health():
    """Check the API is able to respond to requests."""
    try:
        UserConsent.get_all()
    except Exception:
        raise
    else:
        return "Healthy: OK"
