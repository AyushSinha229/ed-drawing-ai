from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="professor")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ReferenceDrawing(Base):
    __tablename__ = "reference_drawings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    drawing_type: Mapped[str] = mapped_column(String(50), default="orthographic")
    original_filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(Text)
    preview_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    features_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    batches: Mapped[list["SubmissionBatch"]] = relationship(back_populates="reference")


class SubmissionBatch(Base):
    __tablename__ = "submission_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reference_id: Mapped[int] = mapped_column(ForeignKey("reference_drawings.id"))
    drawing_type: Mapped[str] = mapped_column(String(50), default="orthographic")
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    processed_files: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="uploaded")
    summary_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    reference: Mapped["ReferenceDrawing"] = relationship(back_populates="batches")
    submissions: Mapped[list["StudentSubmission"]] = relationship(back_populates="batch")


class StudentSubmission(Base):
    __tablename__ = "student_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("submission_batches.id"))
    student_id: Mapped[str] = mapped_column(String(100), index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(Text)
    preview_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="uploaded")
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    batch: Mapped["SubmissionBatch"] = relationship(back_populates="submissions")

