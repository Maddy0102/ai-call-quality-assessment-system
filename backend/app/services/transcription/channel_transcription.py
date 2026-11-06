import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from app.services.transcription.reliability import (
    assess_transcription_reliability,
)

from app.services.transcription.silence_detection import detect_silence


BACKEND_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BACKEND_DIR / ".env")

MODEL_NAME = "gpt-transcribe"

# ISO-639-1 language hints. The transcript remains in its spoken language.
LANGUAGES = ["ta", "kn", "en"]


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing from backend .env")

    return OpenAI(api_key=api_key)


def get_audio_duration(audio_path):
    """Get audio duration locally using FFprobe."""

    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return float(result.stdout.strip())


def transcribe_channel(audio_path, speaker, channel):
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    file_size = os.path.getsize(audio_path)

    if file_size > 25 * 1024 * 1024:
        raise ValueError(
            f"{speaker} audio exceeds OpenAI's 25 MB upload limit."
        )

    # Local processing only; no additional API call.
    audio_duration = get_audio_duration(audio_path)
    silence_intervals = detect_silence(audio_path)

    client = get_openai_client()

    # GPT-Transcribe: one transcription request per speaker channel.
    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            file=audio_file,
            model=MODEL_NAME,
            languages=LANGUAGES,
        )

    transcript_text = (response.text or "").strip()

    detected_languages = getattr(response, "languages", None) or []
    language_codes = []

    for language in detected_languages:
        code = getattr(language, "code", None)

        if code:
            language_codes.append(code)

    # GPT-Transcribe does not provide Whisper-style segment timestamps.
    # Preserve the complete channel transcript without inventing timings.
    segments = []

    if transcript_text:
        segments.append({
            "speaker": speaker,
            "channel": channel,
            "start": None,
            "end": None,
            "text": transcript_text,
            "avg_logprob": None,
            "no_speech_prob": None,
            "timestamp_source": None,
        })

    return {
        "language": language_codes[0] if language_codes else None,
        "languages": language_codes,
        "duration": audio_duration,
        "silence_intervals": silence_intervals,
        "segments": segments,
    }


def transcribe_call(left_audio_path, right_audio_path):
    executive = transcribe_channel(
        left_audio_path,
        speaker="EXECUTIVE",
        channel="left",
    )

    customer = transcribe_channel(
        right_audio_path,
        speaker="CUSTOMER",
        channel="right",
    )

    combined_segments = (
        executive["segments"] + customer["segments"]
    )

    # Both channel transcripts currently have unavailable timestamps.
    # Preserve channel order rather than pretending to know exact timing.

    audio_duration = max(
        executive["duration"],
        customer["duration"],
    )

    reliability = assess_transcription_reliability(
        combined_segments,
        audio_duration=audio_duration,
    )

    return {
        "model": MODEL_NAME,
        "provider": "OpenAI",
        "executive_language": executive["language"],
        "customer_language": customer["language"],
        "executive_languages": executive["languages"],
        "customer_languages": customer["languages"],
        "audio_duration": audio_duration,
        "timestamp_status": "unavailable",
        "reliability_summary": {
            "total_segments": reliability["total_segments"],
            "reliable_segments": reliability["reliable_segments"],
            "needs_review_segments": reliability["needs_review_segments"],
            "uncertain_segments": reliability["uncertain_segments"],
        },
        "segments": reliability["segments"],
    }
