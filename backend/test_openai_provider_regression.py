import json
from types import SimpleNamespace
from unittest.mock import Mock

from app.services.openai_provider import OpenAIEvaluationProvider


def create_provider(mock_result):
    provider = OpenAIEvaluationProvider.__new__(
        OpenAIEvaluationProvider
    )

    provider.model = "gpt-4o-mini"

    response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=json.dumps(mock_result)
                )
            )
        ]
    )

    provider.client = Mock()
    provider.client.chat.completions.create.return_value = response

    return provider


TRANSCRIPT = [
    {
        "speaker": "EXECUTIVE",
        "text": "Vanakkam sir, thank you for your time.",
        "start": None,
        "end": None,
        "reliability": {"status": "reliable"}
    }
]


def test_unsupported_yes_becomes_not_clear():
    provider = create_provider({
        "status": "YES",
        "explanation": "The executive confirmed the customer name.",
        "evidence": [],
        "review_required": False,
        "review_reason": None
    })

    result = provider.evaluate_question(
        "Did the executive confirm the prospect's name?",
        "Executive confirms prospect name.",
        TRANSCRIPT
    )

    assert result["status"] == "NOT_CLEAR"
    assert result["evidence"] == []
    assert result["review_required"] is True
    assert "verifiable" in result["explanation"].lower()

    print("PASS: Unsupported YES downgraded to NOT_CLEAR")


def test_unsupported_partial_becomes_not_clear():
    provider = create_provider({
        "status": "PARTIAL",
        "explanation": "The executive asked about budget preferences.",
        "evidence": [],
        "review_required": False,
        "review_reason": None
    })

    result = provider.evaluate_question(
        "Did the executive probe customer requirements?",
        "Executive asks about customer requirements.",
        TRANSCRIPT
    )

    assert result["status"] == "NOT_CLEAR"
    assert result["evidence"] == []
    assert result["review_required"] is True
    assert "verifiable" in result["explanation"].lower()

    print("PASS: Unsupported PARTIAL downgraded to NOT_CLEAR")


def test_valid_executive_evidence_is_preserved():
    provider = create_provider({
        "status": "YES",
        "explanation": "The executive greeted the customer.",
        "evidence": [
            {
                "speaker": "EXECUTIVE",
                "text": "Vanakkam sir"
            }
        ],
        "review_required": False,
        "review_reason": None
    })

    result = provider.evaluate_question(
        "Did the executive greet the customer?",
        "Executive gives a professional greeting.",
        TRANSCRIPT
    )

    assert result["status"] == "YES"
    assert len(result["evidence"]) == 1
    assert result["evidence"][0]["speaker"] == "EXECUTIVE"
    assert result["evidence"][0]["text"] == "Vanakkam sir"
    assert result["explanation"] == "The executive greeted the customer."

    print("PASS: Valid executive evidence preserved")


if __name__ == "__main__":
    test_unsupported_yes_becomes_not_clear()
    test_unsupported_partial_becomes_not_clear()
    test_valid_executive_evidence_is_preserved()

    print("\nALL REGRESSION TESTS PASSED")
