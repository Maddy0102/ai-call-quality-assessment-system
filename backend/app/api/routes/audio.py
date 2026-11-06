import os

from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.audio_service import save_audio_file
from app.database.connection import get_database

router = APIRouter(
    prefix="/api/audio",
    tags=["Audio Upload"]
)


@router.post("/upload", status_code=201)
async def upload_audio(file: UploadFile = File(...)):

    saved_audio = None

    try:

        # Step 1: Save and validate audio
        saved_audio = await save_audio_file(file)

        # Step 2: Connect to MongoDB
        database = get_database()

        database.client.admin.command("ping")

        # Step 3: Create call record
        call_record = {
            "original_filename": saved_audio["original_filename"],
            "stored_filename": saved_audio["filename"],
            "file_path": saved_audio["file_path"],
            "file_size": saved_audio["file_size"],
            "file_format": saved_audio["file_format"],
            "status": "uploaded",
            "transcription_status": "pending",
            "evaluation_status": "pending",
            "created_at": datetime.now(timezone.utc)
        }

        # Step 4: Save record in MongoDB
        result = database["calls"].insert_one(call_record)

        # Step 5: Return response
        return {
            "success": True,
            "message": "Audio uploaded successfully",
            "data": {
                "call_id": str(result.inserted_id),
                "filename": saved_audio["original_filename"],
                "stored_filename": saved_audio["filename"],
                "file_format": saved_audio["file_format"],
                "file_size": saved_audio["file_size"],
                "status": "uploaded"
            }
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        # Remove saved file if database operation fails
        if saved_audio and os.path.exists(saved_audio["file_path"]):
            os.remove(saved_audio["file_path"])

        raise HTTPException(
            status_code=500,
            detail=f"Audio upload failed: {str(error)}"
        )
