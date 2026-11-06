import os
import uuid

from pathlib import Path
from fastapi import UploadFile

UPLOAD_DIR = Path("uploads")

MAX_FILE_SIZE = 100 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a"
}


def validate_audio_header(header: bytes, extension: str) -> bool:

    if extension == ".mp3":
        return (
            header.startswith(b"ID3")
            or (
                len(header) >= 2
                and header[0] == 0xFF
                and (header[1] & 0xE0) == 0xE0
            )
        )

    if extension == ".wav":
        return (
            len(header) >= 12
            and header[:4] == b"RIFF"
            and header[8:12] == b"WAVE"
        )

    if extension == ".m4a":
        return len(header) >= 8 and header[4:8] == b"ftyp"

    return False


async def save_audio_file(file: UploadFile):

    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Unsupported format. Only MP3, WAV and M4A are allowed."
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    unique_filename = f"{uuid.uuid4()}{extension}"

    file_path = UPLOAD_DIR / unique_filename

    total_size = 0
    first_chunk = True

    try:
        with open(file_path, "wb") as audio_file:

            while True:

                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise ValueError(
                        "Audio file exceeds the 100 MB limit."
                    )

                if first_chunk:
                    if not validate_audio_header(chunk[:16], extension):
                        raise ValueError(
                            "The uploaded file does not contain a valid audio header."
                        )

                    first_chunk = False

                audio_file.write(chunk)

        if total_size == 0:
            raise ValueError("Uploaded audio file is empty.")

        return {
            "filename": unique_filename,
            "original_filename": file.filename,
            "file_path": str(file_path),
            "file_size": total_size,
            "file_format": extension.replace(".", "").upper()
        }

    except Exception:
        if file_path.exists():
            os.remove(file_path)

        raise

    finally:
        await file.close()
