"""SOC 2 / GDPR readiness endpoints (v3.0.4).

Endpoints
---------
GET    /api/v1/compliance/me/export   Right-to-access — dump everything we hold on the caller
DELETE /api/v1/compliance/me          Right-to-erasure — schedule account + data deletion
GET    /api/v1/compliance/me/audit    Recent audit events touching the caller
GET    /api/v1/compliance/policies    Public — current retention + processing summary
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, status
from pydantic import BaseModel
from sqlalchemy import or_, select

from app.core.audit_log import log_security_event
from app.database import DB
from app.models.audit_event import AuditEvent
from app.models.portfolio import Portfolio
from app.models.resume import Resume
from app.security import CurrentUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/compliance", tags=["Compliance"])

class AuditEntry(BaseModel):
    id: uuid.UUID
    action: str
    target_type: str | None
    target_id: str | None
    created_at: datetime

class PoliciesResponse(BaseModel):
    retention_days_inactive_account: int = 365
    retention_days_audit_events: int = 730
    retention_days_webhook_deliveries: int = 90
    data_residency: str = "us-east"
    encryption_at_rest: bool = True
    encryption_in_transit: bool = True
    subprocessors: list[str] = [
        "Stripe (payments)",
        "Clerk (authentication)",
        "Resend (email)",
        "Anthropic / Google Gemini (AI inference)",
        "AWS S3 (object storage)",
    ]

@router.get("/policies", response_model=PoliciesResponse)
async def get_policies() -> PoliciesResponse:
    """Public — disclosed retention, residency, and subprocessor list."""
    return PoliciesResponse()

@router.get("/me/export")
async def export_my_data(db: DB, current_user: CurrentUser) -> dict:
    """SOC 2 / GDPR Art. 15 — return everything we hold on the caller."""
    portfolios = (
        await db.execute(select(Portfolio).where(Portfolio.user_id == current_user.id))
    ).scalars().all()
    resumes = (
        await db.execute(select(Resume).where(Resume.user_id == current_user.id))
    ).scalars().all()
    audit_rows = (
        await db.execute(
            select(AuditEvent)
            .where(AuditEvent.actor_user_id == current_user.id)
            .order_by(AuditEvent.created_at.desc())
            .limit(500)
        )
    ).scalars().all()

    log_security_event(
        "compliance_export",
        user_id=str(current_user.id),
        detail={"portfolios": len(portfolios), "resumes": len(resumes)},
    )
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "name": current_user.name,
            "plan": current_user.plan,
            "created_at": current_user.created_at.isoformat(),
        },
        "portfolios": [
            {
                "id": str(p.id),
                "slug": p.slug,
                "status": p.status,
                "template_id": p.template_id,
                "views": p.views,
                "created_at": p.created_at.isoformat(),
            }
            for p in portfolios
        ],
        "resumes": [
            {
                "id": str(r.id),
                "original_filename": r.original_filename,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
            }
            for r in resumes
        ],
        "audit_events": [
            {
                "action": a.action,
                "target_type": a.target_type,
                "target_id": a.target_id,
                "created_at": a.created_at.isoformat(),
            }
            for a in audit_rows
        ],
    }

@router.delete("/me", status_code=status.HTTP_202_ACCEPTED)
async def delete_my_account(db: DB, current_user: CurrentUser) -> dict:
    """SOC 2 / GDPR Art. 17 — schedule deletion of account + cascaded data.

    Cascades on Portfolio, Resume, APIKey, etc. via the ondelete=CASCADE FKs.
    Audit log entries are preserved (actor_user_id set NULL) for compliance.
    """
    user_id = current_user.id
    log_security_event(
        "compliance_account_deleted",
        user_id=str(user_id),
        detail={"plan": current_user.plan},
    )
    await db.delete(current_user)
    await db.commit()
    return {"deleted_user_id": str(user_id), "deleted_at": datetime.now(timezone.utc).isoformat()}

@router.get("/me/audit", response_model=list[AuditEntry])
async def my_audit_events(db: DB, current_user: CurrentUser) -> list[AuditEntry]:
    rows = (
        await db.execute(
            select(AuditEvent)
            .where(
                or_(
                    AuditEvent.actor_user_id == current_user.id,
                    AuditEvent.target_id == str(current_user.id),
                )
            )
            .order_by(AuditEvent.created_at.desc())
            .limit(100)
        )
    ).scalars().all()
    return [
        AuditEntry(
            id=a.id,
            action=a.action,
            target_type=a.target_type,
            target_id=a.target_id,
            created_at=a.created_at,
        )
        for a in rows
    ]
