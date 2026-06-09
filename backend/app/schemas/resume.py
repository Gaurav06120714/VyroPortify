"""Pydantic v2 schemas for resume endpoints."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

class ResumeResponse(BaseModel):
    """Public representation of a Resume row (no S3 key exposed)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    file_url: str | None          
    file_type: str | None         
    original_filename: str | None 
    status: str                   
    parsed_data: dict[str, Any] | None
    raw_text: str | None
    created_at: datetime
    updated_at: datetime

class ResumeListResponse(BaseModel):
    """Paginated list of resumes."""

    items: list[ResumeResponse]
    total: int

class ResumeStatusResponse(BaseModel):
    """Polling response for parse job status."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    parsed_data: dict[str, Any] | None

class PresignedUrlResponse(BaseModel):
    """Standalone presigned URL response."""

    url: str
    expires_in_hours: int = Field(description="How many hours until this URL expires")
    key: str = Field(description="S3 object key — use with DELETE /resume/{id}")
