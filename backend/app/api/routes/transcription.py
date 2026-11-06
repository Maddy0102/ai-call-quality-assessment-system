
import os
import json
import subprocess

from pathlib import Path
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.database.connection import get_database

router = APIRouter(
    prefix="/api/transcription",
    tags=["Audio Transcription"]
)


def extract_audio_channels(audio_path, call_id):
    """
    Extract left and right channels and convert them
    to 16 kHz mono WAV files.
    """

    output_dir = Path("uploads/processed") / call_id
    output_dir.mkdir(parents=True, exist_ok=True)

    left_path = output_dir / "left_16k.wav"
    right_path = output_dir / "right_16k.wav"

    # Check audio channel count
    probe = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=channels",
            "-of", "json",
            audio_path
        ],
        capture_output=True,
        text=True,
        check=True
    )

    probe_data = json.loads(probe.stdout)
    streams = probe_data.get("streams", [])

    if not streams or streams[0].get("channels", 0) < 2:
        raise ValueError(
            "Stereo audio is required for the current "
            "left/right speaker identification method."
        )

    # Extract executive channel
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", audio_path,
            "-af", "pan=mono|c0=FL",
            "-ar", "16000",
            "-ac", "1",
            str(left_path)
        ],
        capture_output=True,
        text=True,
        check=True
    )

    # Extract customer channel
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", audio_path,
            "-af", "pan=mono|c0=FR",
            "-ar", "16000",
            "-ac", "1",
            str(right_path)
        ],
        capture_output=True,
        text=True,
        check=True
    )

    return str(left_path), str(right_path)


def process_transcription(call_id):
    """
    Background task for audio transcription.
    """

    database = get_database()
    calls = database["calls"]

    try:
        record = calls.find_one({
            "_id": ObjectId(call_id)
        })

        if not record:
            raise ValueError("Call record not found")

        audio_path = record["file_path"]

        if not os.path.exists(audio_path):
            raise FileNotFoundError("Original audio file not found")

        # Extract separate speaker channels
        left_path, right_path = extract_audio_channels(
            audio_path,
            call_id
        )

        # Import here to avoid loading the AI model
        # when the FastAPI application starts.
        from app.services.transcription.channel_transcription import (
            transcribe_call
        )

        result = transcribe_call(
            left_audio_path=left_path,
            right_audio_path=right_path
        )

        # Save transcription to MongoDB
        calls.update_one(
            {"_id": ObjectId(call_id)},
            {
                "$set": {
                    "transcription_status": "completed",
                    "transcription": result,
                    "transcription_completed_at": datetime.now(
                        timezone.utc
                    )
                }
            }
        )

    except Exception as error:

        calls.update_one(
            {"_id": ObjectId(call_id)},
            {
                "$set": {
                    "transcription_status": "failed",
                    "transcription_error": str(error),
                    "transcription_failed_at": datetime.now(
                        timezone.utc
                    )
                }
            }
        )


@router.post("/{call_id}/start", status_code=202)
def start_transcription(
    call_id: str,
    background_tasks: BackgroundTasks
):

    if not ObjectId.is_valid(call_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid call ID"
        )

    database = get_database()
    calls = database["calls"]

    record = calls.find_one({
        "_id": ObjectId(call_id)
    })

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Call record not found"
        )

    # Prevent duplicate transcription requests.
    result = calls.update_one(
        {
            "_id": ObjectId(call_id),
            "transcription_status": {
                "$in": ["pending", "failed"]
            }
        },
        {
            "$set": {
                "transcription_status": "processing",
                "transcription_error": None,
                "transcription_started_at": datetime.now(
                    timezone.utc
                )
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=409,
            detail=(
                "Transcription is already processing "
                "or has already completed."
            )
        )

    background_tasks.add_task(
        process_transcription,
        call_id
    )

    return {
        "success": True,
        "message": "Transcription started",
        "data": {
            "call_id": call_id,
            "transcription_status": "processing"
        }
    }


@router.get("/{call_id}/status")
def get_transcription_status(call_id: str):

    if not ObjectId.is_valid(call_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid call ID"
        )

    database = get_database()

    record = database["calls"].find_one(
        {"_id": ObjectId(call_id)},
        {
            "transcription_status": 1,
            "transcription_error": 1
        }
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Call record not found"
        )

    return {
        "success": True,
        "data": {
            "call_id": call_id,
            "transcription_status": record.get(
                "transcription_status", "pending"
            ),
            "error": record.get("transcription_error")
        }
    }

@router.get("/{call_id}/result")
def get_transcription_result(call_id: str):

    if not ObjectId.is_valid(call_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid call ID"
        )

    database = get_database()

    record = database["calls"].find_one(
        {"_id": ObjectId(call_id)},
        {
            "original_filename": 1,
            "transcription_status": 1,
            "transcription": 1
        }
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Call record not found"
        )

    if record.get("transcription_status") != "completed":
        raise HTTPException(
            status_code=409,
            detail="Transcription is not completed yet"
        )

    return {
        "success": True,
        "data": {
            "call_id": call_id,
            "filename": record.get("original_filename"),
            "transcription": record.get("transcription")
        }
    }