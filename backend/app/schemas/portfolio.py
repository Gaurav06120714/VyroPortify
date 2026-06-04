"""Pydantic v2 schemas for portfolio endpoints."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GeneratePortfolioRequest(BaseModel):
    resume_id: uuid.UUID
    template_id: str = Field(default="aurora", pattern="^(aurora|minimal|cyber)$")


class PortfolioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    resume_id: uuid.UUID | None
    slug: str
    template_id: str | None
    content: dict[str, Any] | None
    html_url: str | None
    is_public: bool
    views: int
    status: str
    created_at: datetime
    updated_at: datetime


class PortfolioStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    html_url: str | None
    slug: str
    ai_fallback: bool = False


class PortfolioListResponse(BaseModel):
    items: list[PortfolioResponse]
    total: int


class GeneratePortfolioResponse(BaseModel):
    portfolio_id: uuid.UUID
    job_queued: bool
    message: str


# ── Custom domain (Pro) ────────────────────────────────────────────────────────


class CustomDomainRequest(BaseModel):
    # Stored normalized (lowercase, no scheme). Validation happens server-side
    # so we accept slightly sloppy input (e.g. "https://Alex.dev/") here.
    domain: str = Field(min_length=3, max_length=253)


class CustomDomainResponse(BaseModel):
    portfolio_id: uuid.UUID
    domain: str | None
    verified: bool
    cname_target: str | None
    expected_target: str
    detail: str
