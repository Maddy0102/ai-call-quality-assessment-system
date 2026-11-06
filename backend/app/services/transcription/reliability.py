import re
from collections import Counter


PROMPT_TEXT = (
    "the conversation may contain tamil kannada english "
    "or mixed tamil english and kannada english speech"
)


def normalize_text(text):
    text = (text or "").lower()

    # Preserve Tamil, Kannada and other Unicode letters.
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)

    return re.sub(r"\s+", " ", text).strip()


def assess_segment_reliability(
    segment,
    audio_duration=None,
    repeated_text=False,
):
    """
    Assess available transcription quality indicators.

    Missing timestamps or confidence metadata are not treated
    as evidence of transcription errors.
    """

    text = (segment.get("text") or "").strip()
    normalized = normalize_text(text)

    avg_logprob = segment.get("avg_logprob")
    no_speech_prob = segment.get("no_speech_prob")

    start = segment.get("start")
    end = segment.get("end")

    reasons = []

    if not text:
        return {
            "status": "uncertain",
            "reasons": ["Empty transcription"],
            "timestamp_available": False,
            "confidence_metadata_available": False,
        }

    # Validate timestamps only when both are available.
    if start is not None and end is not None:
        if start < 0 or end <= start:
            reasons.append("Invalid timestamps")

        elif audio_duration is not None:
            if start >= audio_duration or end > audio_duration + 0.5:
                reasons.append("Timestamp exceeds audio duration")

    # Detect possible prompt contamination.
    if normalized == normalize_text(PROMPT_TEXT):
        reasons.append(
            "Possible transcription prompt returned as speech"
        )

    if repeated_text:
        reasons.append(
            "Repeated identical text across multiple segments"
        )

    if segment.get("overlaps_silence"):
        reasons.append("Segment overlaps detected silence")

    if segment.get("mostly_silence"):
        reasons.append("Segment is mostly within detected silence")

    # Evaluate confidence only when both values are supplied.
    if avg_logprob is not None and no_speech_prob is not None:
        if no_speech_prob >= 0.6:
            reasons.append("High probability of no speech")

        if avg_logprob < -1.0:
            reasons.append("Very low average log probability")
        elif avg_logprob < -0.5:
            reasons.append("Low average log probability")

    critical_reasons = {
        "Invalid timestamps",
        "Timestamp exceeds audio duration",
        "Possible transcription prompt returned as speech",
        "Repeated identical text across multiple segments",
        "Segment is mostly within detected silence",
    }

    if (
        any(reason in critical_reasons for reason in reasons)
        or (no_speech_prob is not None and no_speech_prob >= 0.8)
        or (avg_logprob is not None and avg_logprob < -1.0)
    ):
        status = "uncertain"
    elif reasons:
        status = "needs_review"
    else:
        status = "reliable"

    return {
        "status": status,
        "reasons": reasons,
        "timestamp_available": start is not None and end is not None,
        "confidence_metadata_available": (
            avg_logprob is not None and no_speech_prob is not None
        ),
    }


def assess_transcription_reliability(
    segments,
    audio_duration=None,
):
    """
    Assess all segments, including repeated-text patterns.
    Original segment text and timestamps are preserved.
    """

    text_counts = Counter(
        (
            segment.get("speaker"),
            normalize_text(segment.get("text")),
        )
        for segment in segments
        if normalize_text(segment.get("text"))
    )

    reliable = 0
    needs_review = 0
    uncertain = 0

    assessed_segments = []

    for segment in segments:
        key = (
            segment.get("speaker"),
            normalize_text(segment.get("text")),
        )

        repeated_text = text_counts[key] >= 5

        assessment = assess_segment_reliability(
            segment,
            audio_duration=audio_duration,
            repeated_text=repeated_text,
        )

        updated_segment = {
            **segment,
            "reliability": assessment,
        }

        assessed_segments.append(updated_segment)

        if assessment["status"] == "reliable":
            reliable += 1
        elif assessment["status"] == "needs_review":
            needs_review += 1
        else:
            uncertain += 1

    return {
        "total_segments": len(segments),
        "reliable_segments": reliable,
        "needs_review_segments": needs_review,
        "uncertain_segments": uncertain,
        "segments": assessed_segments,
    }
