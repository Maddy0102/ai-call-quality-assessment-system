
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.database.connection import get_database


router = APIRouter(
    prefix="/api/evaluation",
    tags=["Call Evaluation"]
)


def process_evaluation(call_id):
    """
    Background task to evaluate a completed call.
    """

    database = get_database()
    calls = database["calls"]

    try:
        record = calls.find_one({
            "_id": ObjectId(call_id)
        })

        if not record:
            raise ValueError("Call record not found")

        if record.get("transcription_status") != "completed":
            raise ValueError("Transcription is not completed")

        transcript = record.get("transcription", {})
        transcript_segments = transcript.get("segments", [])

        if not transcript_segments:
            raise ValueError("No transcript segments found")

        # Import evaluator only when required.
        from app.services.evaluation.checklist_evaluator import (
            ChecklistEvaluator
        )

        evaluator = ChecklistEvaluator()

        report = evaluator.evaluate(
            transcript_segments=transcript_segments,
            checklist_name="digilogy_call"
        )

        # Save evaluation report in MongoDB.
        calls.update_one(
            {"_id": ObjectId(call_id)},
            {
                "$set": {
                    "evaluation_status": "completed",
                    "evaluation": report.model_dump(),
                    "evaluation_completed_at": datetime.now(
                        timezone.utc
                    ),
                    "evaluation_error": None
                }
            }
        )

    except Exception as error:

        calls.update_one(
            {"_id": ObjectId(call_id)},
            {
                "$set": {
                    "evaluation_status": "failed",
                    "evaluation_error": str(error),
                    "evaluation_failed_at": datetime.now(
                        timezone.utc
                    )
                }
            }
        )


@router.post("/{call_id}/start", status_code=202)
def start_evaluation(
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

    if record.get("transcription_status") != "completed":
        raise HTTPException(
            status_code=409,
            detail="Complete transcription before evaluation"
        )

    # Prevent duplicate evaluation requests.
    result = calls.update_one(
        {
            "_id": ObjectId(call_id),
            "transcription_status": "completed",
            "evaluation_status": {
                "$in": ["pending", "failed"]
            }
        },
        {
            "$set": {
                "evaluation_status": "processing",
                "evaluation_error": None,
                "evaluation_started_at": datetime.now(
                    timezone.utc
                )
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=409,
            detail=(
                "Evaluation is already processing "
                "or has already completed."
            )
        )

    background_tasks.add_task(
        process_evaluation,
        call_id
    )

    return {
        "success": True,
        "message": "Call evaluation started",
        "data": {
            "call_id": call_id,
            "evaluation_status": "processing"
        }
    }


@router.get("/{call_id}/status")
def get_evaluation_status(call_id: str):

    if not ObjectId.is_valid(call_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid call ID"
        )

    database = get_database()

    record = database["calls"].find_one(
        {"_id": ObjectId(call_id)},
        {
            "evaluation_status": 1,
            "evaluation_error": 1
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
            "evaluation_status": record.get(
                "evaluation_status", "pending"
            ),
            "error": record.get("evaluation_error")
        }
    }


@router.get("/{call_id}/result")
def get_evaluation_result(call_id: str):

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
            "evaluation_status": 1,
            "evaluation": 1
        }
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Call record not found"
        )

    if record.get("evaluation_status") != "completed":
        raise HTTPException(
            status_code=409,
            detail="Evaluation is not completed yet"
        )

    return {
        "success": True,
        "data": {
            "call_id": call_id,
            "filename": record.get("original_filename"),
            "evaluation": record.get("evaluation")
        }
    }
