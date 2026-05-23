"""Google Gemini LLM client — wraps ChatGoogleGenerativeAI for the pipeline."""

import functools
import logging
from typing import Any

from langchain_core.language_models import BaseChatModel

from .config import settings

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def get_llm() -> BaseChatModel:
    """
    Get a cached ChatGoogleGenerativeAI instance.

    Model and parameters are loaded from environment variables:
    - GEMINI_MODEL        (e.g. gemini-2.0-flash, gemini-1.5-pro)
    - GEMINI_TEMPERATURE
    - GEMINI_MAX_TOKENS
    - GEMINI_API_KEY      (Google AI Studio key)
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            temperature=settings.gemini_temperature,
            max_output_tokens=settings.gemini_max_tokens,
            google_api_key=settings.gemini_api_key,
        )
    except Exception as e:
        logger.error(f"Failed to initialize Gemini LLM: {e}")
        raise


@functools.lru_cache(maxsize=1)
def get_langfuse_callback() -> Any | None:
    """Get a cached Langfuse callback handler for LangChain."""
    has_keys = bool(settings.langfuse_public_key) and bool(settings.langfuse_secret_key)
    if not has_keys:
        return None

    try:
        from langfuse.langchain import CallbackHandler

        return CallbackHandler()
    except Exception as e:
        logger.warning(f"Failed to create Langfuse callback: {e}")
        return None


def get_lc_config(node: str, parent_config: dict | None = None) -> dict:
    """Build LangChain config with Langfuse callback and node metadata.

    When *parent_config* is provided (e.g. the RunnableConfig propagated by
    LangGraph), callbacks and metadata are merged so that every LLM call
    appears under a single Langfuse trace instead of spawning separate ones.
    """
    if parent_config is not None:
        cfg = dict(parent_config)
        metadata = dict(cfg.get("metadata") or {})
        metadata["node"] = node
        cfg["metadata"] = metadata
        return cfg

    # Fallback: standalone config (e.g. when called outside the graph)
    cfg: dict[str, Any] = {"metadata": {"node": node}}
    cb = get_langfuse_callback()
    if cb is not None:
        cfg["callbacks"] = [cb]
    return cfg
