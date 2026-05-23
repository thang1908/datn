"""Node 4: QA scoring against conversation quality criteria."""

import logging

from langchain_core.runnables import RunnableConfig

from src.core.litellm_client import get_lc_config, get_llm
from ..state import CallState
from src.utils.helpers import compute_total_score, normalize_case_type, normalize_resolved
from src.utils.prompts import SCORE_QA_PROMPT
from src.models.pipeline import QAScoringOutput

logger = logging.getLogger(__name__)


async def score_qa(state: CallState, config: RunnableConfig) -> dict:
    """Score conversation against QA criteria."""
    transcript = state.get("transcript", "")
    case_type = normalize_case_type(state.get("case_type", ""))
    resolved = normalize_resolved(str(state.get("resolved", "REVIEW")))
    llm = get_llm().with_structured_output(QAScoringOutput)
    chain = SCORE_QA_PROMPT | llm
    try:
        parsed_result = await chain.ainvoke(
            {
                "transcript": transcript,
                "case_type": case_type,
                "resolved": resolved,
            },
            config=get_lc_config("score_qa", config),
        )
    except Exception as e:
        logger.error(f"QA scoring LLM call failed: {e}", exc_info=True)
        raise
    raw_result = (
        parsed_result if isinstance(parsed_result, dict) else parsed_result.model_dump()
    )

    raw_violations = raw_result.get("violations")
    violations = raw_violations if isinstance(raw_violations, list) else []

    raw_scores = raw_result.get("criteria_scores")
    criteria_scores = raw_scores if isinstance(raw_scores, dict) else {}
    total_score = compute_total_score(criteria_scores)

    return {
        "criteria_scores": criteria_scores,
        "total_score": total_score,
        "violations": violations,
    }
