"""Connection check routes."""

from fastapi import APIRouter, HTTPException

from src.services.health_service import (
    check_langfuse,
    check_gemini,
    check_mongodb,
    run_all_checks,
)

router = APIRouter(prefix="/connections", tags=["connections"])


@router.get("")
async def connections() -> dict:
    """Run all connectivity checks."""
    return await run_all_checks()


async def _check_or_503(check_fn, service_name: str) -> dict:
    """Run a check function; raise 503 if it fails."""
    status, info = await check_fn()
    if status != "ok":
        raise HTTPException(
            status_code=503, detail=f"{service_name} unavailable: {info.get('error', 'unknown')}"
        )
    return {"status": status, **info}


@router.get("/mongodb")
async def mongodb_check() -> dict:
    """Check MongoDB connectivity."""
    return await _check_or_503(check_mongodb, "MongoDB")


@router.get("/gemini")
async def gemini_check() -> dict:
    """Check Google Gemini API connectivity."""
    return await _check_or_503(check_gemini, "Gemini")


@router.get("/langfuse")
async def langfuse_check() -> dict:
    """Check Langfuse connectivity."""
    return await _check_or_503(check_langfuse, "Langfuse")
