"""Dummy service for end-to-end testing."""

import os

from fastapi import APIRouter
from fastapi import Request
from starlette.responses import Response

from consent_api.jinja import templates

router = APIRouter(include_in_schema=False)
get = router.get

OTHER_URL = os.getenv("OTHER_URL")


@get("/dummy-service")
async def dummy_home(request: Request) -> Response:
    """Show a service home page."""
    return templates.TemplateResponse(
        "dummy_service/home.html",
        {"request": request},
    )


@get("/dummy-service/start-page")
async def start_page(request: Request) -> Response:
    """Show a start page."""
    return templates.TemplateResponse(
        "dummy_service/start.html",
        {
            "OTHER_URL": OTHER_URL,
            "request": request,
        },
    )


@get("/dummy-service/landing-page")
async def landing_page(request: Request) -> Response:
    """Show a landing page."""
    return templates.TemplateResponse(
        "dummy_service/landing.html",
        {"request": request},
    )


@get("/dummy-service/cookies")
async def cookies_page(request: Request) -> Response:
    """Show a cookie settings form."""
    return templates.TemplateResponse(
        "dummy_service/cookies.html",
        {"request": request},
    )
