
from abc import ABC, abstractmethod


class EvaluationProvider(ABC):
    """
    Base interface for checklist evaluation providers.
    """

    @abstractmethod
    def evaluate_question(
        self,
        question,
        expected_behavior,
        transcript_segments
    ):
        """
        Evaluate one checklist question against transcript evidence.

        The provider must return:
        - status
        - explanation
        - evidence
        - review_required
        - review_reason
        """
        pass


class UnavailableEvaluationProvider(EvaluationProvider):
    """
    Safe fallback when no AI provider is configured.

    Never invent checklist decisions.
    """

    def evaluate_question(
        self,
        question,
        expected_behavior,
        transcript_segments
    ):
        return {
            "status": "NOT_CLEAR",
            "explanation": (
                "No AI evaluation provider is configured. "
                "Manual review is required."
            ),
            "evidence": [],
            "review_required": True,
            "review_reason": "AI evaluation provider unavailable"
        }
