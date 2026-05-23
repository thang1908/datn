from typing import List, Optional

from pydantic import BaseModel, Field


class CallRequest(BaseModel):
    """Request model for call analysis pipeline."""

    CallId: str = Field(..., description="Call ID")
    AudioLink: str = Field(..., description="URL to audio file (wav/mp3/m4a/flac)")
    Direction: Optional[int] = Field(1, description="1 = inbound, 2 = outbound")


class CRMViolationEvidence(BaseModel):
    Speaker: str
    Text: str


class CRMViolationItem(BaseModel):
    CriterionId: str
    ViolationCode: str
    Description: str
    Deduction: float
    Evidence: List[CRMViolationEvidence] = Field(default_factory=list)


class CRMCriteriaScores(BaseModel):
    Communication: float = 0
    Attitude: float = 0
    DataCollection: float = 0
    ProblemSolving: float = 0


class CRMTranscriptTurn(BaseModel):
    Speaker: str
    Text: str


class CallAnalysisResult(BaseModel):
    """Analysis result returned from the pipeline."""

    ConversationId: str
    ChannelType: str
    Transcript: List[CRMTranscriptTurn] = Field(default_factory=list)
    Summary: str = ""
    IsNegative: str = "REVIEW"
    NegativeReasonCode: List[str] = Field(default_factory=list)
    NegativeReasonDescription: List[str] = Field(default_factory=list)
    CriteriaScores: CRMCriteriaScores = Field(default_factory=CRMCriteriaScores)
    CaseType: str = ""
    Resolved: str = "REVIEW"
    Violations: List[CRMViolationItem] = Field(default_factory=list)


# Keep backward-compatible aliases
CRMKafkaMessage = CallRequest
CRMOutputMessage = CallAnalysisResult
