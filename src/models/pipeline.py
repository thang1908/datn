from typing import List, Literal

from pydantic import BaseModel, Field


class ClassificationResolvedOutput(BaseModel):
    case_type: str
    resolved: Literal["YES", "NO", "REVIEW"]


class TranscriptTurn(BaseModel):
    speaker: Literal["agent", "customer"]
    text: str


class TranscribeOutput(BaseModel):
    transcript: List[TranscriptTurn] = Field(default_factory=list)


class NegativeDetectionOutput(BaseModel):
    is_negative: Literal["TRUE", "FALSE", "REVIEW"] = "REVIEW"
    negative_reason_code: List[
        Literal[
            "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "A1", "A2", "A3", "A4"
        ]
    ] = Field(default_factory=list)
    negative_reason_description: List[str] = Field(default_factory=list)


class SummaryOutput(BaseModel):
    summary: str = ""


class CriteriaScores(BaseModel):
    communication: float = 0
    attitude: float = 0
    data_collection: float = 0
    problem_solving: float = 0


class ViolationEvidence(BaseModel):
    speaker: Literal["agent", "customer"]
    text: str


class ViolationItem(BaseModel):
    criterion_id: Literal[
        "communication", "attitude", "data_collection", "problem_solving"
    ]
    violation_code: str
    description: str
    deduction: float
    evidence: List[ViolationEvidence] = Field(default_factory=list)


class QAScoringOutput(BaseModel):
    criteria_scores: CriteriaScores = Field(default_factory=CriteriaScores)
    total_score: float = 0
    violations: List[ViolationItem] = Field(default_factory=list)
