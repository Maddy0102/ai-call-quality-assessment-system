
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ChecklistStatus(str, Enum):
    YES = "YES"
    NO = "NO"
    PARTIAL = "PARTIAL"
    NOT_CLEAR = "NOT_CLEAR"


class Evidence(BaseModel):
    speaker: str
    start: Optional[float] = None
    end: Optional[float] = None
    text: str


class QuestionEvaluation(BaseModel):
    question_id: str
    question: str
    category: str
    status: ChecklistStatus

    explanation: str

    evidence: list[Evidence] = Field(default_factory=list)

    review_required: bool = False
    review_reason: Optional[str] = None

    weight: int = 0


class ChecklistEvaluation(BaseModel):
    checklist_id: str
    checklist_name: str

    total_questions: int

    yes_count: int = 0
    no_count: int = 0
    partial_count: int = 0
    not_clear_count: int = 0

    compliance_percentage: Optional[float] = None

    results: list[QuestionEvaluation] = Field(
        default_factory=list
    )
