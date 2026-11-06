
from pathlib import Path
import json
import subprocess

from app.services.transcription.reliability import (
    assess_transcription_reliability,
)
from app.services.voice_quality import analyze_call_voice_quality


def get_audio_duration(audio_path):
    """Read audio duration locally using FFprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                str(audio_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        metadata = json.loads(result.stdout)
        return float(metadata["format"]["duration"])

    except (subprocess.SubprocessError, ValueError, KeyError, json.JSONDecodeError):
        return None


def build_call_report(record):
    """
    Build a consolidated call report.

    Read-only:
    - Does not update MongoDB.
    - Does not call OpenAI.
    - Does not modify the original transcript.
    """

    transcription = record.get("transcription") or {}
    segments = transcription.get("segments") or []

    if not segments:
        raise ValueError("No transcript segments are available")

    audio_path = record.get("file_path")
    if not audio_path:
        raise ValueError("Original audio path is missing")

    audio_path = Path(audio_path)

    if not audio_path.is_file():
        raise FileNotFoundError("Original audio file is unavailable")

    duration = transcription.get("audio_duration")

    if duration is None:
        duration = get_audio_duration(audio_path)

    reliability = assess_transcription_reliability(
        segments,
        audio_duration=duration,
    )

    call_id = str(record.get("_id"))
    processed_dir = Path("uploads/processed") / call_id

    executive_audio = processed_dir / "left_16k.wav"
    customer_audio = processed_dir / "right_16k.wav"

    voice_quality = None
    voice_quality_error = None

    if executive_audio.is_file() and customer_audio.is_file():
        try:
            voice_quality = analyze_call_voice_quality(
                str(executive_audio),
                str(customer_audio),
            )
        except Exception as error:
            voice_quality_error = str(error)
    else:
        voice_quality_error = "Processed speaker audio files are unavailable"

    evaluation = record.get("evaluation") or {}
    evaluation_status = record.get("evaluation_status", "pending")

    evaluation_results = evaluation.get("results", [])

    evaluation_review_required = any(
        item.get("review_required", False)
        for item in evaluation_results
    )

    review_required = (
        reliability["uncertain_segments"] > 0
        or reliability["needs_review_segments"] > 0
        or evaluation_status != "completed"
        or evaluation_review_required
        or voice_quality is None
    )

    return {
        "call_id": call_id,
        "filename": record.get("original_filename"),
        "created_at": record.get("created_at"),
        "report_status": (
            "review_required" if review_required else "ready"
        ),
        "transcription_status": record.get(
            "transcription_status", "unknown"
        ),
        "timestamp_status": transcription.get(
            "timestamp_status", "available"
        ),
        "transcription_summary": {
            "total_segments": reliability["total_segments"],
            "reliable_segments": reliability["reliable_segments"],
            "needs_review_segments": reliability["needs_review_segments"],
            "uncertain_segments": reliability["uncertain_segments"],
            "audio_duration_seconds": duration,
        },
        "transcription_segments": reliability["segments"],
        "voice_quality": voice_quality,
        "voice_quality_error": voice_quality_error,
        "evaluation_status": evaluation_status,
        "checklist_evaluation": evaluation,
        "review_required": review_required,
        "review_reasons": [
            reason
            for condition, reason in [
                (
                    reliability["uncertain_segments"] > 0,
                    "Some transcript segments are uncertain.",
                ),
                (
                    reliability["needs_review_segments"] > 0,
                    "Some transcript segments need review.",
                ),
                (
                    evaluation_status != "completed",
                    "Checklist evaluation has not been completed.",
                ),
                (
                    evaluation_review_required,
                    "One or more checklist questions require manual review.",
                ),
                (
                    voice_quality is None,
                    "Voice-quality measurements are unavailable.",
                ),
            ]
            if condition
        ],
        "limitations": [
            "Transcript reliability flags are indicators, not proof of transcription errors.",
            "Speaker-channel silence is measured independently.",
            "Local audio measurements do not establish pronunciation accuracy, confidence, or professionalism.",
            "No final overall performance score is assigned by this report.",
        ],
    }
