from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReferenceResponse(BaseModel):
    id: int
    name: str
    drawing_type: str
    original_filename: str
    preview_path: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class StudentSubmissionResponse(BaseModel):
    id: int
    student_id: str
    original_filename: str
    status: str
    score: float | None
    feedback_text: str | None
    preview_path: str | None
    result_json: dict[str, Any] | None

    class Config:
        from_attributes = True


class BatchResponse(BaseModel):
    id: int
    reference_id: int
    drawing_type: str
    total_files: int
    processed_files: int
    status: str
    summary_json: dict[str, Any] | None
    created_at: datetime
    completed_at: datetime | None
    submissions: list[StudentSubmissionResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ProcessRequest(BaseModel):
    batch_id: int


class JobResponse(BaseModel):
    batch_id: int
    status: str
    processed_files: int
    total_files: int


class ResultListResponse(BaseModel):
    batches: list[BatchResponse]

