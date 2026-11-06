from bson import ObjectId
from fastapi import APIRouter, HTTPException

from app.database.connection import get_database

router = APIRouter(
    prefix="/api/calls",
    tags=["Call History"],
)


def serialize_call(record):
    evaluation = record.get("evaluation") or {}
    evaluation_results = evaluation.get("results") or []

    human_review_count = sum(
        1
        for item in evaluation_results
        if item.get("review_required", False)
        or item.get("status") == "NOT_CLEAR"
    )
    return {
        "call_id": str(record["_id"]),
        "filename": record.get("original_filename"),
        "file_size": record.get("file_size"),
        "file_format": record.get("file_format"),
        "created_at": record.get("created_at"),
        "status": record.get("status", "uploaded"),
        "transcription_status": record.get(
            "transcription_status", "pending"
        ),
        "evaluation_status": record.get(
            "evaluation_status", "pending"
        ),
        "evaluation_summary": {
            "yes_count": evaluation.get("yes_count", 0),
            "no_count": evaluation.get("no_count", 0),
            "partial_count": evaluation.get("partial_count", 0),
            "not_clear_count": evaluation.get("not_clear_count", 0),
            "human_review_count": human_review_count,
            "compliance_percentage": evaluation.get(
                "compliance_percentage"
            ),
        },
    }


@router.get("")
def get_calls():
    calls = get_database()["calls"]

    records = calls.find(
        {},
        {
            "original_filename": 1,
            "file_size": 1,
            "file_format": 1,
            "created_at": 1,
            "status": 1,
            "transcription_status": 1,
            "evaluation_status": 1,
            "evaluation": 1,
        },
    ).sort("created_at", -1)

    return {
        "success": True,
        "data": [serialize_call(record) for record in records],
    }


@router.get("/{call_id}")
def get_call_details(call_id: str):
    if not ObjectId.is_valid(call_id):
        raise HTTPException(status_code=400, detail="Invalid call ID")

    record = get_database()["calls"].find_one(
        {"_id": ObjectId(call_id)}
    )

    if not record:
        raise HTTPException(status_code=404, detail="Call not found")

    return {
        "success": True,
        "data": serialize_call(record),
    }
