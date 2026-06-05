"""SSO/SAML endpoints (v3.0.5).

This is a foundation, not a full SAML SP — XML signature verification needs
`python3-saml` for prod. Today the endpoints:

  GET  /api/v1/sso/configs/{org_id}  Return SP-side metadata + IdP config (admin+)
  PUT  /api/v1/sso/configs/{org_id}  Configure IdP (admin+, enterprise plan)
  GET  /api/v1/sso/login?domain=…    Public — discover IdP redirect for an email domain
  POST /api/v1/sso/acs               IdP POST-binding assertion consumer (stub)
"""

import logging
import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.authz import require_role
from app.database import DB
from app.models.organization import Organization
from app.models.sso import SSOConfig
from app.security import CurrentUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sso", tags=["SSO"])


class SSOConfigIn(BaseModel):
    idp_entity_id: str = Field(..., min_length=1, max_length=255)
    idp_sso_url: str = Field(..., min_length=1)
    idp_x509_cert: str = Field(..., min_length=1)
    sp_entity_id: str = Field(..., min_length=1, max_length=255)
    email_domain: str = Field(..., min_length=3, max_length=120)
    enabled: bool = True


class SSOConfigOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    idp_entity_id: str
    idp_sso_url: str
    sp_entity_id: str
    email_domain: str
    enabled: bool


@router.get(
    "/configs/{org_id}",
    response_model=SSOConfigOut | None,
    dependencies=[Depends(require_role("admin"))],
)
async def get_config(org_id: uuid.UUID, db: DB, current_user: CurrentUser) -> SSOConfigOut | None:
    cfg = (
        await db.execute(select(SSOConfig).where(SSOConfig.organization_id == org_id))
    ).scalar_one_or_none()
    if cfg is None:
        return None
    return SSOConfigOut(
        id=cfg.id,
        organization_id=cfg.organization_id,
        idp_entity_id=cfg.idp_entity_id,
        idp_sso_url=cfg.idp_sso_url,
        sp_entity_id=cfg.sp_entity_id,
        email_domain=cfg.email_domain,
        enabled=cfg.enabled,
    )


@router.put(
    "/configs/{org_id}",
    response_model=SSOConfigOut,
    dependencies=[Depends(require_role("admin"))],
)
async def put_config(
    org_id: uuid.UUID, body: SSOConfigIn, db: DB, current_user: CurrentUser
) -> SSOConfigOut:
    org = await db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Org not found")
    if org.plan != "enterprise":
        raise HTTPException(status_code=403, detail="SSO requires the enterprise plan.")

    cfg = (
        await db.execute(select(SSOConfig).where(SSOConfig.organization_id == org_id))
    ).scalar_one_or_none()
    if cfg is None:
        cfg = SSOConfig(organization_id=org_id, **body.model_dump())
        db.add(cfg)
    else:
        for k, v in body.model_dump().items():
            setattr(cfg, k, v)
    await db.commit()
    await db.refresh(cfg)
    return SSOConfigOut(
        id=cfg.id,
        organization_id=cfg.organization_id,
        idp_entity_id=cfg.idp_entity_id,
        idp_sso_url=cfg.idp_sso_url,
        sp_entity_id=cfg.sp_entity_id,
        email_domain=cfg.email_domain,
        enabled=cfg.enabled,
    )


@router.get("/login")
async def discover_idp(domain: str, db: DB) -> dict:
    """Public discovery — given an email domain, return the IdP SSO URL.

    Frontend calls this to decide between password (Clerk) and SAML redirect.
    """
    cfg = (
        await db.execute(
            select(SSOConfig).where(SSOConfig.email_domain == domain.lower(), SSOConfig.enabled.is_(True))
        )
    ).scalar_one_or_none()
    if cfg is None:
        return {"sso_enabled": False}
    return {
        "sso_enabled": True,
        "idp_sso_url": cfg.idp_sso_url,
        "sp_entity_id": cfg.sp_entity_id,
    }


@router.post("/acs", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def assertion_consumer_service(SAMLResponse: str = Form(...), RelayState: str | None = Form(default=None)) -> dict:
    """SAML 2.0 POST-binding Assertion Consumer Service.

    STUB: in v3.0.5 we accept the POST but require a future patch that wires
    `python3-saml` for XML signature verification before we trust the assertion.
    Returning 501 makes the intent explicit and prevents accidental bypass.
    """
    logger.info("SAML ACS hit (stub) — payload_len=%d relay=%s", len(SAMLResponse), bool(RelayState))
    return {
        "status": "not_implemented",
        "detail": "SAML assertion verification pending python3-saml integration.",
    }
