import asyncio
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.models import ReferenceDrawing, SubmissionBatch
from app.services.evaluation import evaluate_submission


async def process_batch(batch_id: int) -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _process_batch_sync, batch_id)


def _process_batch_sync(batch_id: int) -> None:
    db: Session = SessionLocal()
    try:
        batch = db.get(SubmissionBatch, batch_id)
        if not batch:
            return
        batch.status = "processing"
        db.commit()

        reference = db.get(ReferenceDrawing, batch.reference_id)
        if not reference or not reference.features_json:
            batch.status = "failed"
            batch.summary_json = {"error": "Reference drawing is missing extracted features."}
            db.commit()
            return

        rows = []
        for submission in batch.submissions:
            submission.status = "processing"
            db.commit()
            try:
                result = evaluate_submission(
                    reference.features_json,
                    Path(submission.file_path),
                    batch.drawing_type,
                    f"submission_{submission.id}.png",
                )
                submission.score = result["score"]
                submission.feedback_text = result["feedback_text"]
                submission.preview_path = str(result["feedback_image_path"])
                submission.result_json = result["result_json"]
                submission.status = "completed"
                submission.processed_at = datetime.utcnow()
                rows.append(
                    {
                        "student_id": submission.student_id,
                        "marks": submission.score,
                        "feedback": submission.feedback_text,
                    }
                )
            except Exception as exc:
                submission.status = "failed"
                submission.feedback_text = f"Processing failed: {exc}"
            batch.processed_files += 1
            db.commit()

        export_path = settings.storage_dir / "exports" / f"batch_{batch.id}.xlsx"
        csv_path = settings.storage_dir / "exports" / f"batch_{batch.id}.csv"
        export_path.parent.mkdir(parents=True, exist_ok=True)
        dataframe = pd.DataFrame(rows)
        dataframe.to_excel(export_path, index=False)
        dataframe.to_csv(csv_path, index=False)
        batch.status = "completed"
        batch.completed_at = datetime.utcnow()
        batch.summary_json = build_batch_summary(batch, export_path, csv_path)
        db.commit()
    finally:
        db.close()


def build_batch_summary(batch: SubmissionBatch, export_path: Path, csv_path: Path) -> dict:
    completed = [submission for submission in batch.submissions if submission.score is not None]
    scores = [submission.score for submission in completed]
    return {
        "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
        "highest_score": max(scores) if scores else 0,
        "lowest_score": min(scores) if scores else 0,
        "completed": len(completed),
        "failed": len([submission for submission in batch.submissions if submission.status == "failed"]),
        "export_path": f"/static/{export_path.relative_to(settings.storage_dir).as_posix()}",
        "csv_export_path": f"/static/{csv_path.relative_to(settings.storage_dir).as_posix()}",
    }
