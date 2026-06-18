from typing import Any, Literal
from typing_extensions import TypedDict


class CallState(TypedDict, total=False):
    """Graph state that flows through all pipeline nodes."""

    # Input fields
    call_id: str | None
    audio_link: str        # URL to download audio

    # Internal
    audio_bytes: bytes
    audio_format: str
    conversation_id: str

    # Node: Transcription output
    transcript: str
    transcript_turns: list[dict[str, str]]

    # Node: Classification & Resolution output
    case_type: str
    resolved: Literal["YES", "NO", "REVIEW"]

    # Node: Negative Detection output
    is_negative: Literal["TRUE", "FALSE", "REVIEW"]
    negative_reason_code: list[str]
    negative_reason_description: list[str]

    # Node: QA Scoring output
    criteria_scores: dict[str, float]
    total_score: float
    violations: list[dict[str, Any]]

    # Node: Summarization output
    summary: str

    # Merge output — CRM PascalCase fields
    ConversationId: str
    Transcript: list[dict[str, str]]
    Summary: str
    IsNegative: str
    NegativeReasonCode: list[str]
    NegativeReasonDescription: list[str]
    CriteriaScores: dict[str, float]
    CaseType: str
    Resolved: str
    Violations: list[dict[str, Any]]
