from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.core.storage import public_path
from app.db import get_db
from app.models import SubmissionBatch
from app.schemas import BatchResponse, ResultListResponse


router = APIRouter()


@router.get("/results", response_model=ResultListResponse)
async def list_results(db: Session = Depends(get_db)):
    batches = (
        db.query(SubmissionBatch)
        .options(selectinload(SubmissionBatch.submissions))
        .order_by(SubmissionBatch.created_at.desc())
        .all()
    )
    for batch in batches:
        hydrate_batch(batch)
    return ResultListResponse(batches=batches)


@router.get("/results/{batch_id}", response_model=BatchResponse)
async def get_batch_results(batch_id: int, db: Session = Depends(get_db)):
    batch = (
        db.query(SubmissionBatch)
        .options(selectinload(SubmissionBatch.submissions))
        .filter(SubmissionBatch.id == batch_id)
        .first()
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found.")
    hydrate_batch(batch)
    return batch


def hydrate_batch(batch: SubmissionBatch) -> None:
    for submission in batch.submissions:
        submission.preview_path = public_path(Path(submission.preview_path)) if submission.preview_path else None

