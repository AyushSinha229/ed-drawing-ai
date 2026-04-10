import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings


def ensure_storage() -> None:
    for name in ["references", "students", "exports", "visual_feedback"]:
        (settings.storage_dir / name).mkdir(parents=True, exist_ok=True)


def save_upload(upload: UploadFile, category: str) -> Path:
    ensure_storage()
    suffix = Path(upload.filename or "").suffix.lower()
    file_path = settings.storage_dir / category / f"{uuid.uuid4().hex}{suffix}"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)
    return file_path


def public_path(file_path: Path | None) -> str | None:
    if not file_path:
        return None
    return f"/static/{file_path.relative_to(settings.storage_dir).as_posix()}"

