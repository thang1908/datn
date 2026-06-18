"""Node: Unified conversation summarization."""

import logging

from langchain_core.runnables import RunnableConfig

from src.core.litellm_client import get_lc_config, get_llm
from src.utils.prompts import SUMMARY_CONVERSATION_PROMPT
from src.models.pipeline import SummaryOutput
from ..state import CallState

logger = logging.getLogger(__name__)


async def summarize_conversation(state: CallState, config: RunnableConfig) -> dict:
    """Summarize a single call conversation.

    Uses a single unified prompt for all conversations
    and returns a single ``summary`` string.
    """
    transcript = state.get("transcript", "")

    prompt = SUMMARY_CONVERSATION_PROMPT

    llm = get_llm().with_structured_output(SummaryOutput)
    chain = prompt | llm
    try:
        result = await chain.ainvoke(
            {"user_raw_text": transcript},
            config=get_lc_config("summarize_conversation", config),
        )
    except Exception as e:
        logger.error(f"Summarization LLM call failed: {e}", exc_info=True)
        raise

    if isinstance(result, dict):
        summary = str(result.get("summary", "")).strip()
    else:
        summary = str(result.summary).strip()

    return {
        "summary": summary,
    }
