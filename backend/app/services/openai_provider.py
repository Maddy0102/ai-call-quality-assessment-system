import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from app.services.evaluation_provider import EvaluationProvider


# Load backend/.env
BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

ALLOWED_STATUSES = {"YES", "NO", "PARTIAL", "NOT_CLEAR"}


class OpenAIEvaluationProvider(EvaluationProvider):

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing")

        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv(
            "OPENAI_EVALUATION_MODEL",
            "gpt-4o-mini"
        )

    def evaluate_question(
        self,
        question,
        expected_behavior,
        transcript_segments
    ):

        executive_segments = [
            segment
            for segment in transcript_segments
            if segment.get("speaker") == "EXECUTIVE"
            and (segment.get("text") or "").strip()
        ]

        if not executive_segments:
            return {
                "status": "NOT_CLEAR",
                "explanation": (
                    "Executive transcript is unavailable. "
                    "The checklist cannot be evaluated reliably."
                ),
                "evidence": [],
                "review_required": True,
                "review_reason": "Executive transcript is missing.",
            }

        conversation = []

        for segment in transcript_segments:
            reliability = segment.get("reliability") or {}

            conversation.append({
                "speaker": segment.get("speaker"),
                "start": segment.get("start"),
                "end": segment.get("end"),
                "text": segment.get("text"),
                "reliability": reliability.get("status", "unknown")
            })

        prompt = f"""
You are a professional multilingual call quality auditor.

Evaluate ONE checklist question independently.

CHECKLIST QUESTION:
{question}

EXPECTED BEHAVIOR:
{expected_behavior}

CONVERSATION:
{json.dumps(conversation, ensure_ascii=False)}

STRICT RULES:

1. Evaluate EXECUTIVE actions, not customer actions.
2. Understand Tamil, Kannada, English and mixed languages.
3. Evaluate meaning and conversational context, not keywords.
4. Never invent statements, evidence or timestamps.
5. Use only the supplied transcript.
6. YES means the complete expected behavior was fulfilled.
7. PARTIAL means some expected behavior was fulfilled.
8. NO means sufficient reliable evidence establishes non-compliance.
9. NOT_CLEAR means there is insufficient reliable evidence.
10. Missing transcript content alone does not prove non-compliance.
11. Evidence must be copied exactly from the transcript.
12. Preserve the original speaker.
13. YES and PARTIAL require executive evidence.
14. Every NO or PARTIAL must explain the reason.
15. Mark review_required when evidence is uncertain.
16. Timestamps are unavailable for this transcript. Never generate or estimate timestamps.
17. Evidence must identify the original speaker and exact transcript text.
18. A NO result requires exact executive evidence supporting non-compliance.
19. Do not mark NO merely because a required statement is absent from the transcript.

Return valid JSON only:

{{
    "status": "YES",
    "explanation": "Reason for the decision",
    "evidence": [
        {{
            "speaker": "EXECUTIVE",
            "text": "Exact transcript excerpt"
        }}
    ],
    "review_required": false,
    "review_reason": null
}}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict, fair and evidence-based "
                        "multilingual call quality auditor. "
                        "Never fabricate evidence."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError("OpenAI returned an empty response")

        result = json.loads(content)

        status = result.get("status")

        if status not in ALLOWED_STATUSES:
            raise ValueError(f"Invalid evaluation status: {status}")

        evidence = result.get("evidence", [])

        if not isinstance(evidence, list):
            raise ValueError("Evidence must be a list")

        # Validate every evidence excerpt against the original transcript.
        validated_evidence = []

        for item in evidence:
            if not isinstance(item, dict):
                continue

            item_text = item.get("text")
            item_speaker = item.get("speaker")

            if not isinstance(item_text, str):
                continue

            item_text = item_text.strip()

            if not item_text:
                continue

            for segment in transcript_segments:
                original_text = segment.get("text") or ""

                if segment.get("speaker") != item_speaker:
                    continue

                if item_text in original_text:
                    validated_evidence.append({
                        "speaker": segment["speaker"],
                        "start": segment.get("start"),
                        "end": segment.get("end"),
                        "text": item_text
                    })
                    break

        review_required = bool(
            result.get("review_required", False)
        )

        review_reason = result.get("review_reason")
        explanation = result.get("explanation", "")

        # Require verified executive evidence for every scored decision.
        executive_evidence = [
            item for item in validated_evidence
            if item["speaker"] == "EXECUTIVE"
        ]

        if status in {"YES", "PARTIAL", "NO"} and not executive_evidence:
            status = "NOT_CLEAR"
            review_required = True

            explanation = (
                "The model response could not be verified against "
                "the original executive transcript. Human review is required."
            )

            review_reason = (
                "No verifiable executive evidence found "
                "to support the evaluation."
            )

        # Unreliable executive transcript requires review.
        unreliable_executive = any(
            (segment.get("reliability") or {}).get("status")
            != "reliable"
            for segment in executive_segments
        )

        if unreliable_executive:
            review_required = True
            review_reason = (
                "Executive transcript contains segments "
                "requiring reliability review."
            )

        if status == "NOT_CLEAR":
            review_required = True

            if not review_reason:
                review_reason = (
                    "Insufficient reliable evidence for evaluation."
                )

        explanation = result.get("explanation", "")

        if status == "NOT_CLEAR" and not validated_evidence:
            explanation = (
                "Insufficient verifiable transcript evidence "
                "to make a reliable decision. Human review is required."
            )

        return {
            "status": status,
            "explanation": explanation,
            "evidence": validated_evidence,
            "review_required": review_required,
            "review_reason": review_reason
        }
