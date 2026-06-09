"""Pydantic schemas for organization + membership endpoints (v2.0)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str | None = Field(
        default=None,
        max_length=120,
        description="Optional; auto-generated from name if omitted.",
    )

class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    plan: str
    is_personal: bool
    created_at: datetime

class MembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    created_at: datetime

class OrganizationWithRole(BaseModel):
    """Returned by /me/organizations — the user's orgs + their role in each."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    plan: str
    is_personal: bool
    role: str  

class MembershipInvite(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    role: str = Field(pattern="^(admin|editor|viewer)$")

class MembershipRoleUpdate(BaseModel):
    role: str = Field(pattern="^(owner|admin|editor|viewer)$")
