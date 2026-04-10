import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session, selectinload

from app.core.storage import public_path, save_upload
from app.db import get_db
from app.models import ReferenceDrawing, StudentSubmission, SubmissionBatch
from app.schemas import BatchResponse, JobResponse, ProcessRequest, ReferenceResponse
from app.services.evaluation import build_reference_features
from app.services.jobs import process_batch


router = APIRouter()


@router.post("/upload-reference", response_model=ReferenceResponse)
async def upload_reference(
    file: UploadFile = File(...),
    name: str = Form(...),
    drawing_type: str = Form("orthographic"),
    db: Session = Depends(get_db),
):
    file_path = save_upload(file, "references")
    features, _ = build_reference_features(file_path)
    reference = ReferenceDrawing(
        name=name,
        drawing_type=drawing_type,
        original_filename=file.filename or file_path.name,
        file_path=str(file_path),
        preview_path=str(file_path),
        features_json=features,
    )
    db.add(reference)
    db.commit()
    db.refresh(reference)
    reference.preview_path = public_path(Path(reference.preview_path))
    return reference


@router.post("/upload-students", response_model=BatchResponse)
async def upload_students(
    reference_id: int = Form(...),
    drawing_type: str = Form("orthographic"),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    reference = db.get(ReferenceDrawing, reference_id)
    if not reference:
        raise HTTPException(status_code=404, detail="Reference drawing not found.")

    batch = SubmissionBatch(reference_id=reference_id, drawing_type=drawing_type, total_files=len(files), status="uploaded")
    db.add(batch)
    db.commit()
    db.refresh(batch)

    for index, file in enumerate(files, start=1):
        file_path = save_upload(file, "students")
        student_id = infer_student_id(file.filename or "", index)
        submission = StudentSubmission(
            batch_id=batch.id,
            student_id=student_id,
            original_filename=file.filename or file_path.name,
            file_path=str(file_path),
            preview_path=str(file_path),
        )
        db.add(submission)
    db.commit()

    batch = (
        db.query(SubmissionBatch)
        .options(selectinload(SubmissionBatch.submissions))
        .filter(SubmissionBatch.id == batch.id)
        .one()
    )
    hydrate_batch_paths(batch)
    return batch


@router.post("/process", response_model=JobResponse)
async def process_submissions(payload: ProcessRequest, db: Session = Depends(get_db)):
    batch = db.get(SubmissionBatch, payload.batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found.")
    if batch.status == "processing":
        raise HTTPException(status_code=409, detail="Batch is already processing.")
    asyncio.create_task(process_batch(batch.id))
    batch.status = "queued"
    db.commit()
    return JobResponse(batch_id=batch.id, status=batch.status, processed_files=batch.processed_files, total_files=batch.total_files)


def infer_student_id(filename: str, index: int) -> str:
    stem = Path(filename).stem.strip()
    return stem if stem else f"student_{index:03d}"


def hydrate_batch_paths(batch: SubmissionBatch) -> None:
    for submission in batch.submissions:
        submission.preview_path = public_path(Path(submission.preview_path)) if submission.preview_path else None

