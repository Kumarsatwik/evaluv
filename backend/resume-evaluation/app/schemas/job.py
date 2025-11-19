from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid


class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    skills: str = Field(..., min_length=1)
    experience: str = Field(..., min_length=1)
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: str = Field(default="full-time", pattern="^(full-time|part-time|contract|internship)$")
    status: str = Field(default="active", pattern="^(active|inactive|closed)$")


class JobUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    skills: Optional[str] = Field(None, min_length=1)
    experience: Optional[str] = Field(None, min_length=1)
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = Field(None, pattern="^(full-time|part-time|contract|internship)$")
    status: Optional[str] = Field(None, pattern="^(active|inactive|closed)$")


class JobResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    skills: str
    experience: str
    location: Optional[str]
    salary_range: Optional[str]
    job_type: str
    status: str
    embedding_status: str
    qdrant_point_id: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
