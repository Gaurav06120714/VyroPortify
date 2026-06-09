"""Organization router (v2.0.0).

Endpoints
---------
GET    /api/v1/organizations              List orgs the caller belongs to
POST   /api/v1/organizations              Create a new org (caller becomes owner)
GET    /api/v1/organizations/{id}         Get one org (membership required)
GET    /api/v1/organizations/{id}/members List org members
POST   /api/v1/organizations/{id}/invite  Invite by email (admin+ required)
PATCH  /api/v1/organizations/{id}/members/{user_id}  Change role (owner only)
DELETE /api/v1/organizations/{id}/members/{user_id}  Remove member (owner only)

RBAC enforcement lives in app.core.authz.require_role (v2.0.1).
"""

import logging
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.authz import require_role
from app.database import DB
from app.models.organization import Membership, Organization
from app.models.user import User
from app.schemas.organization import (
    MembershipInvite,
    MembershipResponse,
    MembershipRoleUpdate,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationWithRole,
)
from app.security import CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/organizations", tags=["Organizations"])

def _slugify(name: str) -> str:
    """Lowercase, hyphenate, strip non-alphanum. Uniqueness is checked at the DB level."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)[:80]
    
    return f"{s}-{uuid.uuid4().hex[:6]}"

async def _ensure_member(
    organization_id: uuid.UUID, user: User, db: DB
) -> Membership:
    """Return the caller's membership in the org, or raise 404.

    404 (not 403) because the membership absence and the org absence are
    indistinguishable from the caller's perspective — same OWASP DOR
    rationale as core.authz.assert_owner.
    """
    result = await db.execute(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.user_id == user.id,
        )
    )
    m = result.scalar_one_or_none()
    if m is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )
    return m

@router.get(
    "",
    response_model=list[OrganizationWithRole],
    summary="List organizations the current user belongs to",
)
async def list_organizations(
    current_user: CurrentUser, db: DB
) -> list[OrganizationWithRole]:
    
    result = await db.execute(
        select(Membership)
        .join(Organization, Membership.organization_id == Organization.id)
        .where(Membership.user_id == current_user.id)
        .options(selectinload(Membership.organization))
        .order_by(Organization.is_personal.desc(), Organization.created_at.asc())
    )
    rows = result.scalars().all()
    return [
        OrganizationWithRole(
            id=m.organization.id,
            name=m.organization.name,
            slug=m.organization.slug,
            plan=m.organization.plan,
            is_personal=m.organization.is_personal,
            role=m.role,
        )
        for m in rows
    ]

@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization (caller becomes owner)",
)
async def create_organization(
    body: OrganizationCreate, current_user: CurrentUser, db: DB
) -> OrganizationResponse:
    org = Organization(
        name=body.name,
        slug=body.slug or _slugify(body.name),
        is_personal=False,
    )
    db.add(org)
    await db.flush()  

    db.add(Membership(organization_id=org.id, user_id=current_user.id, role="owner"))
    await db.commit()
    await db.refresh(org)
    logger.info("organization_created id=%s user=%s", org.id, current_user.id)
    return OrganizationResponse.model_validate(org)

@router.get(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Get one organization (membership required)",
)
async def get_organization(
    org_id: uuid.UUID, current_user: CurrentUser, db: DB
) -> OrganizationResponse:
    await _ensure_member(org_id, current_user, db)
    org = await db.get(Organization, org_id)
    return OrganizationResponse.model_validate(org)

@router.get(
    "/{org_id}/members",
    response_model=list[MembershipResponse],
    summary="List members of an organization",
)
async def list_members(
    org_id: uuid.UUID, current_user: CurrentUser, db: DB
) -> list[MembershipResponse]:
    await _ensure_member(org_id, current_user, db)
    result = await db.execute(
        select(Membership).where(Membership.organization_id == org_id)
    )
    return [MembershipResponse.model_validate(m) for m in result.scalars().all()]

@router.post(
    "/{org_id}/invite",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite an existing user to the organization (admin+)",
    dependencies=[Depends(require_role("admin"))],
)
async def invite_member(
    org_id: uuid.UUID,
    body: MembershipInvite,
    current_user: CurrentUser,
    db: DB,
) -> MembershipResponse:
    
    result = await db.execute(select(User).where(User.email == body.email))
    invitee = result.scalar_one_or_none()
    if invitee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user with that email exists yet — ask them to sign up first.",
        )

    existing = await db.execute(
        select(Membership).where(
            Membership.organization_id == org_id,
            Membership.user_id == invitee.id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User is already a member"
        )

    m = Membership(
        organization_id=org_id, user_id=invitee.id, role=body.role
    )
    db.add(m)
    await db.flush()

    from app.services.audit import record_audit_safe

    await record_audit_safe(
        db,
        organization_id=org_id,
        actor_user_id=current_user.id,
        action="membership.invite",
        target_type="user",
        target_id=str(invitee.id),
        meta={"role": body.role},
    )

    await db.commit()
    await db.refresh(m)
    logger.info(
        "membership_created org=%s user=%s role=%s invited_by=%s",
        org_id, invitee.id, body.role, current_user.id,
    )
    return MembershipResponse.model_validate(m)

@router.patch(
    "/{org_id}/members/{user_id}",
    response_model=MembershipResponse,
    summary="Change a member's role (owner only)",
    dependencies=[Depends(require_role("owner"))],
)
async def update_role(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    body: MembershipRoleUpdate,
    db: DB,
) -> MembershipResponse:
    result = await db.execute(
        select(Membership).where(
            Membership.organization_id == org_id, Membership.user_id == user_id
        )
    )
    m = result.scalar_one_or_none()
    if m is None:
        raise HTTPException(status_code=404, detail="Membership not found")
    m.role = body.role
    await db.commit()
    await db.refresh(m)
    return MembershipResponse.model_validate(m)

@router.get(
    "/{org_id}/audit-log",
    summary="List audit events for the org (admin+)",
    dependencies=[Depends(require_role("admin"))],
)
async def list_audit_log(
    org_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
    limit: int = 50,
    offset: int = 0,
    action: str | None = None,
) -> dict:
    
    from app.models.audit_event import AuditEvent

    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    q = select(AuditEvent).where(AuditEvent.organization_id == org_id)
    if action:
        q = q.where(AuditEvent.action.like(f"{action}%"))
    q = q.order_by(AuditEvent.created_at.desc()).limit(limit).offset(offset)

    rows = (await db.execute(q)).scalars().all()
    return {
        "items": [
            {
                "id": str(r.id),
                "action": r.action,
                "actor_user_id": str(r.actor_user_id) if r.actor_user_id else None,
                "target_type": r.target_type,
                "target_id": r.target_id,
                "meta": r.meta,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
        "limit": limit,
        "offset": offset,
    }

@router.delete(
    "/{org_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member (owner only)",
    dependencies=[Depends(require_role("owner"))],
)
async def remove_member(
    org_id: uuid.UUID, user_id: uuid.UUID, db: DB
) -> None:
    result = await db.execute(
        select(Membership).where(
            Membership.organization_id == org_id, Membership.user_id == user_id
        )
    )
    m = result.scalar_one_or_none()
    if m is None:
        raise HTTPException(status_code=404, detail="Membership not found")
    
    if m.role == "owner":
        from sqlalchemy import func as sql_func

        owner_count = await db.scalar(
            select(sql_func.count(Membership.id)).where(
                Membership.organization_id == org_id, Membership.role == "owner"
            )
        )
        if (owner_count or 0) <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove the last owner — promote another member first.",
            )
    await db.delete(m)
    await db.commit()

from pydantic import BaseModel as _BrBase  

class BrandingResponse(_BrBase):
    logo_url: str | None = None
    primary_color: str | None = None
    accent_color: str | None = None
    font_family: str | None = None
    custom_css: str | None = None
    hide_branding: bool = False

class BrandingUpdate(_BrBase):
    logo_url: str | None = None
    primary_color: str | None = None  
    accent_color: str | None = None
    font_family: str | None = None
    custom_css: str | None = None
    hide_branding: bool | None = None

_FORBIDDEN_CSS = ("<script", "</script", "<iframe", "javascript:", "@import")

def _sanitise_css(css: str | None) -> str | None:
    if css is None:
        return None
    low = css.lower()
    for bad in _FORBIDDEN_CSS:
        if bad in low:
            raise HTTPException(
                status_code=400,
                detail=f"custom_css contains disallowed token: {bad}",
            )
    if len(css) > 20_000:
        raise HTTPException(status_code=400, detail="custom_css too large (>20kB)")
    return css

@router.get(
    "/{org_id}/branding",
    response_model=BrandingResponse,
    summary="Get the org's white-label branding (members)",
)
async def get_branding(org_id: uuid.UUID, db: DB, current_user: CurrentUser) -> BrandingResponse:
    org = await db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Org not found")
    
    is_member = await db.scalar(
        select(Membership.id).where(
            Membership.organization_id == org_id, Membership.user_id == current_user.id
        )
    )
    if is_member is None:
        raise HTTPException(status_code=403, detail="Not a member of this org")
    return BrandingResponse(
        logo_url=org.logo_url,
        primary_color=org.primary_color,
        accent_color=org.accent_color,
        font_family=org.font_family,
        custom_css=org.custom_css,
        hide_branding=org.hide_branding,
    )

@router.put(
    "/{org_id}/branding",
    response_model=BrandingResponse,
    summary="Update white-label branding (admin+, enterprise plan only)",
    dependencies=[Depends(require_role("admin"))],
)
async def update_branding(
    org_id: uuid.UUID,
    body: BrandingUpdate,
    db: DB,
    current_user: CurrentUser,
) -> BrandingResponse:
    org = await db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Org not found")
    if org.plan != "enterprise":
        raise HTTPException(
            status_code=403,
            detail="White-label branding requires the enterprise plan.",
        )

    if body.custom_css is not None:
        org.custom_css = _sanitise_css(body.custom_css)
    if body.logo_url is not None:
        org.logo_url = body.logo_url or None
    if body.primary_color is not None:
        org.primary_color = body.primary_color or None
    if body.accent_color is not None:
        org.accent_color = body.accent_color or None
    if body.font_family is not None:
        org.font_family = body.font_family or None
    if body.hide_branding is not None:
        org.hide_branding = body.hide_branding

    await db.commit()
    return BrandingResponse(
        logo_url=org.logo_url,
        primary_color=org.primary_color,
        accent_color=org.accent_color,
        font_family=org.font_family,
        custom_css=org.custom_css,
        hide_branding=org.hide_branding,
    )
