"""Node: Unified conversation summarization (direction-based prompt selection)."""

import logging

from langchain_core.runnables import RunnableConfig

from src.core.litellm_client import get_lc_config, get_llm
from src.utils.constants import DIRECTION_OUTBOUND
from src.utils.prompts import SUMMARY_CALL_INBOUND_PROMPT, SUMMARY_CALL_OUTBOUND_PROMPT
from src.models.pipeline import SummaryOutput
from ..state import CallState

logger = logging.getLogger(__name__)


async def summarize_conversation(state: CallState, config: RunnableConfig) -> dict:
    """Summarize a single call conversation.

    Selects the inbound or outbound prompt based on ``direction``
    and returns a single ``summary`` string.
    """
    transcript = state.get("transcript", "")
    direction = state.get("direction", 1)

    if direction == DIRECTION_OUTBOUND:
        prompt = SUMMARY_CALL_OUTBOUND_PROMPT
    else:
        prompt = SUMMARY_CALL_INBOUND_PROMPT

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
