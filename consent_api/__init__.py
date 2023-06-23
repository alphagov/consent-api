"""FastAPI app."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from consent_api import config
from consent_api.routers import consent
from consent_api.routers import self_service

app = FastAPI(
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
        ),
        Middleware(
            SessionMiddleware,
            secret_key=config.SECRET_KEY,
        ),
    ],
)
app.include_router(consent.router)
app.include_router(self_service.router)

app.mount("/static", StaticFiles(directory="consent_api/static"), name="static")
