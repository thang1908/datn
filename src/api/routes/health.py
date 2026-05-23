"""Health check routes."""

from fastapi import APIRouter

from src.services.health_service import run_all_checks

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health() -> dict:
    """Basic liveness probe - returns 200 OK if app is running."""
    return {"status": "ok"}


@router.get("/ready")
async def readiness() -> dict:
    """Readiness probe - returns 200 only if all downstream services are reachable."""
    checks = await run_all_checks()
    all_ok = all(c.get("status") == "ok" for c in checks.values())

    return {
        "status": "ready" if all_ok else "not_ready",
        "checks": checks,
    }
