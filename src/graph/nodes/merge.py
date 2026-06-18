"""Merge node: Final output assembly in CRM format."""

from ..state import CallState


def _pascal_case_turns(turns: list[dict]) -> list[dict]:
    """Convert transcript turns to PascalCase keys."""
    return [
        {"Speaker": t.get("speaker", ""), "Text": t.get("text", "")}
        for t in turns
    ]


def _pascal_case_scores(scores: dict) -> dict:
    """Convert criteria_scores to PascalCase keys."""
    return {
        "Communication": scores.get("communication", 0),
        "Attitude": scores.get("attitude", 0),
        "DataCollection": scores.get("data_collection", 0),
        "ProblemSolving": scores.get("problem_solving", 0),
    }


def _pascal_case_violations(violations: list[dict]) -> list[dict]:
    """Convert violation items to PascalCase keys."""
    result = []
    for v in violations:
        evidence = v.get("evidence") or []
        result.append({
            "CriterionId": v.get("criterion_id", ""),
            "ViolationCode": v.get("violation_code", ""),
            "Description": v.get("description", ""),
            "Deduction": v.get("deduction", 0),
            "Evidence": [
                {"Speaker": e.get("speaker", ""), "Text": e.get("text", "")}
                for e in evidence
            ],
        })
    return result


async def merge_output(state: CallState) -> dict:
    """
    Merge all parallel node outputs into final output format.

    Produces PascalCase keys for API response.
    """
    return {
        "ConversationId": state.get("conversation_id", ""),
        "Transcript": _pascal_case_turns(state.get("transcript_turns") or []),
        "Summary": state.get("summary", ""),
        "IsNegative": state.get("is_negative", "REVIEW"),
        "NegativeReasonCode": state.get("negative_reason_code") or [],
        "NegativeReasonDescription": state.get("negative_reason_description") or [],
        "CriteriaScores": _pascal_case_scores(state.get("criteria_scores") or {}),
        "CaseType": state.get("case_type", ""),
        "Resolved": state.get("resolved", "REVIEW"),
        "Violations": _pascal_case_violations(state.get("violations") or []),
    }
