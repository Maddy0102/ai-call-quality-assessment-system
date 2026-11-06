from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.connection import check_database_connection
from app.api.routes.audio import router as audio_router
from app.api.routes.transcription import router as transcription_router
from app.api.routes.evaluation import router as evaluation_router
from app.api.routes.reports import router as reports_router
from app.api.routes.calls import router as calls_router

app = FastAPI(
    title="AI Call Quality Assessment System",
    description="Multilingual Audio Transcription and AI-Based Call Evaluation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(audio_router)
app.include_router(transcription_router)
app.include_router(evaluation_router)
app.include_router(reports_router)
app.include_router(calls_router)


@app.get("/")
def root():
    return {
        "success": True,
        "message": "AI Call Quality API is running"
    }


@app.get("/api/health")
def health_check():

    try:
        check_database_connection()

        return {
            "success": True,
            "api": "running",
            "database": "connected",
            "database_name": "call_quality_db"
        }

    except Exception as error:

        return {
            "success": False,
            "api": "running",
            "database": "disconnected",
            "error": str(error)
        }
