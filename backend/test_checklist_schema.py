
from app.schemas.checklist import (
    ChecklistStatus,
    QuestionEvaluation,
    Evidence
)

sample = QuestionEvaluation(
    question_id="Q004",
    question="Did the executive ask about the customer's budget?",
    category="Customer Requirement Analysis",
    status=ChecklistStatus.YES,
    explanation="The executive asked about the customer's budget.",
    evidence=[
        Evidence(
            speaker="EXECUTIVE",
            start=25.5,
            end=29.2,
            text="What is your budget?"
        )
    ],
    review_required=False,
    weight=10
)

print("\n========== CHECKLIST SCHEMA TEST ==========")
print(sample.model_dump())
print("\nStatus:", sample.status.value)
print("Evidence count:", len(sample.evidence))
print("\nTEST COMPLETED")
