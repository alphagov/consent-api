"""FastAPI app."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_etag import add_exception_handler
from starlette.middleware.sessions import SessionMiddleware

from consent_api.config import settings
from consent_api.routers import consent
from consent_api.routers import dummy_service
from consent_api.routers import healthcheck
from consent_api.routers import self_service
from consent_api.util import register_origins_for_e2e_testing

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    if settings.flag_fixtures:
        await register_origins_for_e2e_testing()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
)
app.include_router(consent.router)
app.include_router(healthcheck.router)
app.include_router(self_service.router)
app.include_router(dummy_service.router, prefix=dummy_service.DUMMY_SERVICE_PREFIX)

add_exception_handler(app)

app.mount("/static", StaticFiles(directory="consent_api/static"), name="static")
app.mount("/client", StaticFiles(directory="client"), name="client")
