"""Node 3: Negative sentiment and interaction analysis."""

import logging

from langchain_core.runnables import RunnableConfig

from src.core.litellm_client import get_lc_config, get_llm
from ..state import CallState
from src.utils.constants import NEGATIVE_REASON_MAP
from src.utils.helpers import normalize_case_type, normalize_resolved
from src.utils.prompts import NEGATIVE_ONLY_PROMPT
from src.models.pipeline import NegativeDetectionOutput

logger = logging.getLogger(__name__)


async def analyze_negative(state: CallState, config: RunnableConfig) -> dict:
    """
    Node 3: Detect negative sentiment and interaction patterns.

    Accepts `transcript`, detects negative sentiment/interactions,
    outputs `is_negative`, `negative_reason_code`, and `negative_reason_description`.
    """
    transcript = state.get("transcript", "")
    case_type = normalize_case_type(state.get("case_type", ""))
    resolved = normalize_resolved(str(state.get("resolved", "REVIEW")))
    llm = get_llm().with_structured_output(NegativeDetectionOutput)
    chain = NEGATIVE_ONLY_PROMPT | llm
    try:
        parsed_result = await chain.ainvoke(
            {
                "transcript": transcript,
                "case_type": case_type,
                "resolved": resolved,
            },
            config=get_lc_config("analyze_negative", config),
        )
    except Exception as e:
        logger.error(f"Negative analysis LLM call failed: {e}", exc_info=True)
        raise
    raw_result = (
        parsed_result if isinstance(parsed_result, dict) else parsed_result.model_dump()
    )

    raw_codes = raw_result.get("negative_reason_code")
    codes = (
        [str(code).strip().upper() for code in raw_codes]
        if isinstance(raw_codes, list)
        else []
    )

    unique_codes: list[str] = []
    for code in codes:
        if code in NEGATIVE_REASON_MAP and code not in unique_codes:
            unique_codes.append(code)

    if resolved == "YES":
        is_negative = "FALSE"
        final_codes: list[str] = []
    elif resolved == "REVIEW":
        is_negative = "REVIEW"
        final_codes = []
    else:
        is_negative = "TRUE" if unique_codes else "REVIEW"
        final_codes = unique_codes if unique_codes else []

    descriptions = [NEGATIVE_REASON_MAP[code] for code in final_codes]

    return {
        "is_negative": is_negative,
        "negative_reason_code": final_codes,
        "negative_reason_description": descriptions,
    }
