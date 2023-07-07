"""Healthcheck router."""

from fastapi import APIRouter

router = APIRouter(include_in_schema=False)


@router.get("/health")
async def check_health() -> None:
    """Simple endpoint to check app is running."""
