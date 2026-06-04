"""Resume router — upload, build, list, delete.

Endpoints
---------
POST   /api/v1/resume/upload         Upload PDF/DOCX, store in S3, create DB record
POST   /api/v1/resume/build          Build resume from form data via Claude
POST   /api/v1/resume/suggest-skills AI skill suggestions for a partial profile
POST   /api/v1/resume/cover-letter   Generate a tailored cover letter via Claude
GET    /api/v1/resume/               List current user's resumes (with presigned URLs)
GET    /api/v1/resume/{id}/url       Generate a fresh presigned URL for a specific resume
DELETE /api/v1/resume/{id}           Delete from S3 + DB

All endpoints require:
    Authorization: Bearer <access_token>
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import func, select

from app.core.authz import assert_owner, require_plan
from app.core.config import settings
from app.core.enums import Plan, ResumeStatus
from app.core.limiter import limiter
from app.core.rate_limit import RateLimitCheck
from app.database import DB
from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import (
    PresignedUrlResponse,
    ResumeListResponse,
    ResumeResponse,
    ResumeStatusResponse,
)
from app.security import CurrentUser
from app.services.s3_service import (
    ALLOWED_MIME_TYPES,
    storage,
    validate_content_type,
    validate_presigned_ttl,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resume", tags=["Resume"])

# ── Constants ──────────────────────────────────────────────────────────────────

_MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


# ── Build schemas ──────────────────────────────────────────────────────────────

class WorkExperienceInput(BaseModel):
    company: str = ""
    role: str = ""
    achievements: str = ""

class ProjectInput(BaseModel):
    name: str = ""
    description: str = ""
    tech: list[str] = []
    link: str = ""

class EducationInput(BaseModel):
    degree: str = ""
    institution: str = ""
    year: str = ""

class BuildResumeRequest(BaseModel):
    personal: dict = {}
    experience_summary: dict = {}
    work_experiences: list[WorkExperienceInput] = []
    projects: list[ProjectInput] = []
    education: EducationInput = EducationInput()
    skills: list[str] = []
    social_links: dict = {}
    career_goal: str = ""

class BuildResumeResponse(BaseModel):
    resume_id: str
    filename: str
    message: str

class SuggestSkillsRequest(BaseModel):
    current_skills: list[str] = []
    tech_stack: list[str] = []
    role_titles: list[str] = []
    career_goal: str = ""

class SuggestSkillsResponse(BaseModel):
    suggestions: list[str]


class CoverLetterRequest(BaseModel):
    name: str = ""
    title: str = ""
    company: str = ""
    role: str = ""
    highlights: str = ""  # key achievements / selling points
    tone: str = "professional"  # professional | enthusiastic | concise


class CoverLetterResponse(BaseModel):
    cover_letter: str


# ── POST /build ────────────────────────────────────────────────────────────────

@router.post(
    "/build",
    response_model=BuildResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Build a resume from form data using Claude AI",
)
@limiter.limit("10/hour")
async def build_resume(
    request: Request,
    payload: BuildResumeRequest,
    current_user: CurrentUser,
    db: DB,
) -> BuildResumeResponse:
    from app.services.resume_builder import build_resume_with_claude

    form_data = payload.model_dump()

    # Run Claude builder (sync — wraps in thread via anyio if needed)
    import anyio
    resume_data = await anyio.to_thread.run_sync(
        lambda: build_resume_with_claude(form_data)
    )

    name = form_data.get("personal", {}).get("name", "resume")
    filename = f"{name.lower().replace(' ', '_')}_ai_resume.json"

    resume = Resume(
        user_id=current_user.id,
        original_filename=filename,
        file_type="json",
        parsed_data=resume_data.model_dump(),
        raw_text=None,
        status=ResumeStatus.PARSED,  # already parsed — skip Celery task
    )
    db.add(resume)
    await db.flush()

    logger.info("AI-built resume created id=%s user=%s", resume.id, current_user.id)

    return BuildResumeResponse(
        resume_id=str(resume.id),
        filename=filename,
        message="Resume built successfully",
    )


# ── POST /suggest-skills ───────────────────────────────────────────────────────

@router.post(
    "/suggest-skills",
    response_model=SuggestSkillsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI skill suggestions based on partial profile (Pro only)",
    dependencies=[Depends(require_plan(Plan.PRO, feature="AI skill suggestions"))],
)
@limiter.limit("10/hour")
async def suggest_skills(
    request: Request,
    payload: SuggestSkillsRequest,
    current_user: CurrentUser,
) -> SuggestSkillsResponse:
    try:
        from app.services.resume_parser import sanitize_for_ai

        from app.services.ai_client import call_ai

        # Sanitize all user-supplied strings before embedding in the prompt.
        safe_career_goal = sanitize_for_ai(payload.career_goal, source="career_goal")
        safe_roles = [r[:100] for r in payload.role_titles[:20]]
        safe_stack = [t[:100] for t in payload.tech_stack[:50]]
        safe_skills = [s[:100] for s in payload.current_skills[:100]]

        prompt = (
            f"Given a developer/designer with these role titles: {', '.join(safe_roles)}, "
            f"tech stack: {', '.join(safe_stack)}, "
            f"career goal: {safe_career_goal[:500]}, "
            f"and existing skills: {', '.join(safe_skills)}, "
            f"suggest 8–12 additional relevant skills they should add to their resume. "
            f"Return ONLY a JSON array of strings, no explanation. Example: [\"Docker\", \"CI/CD\"]"
        )
        import json
        raw = call_ai(prompt=prompt, max_tokens=256).strip().strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
        suggestions = json.loads(raw)
        # Filter out skills the user already has
        existing_lower = {s.lower() for s in payload.current_skills}
        filtered = [s for s in suggestions if s.lower() not in existing_lower]
        return SuggestSkillsResponse(suggestions=filtered[:12])
    except Exception as exc:
        logger.warning("Skill suggestion failed: %s", exc)
        return SuggestSkillsResponse(suggestions=[])


# ── POST /cover-letter ─────────────────────────────────────────────────────────

@router.post(
    "/cover-letter",
    response_model=CoverLetterResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a tailored cover letter using Claude AI (Pro only)",
    dependencies=[Depends(require_plan(Plan.PRO, feature="AI cover letter"))],
)
@limiter.limit("10/hour")
async def generate_cover_letter(
    request: Request,
    payload: CoverLetterRequest,
    current_user: CurrentUser,
) -> CoverLetterResponse:
    from app.services.resume_parser import sanitize_for_ai

    safe_name = sanitize_for_ai(payload.name[:100], source="name")
    safe_title = sanitize_for_ai(payload.title[:100], source="title")
    safe_company = sanitize_for_ai(payload.company[:150], source="company")
    safe_role = sanitize_for_ai(payload.role[:150], source="role")
    safe_highlights = sanitize_for_ai(payload.highlights[:800], source="highlights")
    tone_map = {"professional": "professional and polished", "enthusiastic": "enthusiastic and energetic", "concise": "concise and direct"}
    tone_desc = tone_map.get(payload.tone, "professional and polished")

    prompt = (
        f"Write a {tone_desc} cover letter for {safe_name}, a {safe_title}, "
        f"applying for the {safe_role} position at {safe_company}.\n\n"
        f"Key highlights to weave in:\n{safe_highlights}\n\n"
        f"Requirements:\n"
        f"- 3-4 paragraphs\n"
        f"- Opening that immediately grabs attention\n"
        f"- Middle paragraphs demonstrating fit with specific achievements\n"
        f"- Strong closing with a clear call to action\n"
        f"- No filler phrases like 'I am writing to express my interest'\n"
        f"- Output only the cover letter text, no subject line or date headers"
    )

    try:
        from app.services.ai_client import call_ai
        # use_cache=False — identical inputs should still produce fresh phrasing.
        letter = call_ai(prompt=prompt, max_tokens=1024, use_cache=False)
        return CoverLetterResponse(cover_letter=letter)
    except Exception as exc:
        logger.warning("Cover letter generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cover letter generation failed. Please try again.",
        )


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _get_resume_or_404(resume_id: uuid.UUID, user: User, db: DB) -> Resume:
    """Fetch a resume owned by *user*, or raise 404.

    Ownership is enforced via app.core.authz.assert_owner so the policy lives
    in a single audited place.
    """
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    return assert_owner(result.scalar_one_or_none(), user)


def _to_response(resume: Resume, presigned_url: str | None = None) -> ResumeResponse:
    """Map ORM → response schema, optionally injecting a fresh presigned URL."""
    return ResumeResponse(
        id=resume.id,
        user_id=resume.user_id,
        file_url=presigned_url or resume.file_url,
        file_type=resume.file_type,
        original_filename=resume.original_filename,
        status=resume.status,
        parsed_data=resume.parsed_data,
        raw_text=resume.raw_text,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
    )


# ── POST /upload ───────────────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a resume (PDF or DOCX, max 5 MB)",
    responses={
        201: {"description": "Resume uploaded and DB record created"},
        400: {"description": "Unsupported file type or file too large"},
        401: {"description": "Not authenticated"},
        413: {"description": "File exceeds the maximum allowed size"},
    },
    dependencies=[
        # 20 uploads / hour / IP — prevent storage abuse
        Depends(RateLimitCheck("resume:upload", max_per_ip=20, window_seconds=3600)),
    ],
)
async def upload_resume(
    file: UploadFile,
    current_user: CurrentUser,
    db: DB,
) -> ResumeResponse:
    # ── 1. Validate content-type ───────────────────────────────────────────
    content_type = file.content_type or ""
    try:
        file_ext = validate_content_type(content_type)
    except ValueError:
        allowed = ", ".join(sorted(ALLOWED_MIME_TYPES.keys()))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{content_type}'. Allowed: {allowed}",
        )

    # ── 2. Read and size-check ─────────────────────────────────────────────
    # Use await file.read() — Python 3.14 removed async iteration on UploadFile
    file_bytes = await file.read()
    total_bytes = len(file_bytes)

    if total_bytes == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    if total_bytes > _MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit "
                f"(received {total_bytes / 1_048_576:.1f} MB)"
            ),
        )

    # ── 2b. Magic byte validation ──────────────────────────────────────────
    # The Content-Type header is attacker-controlled and CANNOT be trusted.
    # We independently verify the file's actual format by checking its magic
    # bytes (the first few bytes that identify a file format), then confirm
    # they match the declared content-type.
    #
    # PDF magic: b'%PDF' (0x25 0x50 0x44 0x46)
    # DOCX/ZIP magic: b'PK\x03\x04' (DOCX is a ZIP archive)
    # DOC magic: b'\xD0\xCF\x11\xE0' (OLE2 Compound File)
    _MAGIC_MAP = {
        "pdf": (b"%PDF",),
        "docx": (b"PK\x03\x04",),
        "doc": (b"\xD0\xCF\x11\xE0",),
    }
    expected_magic_signatures = _MAGIC_MAP.get(file_ext, ())
    if expected_magic_signatures:
        magic_match = any(file_bytes.startswith(sig) for sig in expected_magic_signatures)
        if not magic_match:
            from app.core.audit_log import log_security_event
            log_security_event(
                "file_magic_mismatch",
                user_id=str(current_user.id),
                detail={
                    "declared_content_type": content_type,
                    "expected_extension": file_ext,
                    "actual_magic_hex": file_bytes[:4].hex() if file_bytes else "",
                    "filename": file.filename or "",
                },
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"File content does not match declared type '{content_type}'. "
                    "Please upload a valid PDF or DOCX file."
                ),
            )
    original_filename = file.filename or f"resume.{file_ext}"

    # ── 3. Upload to S3/R2 (falls back to local disk if S3 not configured) ──
    s3_key: str
    presigned: str | None = None

    s3_configured = bool(settings.AWS_ACCESS_KEY_ID or settings.R2_ACCESS_KEY_ID)

    if s3_configured:
        try:
            s3_key = await storage.upload_file(
                data=file_bytes,
                user_id=current_user.id,
                filename=original_filename,
                content_type=content_type,
            )
            presigned = await storage.presigned_url(
                s3_key, ttl_hours=settings.PRESIGNED_URL_DEFAULT_HOURS
            )
        except Exception as exc:
            logger.exception("S3 upload failed for user %s: %s", current_user.id, exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="File storage service unavailable. Please try again.",
            )
    else:
        # Local fallback — store in /tmp/vyroportify_uploads/ with unique name
        import os
        import uuid as _uuid
        upload_dir = "/tmp/vyroportify_uploads"
        os.makedirs(upload_dir, exist_ok=True)
        unique_id = str(_uuid.uuid4())[:8]
        safe_name = f"{current_user.id}_{unique_id}_{original_filename}"
        local_path = os.path.join(upload_dir, safe_name)
        with open(local_path, "wb") as f:
            f.write(file_bytes)
        s3_key = f"local/{safe_name}"
        presigned = None
        logger.info("S3 not configured — saved file locally at %s", local_path)

    # ── 5. Persist to database ────────────────────────────────────────────
    resume = Resume(
        user_id=current_user.id,
        s3_key=s3_key,
        file_url=presigned,
        original_filename=original_filename,
        file_type=file_ext,
        status=ResumeStatus.UPLOADED,  # will be updated by the AI parse job
    )
    db.add(resume)
    await db.flush()  # get ID assigned before returning

    logger.info(
        "Resume created id=%s user=%s key=%s size=%d bytes",
        resume.id, current_user.id, s3_key, total_bytes,
    )

    # ── 6. Parse resume synchronously (inline fallback when Celery unavailable) ──
    try:
        import anyio

        from app.services.resume_parser import parse_resume_bytes
        parsed = await anyio.to_thread.run_sync(
            lambda: parse_resume_bytes(file_bytes, file_ext)
        )
        resume.parsed_data = parsed.model_dump()
        resume.status = ResumeStatus.PARSED
        await db.flush()
        logger.info("Resume parsed inline id=%s", resume.id)
    except Exception as exc:
        logger.error("Inline parse failed for resume %s: %s — will retry via Celery", resume.id, exc)
        # Try Celery as backup
        try:
            from app.workers.tasks.parse_resume import parse_resume_task
            parse_resume_task.delay(str(resume.id))
        except Exception:
            pass  # truly non-fatal — resume saved, parsing can be retried

    return _to_response(resume, presigned)


# ── GET / (list) ───────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=ResumeListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all resumes for the current user",
    responses={
        200: {"description": "Paginated list of resumes with fresh presigned URLs"},
        401: {"description": "Not authenticated"},
    },
)
async def list_resumes(
    current_user: CurrentUser,
    db: DB,
    ttl_hours: int = Query(
        default=settings.PRESIGNED_URL_DEFAULT_HOURS,
        description=(
            f"Presigned URL lifetime in hours. "
            f"Must be a positive multiple of {2} "
            f"(e.g. 2, 4, 24, 48). "
            f"Max: {settings.PRESIGNED_URL_MAX_HOURS}h."
        ),
        ge=2,
    ),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
) -> ResumeListResponse:
    # Validate TTL before hitting the DB
    try:
        ttl_hours = validate_presigned_ttl(ttl_hours)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Count total for pagination metadata
    total_result = await db.execute(
        select(func.count()).select_from(Resume).where(Resume.user_id == current_user.id)
    )
    total = total_result.scalar_one()

    # Fetch page
    rows_result = await db.execute(
        select(Resume)
        .where(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    resumes = rows_result.scalars().all()

    # Generate fresh presigned URLs concurrently for all resumes that have an s3_key
    import asyncio

    async def _with_url(r: Resume) -> ResumeResponse:
        if r.s3_key:
            try:
                url = await storage.presigned_url(r.s3_key, ttl_hours=ttl_hours)
                return _to_response(r, url)
            except Exception:
                logger.warning("Could not generate presigned URL for resume %s", r.id)
        return _to_response(r)

    items = await asyncio.gather(*[_with_url(r) for r in resumes])

    return ResumeListResponse(items=list(items), total=total)


# ── GET /{id}/url ──────────────────────────────────────────────────────────────

@router.get(
    "/{resume_id}/url",
    response_model=PresignedUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a fresh presigned download URL for a resume",
    responses={
        200: {"description": "Fresh presigned URL"},
        400: {"description": "Invalid ttl_hours value"},
        401: {"description": "Not authenticated"},
        404: {"description": "Resume not found"},
    },
)
async def get_presigned_url(
    resume_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
    ttl_hours: int = Query(
        default=settings.PRESIGNED_URL_DEFAULT_HOURS,
        description=(
            "Presigned URL lifetime in hours. "
            "Must be a positive multiple of 2 (e.g. 2, 4, 24, 48). "
            f"Max: {settings.PRESIGNED_URL_MAX_HOURS}h."
        ),
        ge=2,
    ),
) -> PresignedUrlResponse:
    try:
        ttl_hours = validate_presigned_ttl(ttl_hours)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    resume = await _get_resume_or_404(resume_id, current_user, db)

    if not resume.s3_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This resume has no associated file",
        )

    try:
        url = await storage.presigned_url(resume.s3_key, ttl_hours=ttl_hours)
    except Exception as exc:
        logger.exception("Presigned URL generation failed for resume %s: %s", resume_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not generate download URL. Please try again.",
        )

    return PresignedUrlResponse(
        url=url,
        expires_in_hours=ttl_hours,
        key=resume.s3_key,
    )


# ── DELETE /{id} ───────────────────────────────────────────────────────────────

@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a resume from S3 and the database",
    responses={
        204: {"description": "Resume deleted (no content)"},
        401: {"description": "Not authenticated"},
        404: {"description": "Resume not found"},
        502: {"description": "S3 deletion failed — DB record preserved for retry"},
    },
)
async def delete_resume(
    resume_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> None:
    resume = await _get_resume_or_404(resume_id, current_user, db)

    # ── 1. Delete from S3 first ───────────────────────────────────────────
    # Strategy: delete S3 object before the DB row. If S3 fails we return 502
    # and the DB row is preserved, making retries safe. If DB deletion fails
    # after a successful S3 delete the row becomes an orphan — acceptable for
    # MVP; production would use a background cleanup job.
    if resume.s3_key:
        try:
            await storage.delete_file(resume.s3_key)
        except Exception as exc:
            logger.exception(
                "S3 delete failed for resume %s key=%s: %s", resume_id, resume.s3_key, exc
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="File could not be deleted from storage. Please try again.",
            )

    # ── 2. Delete DB record ───────────────────────────────────────────────
    await db.delete(resume)
    # Commit happens automatically when get_db() exits the context manager

    logger.info("Resume deleted id=%s user=%s key=%s", resume_id, current_user.id, resume.s3_key)


# ── GET /{id}/status ───────────────────────────────────────────────────────────

@router.get(
    "/{resume_id}/status",
    response_model=ResumeStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Poll the parsing status of a resume",
    responses={
        200: {"description": "Current parse status and parsed data (if done)"},
        401: {"description": "Not authenticated"},
        404: {"description": "Resume not found"},
    },
)
async def get_resume_status(
    resume_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
) -> ResumeStatusResponse:
    resume = await _get_resume_or_404(resume_id, current_user, db)
    return ResumeStatusResponse(
        id=resume.id,
        status=resume.status,
        parsed_data=resume.parsed_data,
    )


# ── POST /{id}/export-pdf (v2.3) ──────────────────────────────────────────────

@router.post(
    "/{resume_id}/export-pdf",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Render an ATS-friendly resume PDF (Modern/Classic/Compact)",
)
@limiter.limit("10/hour")
async def export_resume_pdf_endpoint(
    request: Request,
    resume_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
    template_id: str = "modern",
) -> dict:
    """Start an async PDF render. Returns the export id + cache status.

    Idempotency: if a row with the same (resume_id, content_hash) already
    has an s3_key, return it immediately — no recompile. Repeat clicks
    on `Download PDF` against unchanged data are a single Stripe call,
    not a fresh render.
    """
    from sqlalchemy import desc

    from app.models.resume_export import ResumeExport
    from app.services.resume_pdf import ResumePayload, TEMPLATES, content_hash

    if template_id not in TEMPLATES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown template '{template_id}'; choose one of {sorted(TEMPLATES)}",
        )

    resume = await _get_resume_or_404(resume_id, current_user, db)
    if not resume.parsed_data:
        raise HTTPException(
            status_code=400,
            detail="Resume hasn't been parsed yet. Wait for parsing to complete first.",
        )

    payload = ResumePayload(
        personal=resume.parsed_data.get("personal", {})
            or {
                "full_name": resume.parsed_data.get("full_name"),
                "email": resume.parsed_data.get("email"),
                "phone": resume.parsed_data.get("phone"),
            },
        links=resume.parsed_data.get("links", {}),
        summary=resume.parsed_data.get("summary"),
        experience=resume.parsed_data.get("work_experience", []),
        education=resume.parsed_data.get("education", []),
        skills=resume.parsed_data.get("skills", []),
        projects=resume.parsed_data.get("projects", []),
        certifications=resume.parsed_data.get("certifications", []),
        achievements=resume.parsed_data.get("achievements", []),
    )
    chash = content_hash(payload, template_id)

    # Cache lookup: same payload + template → return the prior export.
    existing = await db.execute(
        select(ResumeExport)
        .where(
            ResumeExport.resume_id == resume.id,
            ResumeExport.content_hash == chash,
            ResumeExport.s3_key.isnot(None),
        )
        .order_by(desc(ResumeExport.created_at))
        .limit(1)
    )
    hit = existing.scalar_one_or_none()
    if hit is not None:
        return {
            "export_id": str(hit.id),
            "status": "completed",
            "cached": True,
            "engine": hit.engine,
        }

    export = ResumeExport(
        resume_id=resume.id,
        user_id=current_user.id,
        content_hash=chash,
        template_id=template_id,
    )
    db.add(export)
    await db.commit()
    await db.refresh(export)

    # Dispatch render off-process. Synchronous .run() is available for
    # tests that want to skip Celery; production goes through .delay().
    try:
        from app.workers.tasks.export_resume_pdf import export_resume_pdf as task

        task.delay(str(export.id))
    except Exception as exc:
        logger.warning("export_pdf_dispatch_failed: %s", exc)

    return {
        "export_id": str(export.id),
        "status": "queued",
        "cached": False,
    }


@router.get(
    "/exports/{export_id}",
    summary="Get a resume export status + presigned download URL when ready",
)
async def get_resume_export(
    export_id: uuid.UUID, current_user: CurrentUser, db: DB
) -> dict:
    from app.models.resume_export import ResumeExport

    export = await db.get(ResumeExport, export_id)
    if export is None or export.user_id != current_user.id:
        # Same OWASP DOR policy as elsewhere: 404 on foreign / missing.
        raise HTTPException(status_code=404, detail="Export not found")

    if not export.s3_key:
        return {"status": "queued"}

    try:
        url = await storage.presigned_url(export.s3_key, ttl_hours=2)
    except Exception as exc:
        logger.warning(
            "export_presign_failed id=%s err=%s", export.id, exc
        )
        raise HTTPException(status_code=502, detail="Could not generate download URL")

    return {
        "status": "completed",
        "download_url": url,
        "file_size": export.file_size,
        "engine": export.engine,
        "template_id": export.template_id,
    }
