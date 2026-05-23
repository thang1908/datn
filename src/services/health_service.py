"""Shared health check functions used by both /health and /connections routes."""

import logging

from src.core.config import settings

logger = logging.getLogger(__name__)


async def check_mongodb() -> tuple[str, dict]:
    """Check MongoDB connectivity."""
    try:
        from src.db import get_db

        db = await get_db()
        await db.command("ping")
        return "ok", {
            "uri": settings.mongodb_uri,
            "database": settings.mongodb_db_name,
        }
    except Exception as e:
        logger.error(f"MongoDB check failed: {e}")
        return "error", {"error": str(e)}


async def check_gemini() -> tuple[str, dict]:
    """Check Google Gemini API connectivity."""
    try:
        from src.core.litellm_client import get_llm

        llm = get_llm()
        await llm.ainvoke("ping")
        return "ok", {
            "model": settings.gemini_model,
        }
    except Exception as e:
        logger.error(f"Gemini check failed: {e}")
        return "error", {"error": str(e)}


async def check_langfuse() -> tuple[str, dict]:
    """Check Langfuse connectivity."""
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return "ok", {"status": "not_configured"}

    try:
        from src.core.litellm_client import get_langfuse_callback

        get_langfuse_callback()
        return "ok", {"host": settings.langfuse_host}
    except Exception as e:
        logger.error(f"Langfuse check failed: {e}")
        return "error", {"error": str(e)}


async def run_all_checks() -> dict[str, dict]:
    """Run all health checks and return aggregated results."""
    checks = {}

    for name, check_fn in [
        ("mongodb", check_mongodb),
        ("gemini", check_gemini),
        ("langfuse", check_langfuse),
    ]:
        status, info = await check_fn()
        checks[name] = {"status": status, **info}

    return checks
