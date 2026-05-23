"""Node 2a: Classification and case resolution detection."""

import logging

from langchain_core.runnables import RunnableConfig

from src.core.litellm_client import get_lc_config, get_llm
from ..state import CallState
from src.utils.helpers import normalize_case_type, normalize_resolved
from src.utils.prompts import CASE_AND_RESOLVED_PROMPT
from src.models.pipeline import ClassificationResolvedOutput

logger = logging.getLogger(__name__)


async def classify_and_resolved(state: CallState, config: RunnableConfig) -> dict:
    """
    Node 2a: Classify case type and determine resolution status.

    Accepts `transcript`, classifies case type and resolution status,
    outputs `case_type` and `resolved` status.
    """
    transcript = state.get("transcript", "")
    llm = get_llm().with_structured_output(ClassificationResolvedOutput)
    chain = CASE_AND_RESOLVED_PROMPT | llm
    try:
        result = await chain.ainvoke(
            {"transcript": transcript},
            config=get_lc_config("classify_and_resolved", config),
        )
    except Exception as e:
        logger.error(f"Classification LLM call failed: {e}", exc_info=True)
        raise

    if isinstance(result, dict):
        case_type = str(result.get("case_type", ""))
        resolved_raw = str(result.get("resolved", ""))
    else:
        case_type = str(result.case_type)
        resolved_raw = str(result.resolved)

    return {
        "case_type": normalize_case_type(case_type),
        "resolved": normalize_resolved(resolved_raw),
    }
