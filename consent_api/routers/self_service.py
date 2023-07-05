"""Self-service admin mockup."""

from dataclasses import asdict
from dataclasses import dataclass

import fastapi
from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import Response

from consent_api import forms

router = APIRouter(include_in_schema=False)
get = router.get
post = router.post
url_for = router.url_path_for

templates = Jinja2Templates(directory="consent_api/templates")


# @docs.ignore()
@get("/")
async def home(request: Request) -> Response:
    """Display a welcome page and self-service sign up CTA."""
    return templates.TemplateResponse(
        "selfservice/home.html",
        {
            "num_orgs": 1234,
            "num_services": 2468,
            "request": request,
        },
    )


# @docs.ignore()
@get("/create-account")
def create_account(request: Request) -> Response:
    """Show a signup form."""
    return templates.TemplateResponse(
        "selfservice/create_account.html",
        {
            "form": forms.SignUpForm(),
            "request": request,
        },
    )


@dataclass
class UserDetails:
    """User details form data."""

    name: str = Form(...)
    email: str = Form(...)
    phone: str = Form(...)
    password: str = Form(...)


# @docs.ignore()
@post("/create-account")
def post_create_account_form(
    request: Request,
    user_details: UserDetails = fastapi.Depends(),
) -> Response:
    """Handle create account form submission."""
    request.session["user_details"] = asdict(user_details)
    return RedirectResponse(url_for("signup_continue"), status_code=302)


# @docs.ignore()
@get("/continue-signup")
def signup_continue(request: Request) -> Response:
    """Let the user know their signup confirmation email is sent."""
    return templates.TemplateResponse(
        "selfservice/signup_continue.html",
        {
            "request": request,
            "session": request.session,
        },
    )


# @docs.ignore()
@get("/login")
def login(request: Request) -> Response:
    """Show a login form."""
    return templates.TemplateResponse(
        "selfservice/login.html",
        {
            "form": forms.SignInForm(),
            "request": request,
        },
    )


# @docs.ignore()
@post("/login")
def post_login_form() -> Response:
    """Handle login form submission."""
    return RedirectResponse(url_for("dashboard"), status_code=302)


# @docs.ignore()
@get("/forgot_password")
def forgot_password() -> Response:
    """Show a password reset request form."""
    return HTMLResponse("Password reset coming soon")


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


# @docs.ignore()
@get("/dashboard")
def dashboard(request: Request) -> Response:
    """Show dashboard."""
    return templates.TemplateResponse(
        "selfservice/dashboard.html",
        {
            "services": services,
            "request": request,
        },
    )


# @docs.ignore()
@get("/services/{service_id}")
def service(request: Request, service_id: str) -> Response:
    """Show service details."""
    return templates.TemplateResponse(
        "selfservice/service.html",
        {
            "request": request,
            "service": services[service_id],
        },
    )


# @docs.ignore()
@get("/add-service")
def add_service(request: Request) -> Response:
    """Add a service."""
    return templates.TemplateResponse(
        "selfservice/add_service.html",
        {
            "form": forms.ServiceForm(),
            "request": request,
        },
    )


# @docs.ignore()
@post("/add-service")
def post_add_service_form() -> Response:
    """Handle add service form submission."""
    return RedirectResponse(url_for("service", service_id=1), status_code=302)


# @docs.ignore()
@get("/clients")
def list_clients() -> HTMLResponse:
    """Show a list of existing client services and organisations."""
    return HTMLResponse("Client list coming soon")


# @docs.ignore()
@get("/contact")
def contact_us() -> HTMLResponse:
    """Show a contact form."""
    return HTMLResponse("Contact form coming soon")


@get("/test-cors")
def test_cors(request: Request) -> Response:
    """Test CORS policy is working."""
    return templates.TemplateResponse(
        "selfservice/test_cors.html",
        {"request": request},
    )
