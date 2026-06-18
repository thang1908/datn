"""Pipeline execution service — core business logic decoupled from HTTP layer."""

import asyncio
import logging
from datetime import datetime, timezone

from src.core.config import settings
from src.core.litellm_client import get_langfuse_callback
from src.db import save_conversation
from src.graph.graph import call_graph
from src.graph.state import CallState

logger = logging.getLogger(__name__)

_semaphore: asyncio.Semaphore | None = None


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(settings.pipeline_concurrency)
    return _semaphore


def _build_conversation_id(call_id: str) -> str:
    """Build a unique conversation ID from call_id."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"CALL-{date_str}-{call_id}"


async def process_crm_message(message: dict) -> dict:
    """Run the Call pipeline and return analysis results.

    Args:
        message: Request dict with keys:
            CallId (str), AudioLink (str)

    Returns:
        Analysis result dict in PascalCase format.

    Raises:
        ValueError: If required fields are missing.
    """
    call_id = message.get("CallId")
    audio_link = message.get("AudioLink")

    if not call_id:
        raise ValueError("Missing required field: CallId")
    if not audio_link:
        raise ValueError("Missing required field: AudioLink")

    async with _get_semaphore():
        conversation_id = _build_conversation_id(call_id)

        initial_state: CallState = {
            "call_id": call_id,
            "audio_link": audio_link,
            "conversation_id": conversation_id,
        }

        langfuse_callback = get_langfuse_callback()
        config = {}
        if langfuse_callback is not None:
            config = {
                "callbacks": [langfuse_callback],
                "configurable": {"thread_id": conversation_id},
                "metadata": {
                    "conversation_id": conversation_id,
                    "call_id": call_id,
                    "pipeline": "call",
                },
            }

        try:
            result = await call_graph.ainvoke(initial_state, config=config or None)
        finally:
            if langfuse_callback is not None and hasattr(langfuse_callback, "flush"):
                try:
                    langfuse_callback.flush()
                except Exception as e:
                    logger.debug(f"Error flushing Langfuse callback: {e}")

        output_keys = [
            "ConversationId", "Transcript", "Summary",
            "IsNegative", "NegativeReasonCode", "NegativeReasonDescription",
            "CriteriaScores", "CaseType", "Resolved", "Violations",
        ]
        output = {k: result[k] for k in output_keys if k in result}

        await save_conversation(
            message_id=output.get("ConversationId", conversation_id),
            crm_output=output,
            call_id=call_id,
        )
        return output
