from bson import ObjectId
from fastapi import APIRouter, HTTPException

from app.database.connection import get_database
from app.services.report_service import build_call_report

router = APIRouter(
    prefix="/api/reports",
    tags=["Call Reports"],
)


@router.get("/{call_id}")
def get_call_report(call_id: str):
    if not ObjectId.is_valid(call_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid call ID",
        )

    record = get_database()["calls"].find_one(
        {"_id": ObjectId(call_id)}
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Call record not found",
        )

    try:
        report = build_call_report(record)

        return {
            "success": True,
            "data": report,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not generate call report: {str(error)}",
        )
