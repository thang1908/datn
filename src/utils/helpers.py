from typing import Any, Dict

from .constants import CRITERION_ORDER, DEFAULT_CASE_TYPE, RUBRIC


def compute_total_score(criteria_scores: Dict[str, Any]) -> float:
    weighted_total = 0.0
    for criterion in CRITERION_ORDER:
        raw_score = criteria_scores.get(criterion, 0)
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            score = 0.0
        score = max(0.0, min(10.0, score))
        weighted_total += score * float(RUBRIC[criterion]["weight"])
    return round(weighted_total, 1)


def normalize_case_type(case_type: str) -> str:
    """Normalize case type, defaulting to the standard fallback."""
    return case_type.strip() or DEFAULT_CASE_TYPE


def normalize_resolved(resolved: str) -> str:
    """Normalize resolved status to one of YES/NO/REVIEW."""
    val = resolved.strip().upper()
    return val if val in ("YES", "NO", "REVIEW") else "REVIEW"
