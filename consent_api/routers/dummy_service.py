"""Dummy service for end-to-end testing."""


from fastapi import APIRouter
from fastapi import Request
from starlette.responses import Response

from consent_api import config
from consent_api.jinja import templates

router = APIRouter(include_in_schema=False)
get = router.get

DUMMY_SERVICE_PREFIX = "/dummy-service"
OTHER_SERVICE_URL = f"{config.OTHER_SERVICE_ORIGIN}{DUMMY_SERVICE_PREFIX}/"


@get("/")
async def dummy_home(request: Request) -> Response:
    """Show a service home page."""
    return templates.TemplateResponse(
        "dummy_service/home.html",
        {"request": request},
    )


@get("/start-page")
async def start_page(request: Request) -> Response:
    """Show a start page."""
    return templates.TemplateResponse(
        "dummy_service/start.html",
        {
            "OTHER_SERVICE_URL": OTHER_SERVICE_URL,
            "request": request,
        },
    )


@get("/landing-page")
async def landing_page(request: Request) -> Response:
    """Show a landing page."""
    return templates.TemplateResponse(
        "dummy_service/landing.html",
        {"request": request},
    )


@get("/cookies")
async def cookies_page(request: Request) -> Response:
    """Show a cookie settings form."""
    return templates.TemplateResponse(
        "dummy_service/cookies.html",
        {"request": request},
    )
