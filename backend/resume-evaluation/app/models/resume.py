from sqlmodel import SQLModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone


class Resume(SQLModel, table=True):
    id: UUID = Field(primary_key=True)
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    s3_key: str
    job_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResumeResponse(SQLModel):
    id: UUID
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    s3_key: str
    job_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
