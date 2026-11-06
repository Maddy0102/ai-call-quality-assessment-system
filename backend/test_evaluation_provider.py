
from app.services.evaluation_provider import (
    UnavailableEvaluationProvider
)

provider = UnavailableEvaluationProvider()

result = provider.evaluate_question(
    question="Did the executive ask about the customer's budget?",
    expected_behavior="Executive asks about the customer's budget.",
    transcript_segments=[]
)

print("\n========== EVALUATION PROVIDER TEST ==========")

print("Status:", result["status"])
print("Explanation:", result["explanation"])
print("Review required:", result["review_required"])
print("Review reason:", result["review_reason"])

assert result["status"] == "NOT_CLEAR"
assert result["review_required"] is True

print("\nTEST PASSED")
