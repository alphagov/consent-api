"""FastAPI app."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_etag import add_exception_handler
from starlette.middleware.sessions import SessionMiddleware

from consent_api import config
from consent_api.routers import consent
from consent_api.routers import self_service

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=config.SECRET_KEY,
)
app.include_router(consent.router)
app.include_router(self_service.router)

add_exception_handler(app)

app.mount("/static", StaticFiles(directory="consent_api/static"), name="static")
