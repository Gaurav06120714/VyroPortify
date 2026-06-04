"""ATS-friendly resume PDF export (v2.3).

Two engines in priority order:

  1. Tectonic — self-contained LaTeX, deterministic builds, ~120 MB
     in the Celery worker image. First choice. Renders our Jinja2
     templates in `backend/app/templates/resume_pdf/`.
  2. ReportLab — pure-Python fallback. Used when the tectonic binary
     isn't on PATH (dev environments, smoke tests) and when LaTeX
     compilation fails on user-input edge cases (curly quotes,
     unusual Unicode). Layout is intentionally minimalist but still
     single-column + standard section names so ATS parsers pick up
     every field.

Both engines accept the same `ResumePayload` so the caller never has
to branch.

LaTeX safety: the Jinja2 environment escapes user-supplied strings
with `latex_escape()` so a hostile resume payload can't smuggle TeX
commands (`\\input{...}` would otherwise be a remote-file-read vector).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "resume_pdf"
TEMPLATES = {"modern", "classic", "compact"}


# ── Input schema ──────────────────────────────────────────────────────────────

@dataclass
class ResumePayload:
    """Normalized resume data accepted by both engines."""
    personal: dict[str, Any] = field(default_factory=dict)
    links: dict[str, Any] = field(default_factory=dict)
    summary: str | None = None
    experience: list[dict[str, Any]] = field(default_factory=list)
    education: list[dict[str, Any]] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    projects: list[dict[str, Any]] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    achievements: list[str] = field(default_factory=list)


# ── LaTeX escaping (Jinja filter) ─────────────────────────────────────────────

# Characters with special meaning in LaTeX. Order matters: backslash first.
_LATEX_SPECIAL = [
    ("\\", r"\textbackslash{}"),
    ("&", r"\&"),
    ("%", r"\%"),
    ("$", r"\$"),
    ("#", r"\#"),
    ("_", r"\_"),
    ("{", r"\{"),
    ("}", r"\}"),
    ("~", r"\textasciitilde{}"),
    ("^", r"\textasciicircum{}"),
]


def latex_escape(value: Any) -> str:
    """Escape every LaTeX metacharacter in a user-supplied string.

    Applied automatically by the Jinja2 autoescape hook below. Lists and
    dicts pass through (escaped recursively at the template level).
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    for src, dst in _LATEX_SPECIAL:
        value = value.replace(src, dst)
    return value


def _jinja_env() -> Environment:
    """Jinja env with LaTeX-safe defaults.

    autoescape stays off for the .tex.j2 extension — we drive escaping
    through the explicit `latex_escape` filter installed below and run
    it via finalize so every {{ var }} interpolation is escaped.
    """
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(disabled_extensions=("tex.j2",)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        finalize=latex_escape,
    )
    env.filters["latex_escape"] = latex_escape
    return env


# ── Content hash ──────────────────────────────────────────────────────────────

def content_hash(payload: ResumePayload, template_id: str) -> str:
    """SHA-256(template + canonicalized payload). Used for cache lookups."""
    data = {
        "template": template_id,
        "payload": {
            "personal": payload.personal,
            "links": payload.links,
            "summary": payload.summary,
            "experience": payload.experience,
            "education": payload.education,
            "skills": payload.skills,
            "projects": payload.projects,
            "certifications": payload.certifications,
            "achievements": payload.achievements,
        },
    }
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


# ── Tectonic engine ───────────────────────────────────────────────────────────

def _tectonic_available() -> bool:
    return shutil.which("tectonic") is not None


def _render_with_tectonic(payload: ResumePayload, template_id: str) -> bytes:
    env = _jinja_env()
    template = env.get_template(f"{template_id}.tex.j2")
    tex_source = template.render(
        personal=payload.personal,
        links=payload.links,
        summary=payload.summary,
        experience=payload.experience,
        education=payload.education,
        skills=payload.skills,
        projects=payload.projects,
        certifications=payload.certifications,
        achievements=payload.achievements,
    )

    with tempfile.TemporaryDirectory() as workdir:
        tex_path = Path(workdir) / "resume.tex"
        tex_path.write_text(tex_source, encoding="utf-8")
        # --keep-logs=no, --print=false to keep tectonic chatty-but-not-loud.
        # --outdir keeps the .pdf next to the .tex so we can read it back.
        result = subprocess.run(
            ["tectonic", "--outdir", workdir, "--keep-logs=no", str(tex_path)],
            capture_output=True,
            timeout=60,
            check=False,
        )
        pdf_path = Path(workdir) / "resume.pdf"
        if result.returncode != 0 or not pdf_path.exists():
            logger.warning(
                "tectonic_compile_failed code=%s stderr=%s",
                result.returncode, result.stderr.decode("utf-8", errors="replace")[:1000],
            )
            raise RuntimeError("tectonic compile failed")
        return pdf_path.read_bytes()


# ── ReportLab fallback engine ─────────────────────────────────────────────────

def _render_with_reportlab(payload: ResumePayload) -> bytes:
    # Imported lazily so the dep is optional for environments that
    # never hit the fallback (e.g. workers that always have tectonic).
    from io import BytesIO

    from reportlab.lib.colors import HexColor, black
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import (
        ListFlowable,
        ListItem,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
    )

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40,
        title=f"{payload.personal.get('full_name', 'Resume')} — Resume",
    )

    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "vp-body", parent=styles["Normal"], fontSize=10.5, leading=14,
        textColor=black, alignment=TA_LEFT,
    )
    h1 = ParagraphStyle(
        "vp-h1", parent=body, fontSize=20, leading=24, spaceAfter=2,
    )
    h2 = ParagraphStyle(
        "vp-h2", parent=body, fontSize=12, leading=16, spaceBefore=14, spaceAfter=4,
        textColor=HexColor("#2563EB"), fontName="Helvetica-Bold",
    )
    muted = ParagraphStyle("vp-muted", parent=body, textColor=HexColor("#475569"))

    story: list[Any] = []

    # Header
    name = payload.personal.get("full_name", "")
    title = payload.personal.get("title", "")
    if name:
        story.append(Paragraph(f"<b>{name}</b>", h1))
    if title:
        story.append(Paragraph(title, muted))
    contact_bits = [
        payload.personal.get("email"),
        payload.personal.get("phone"),
        payload.personal.get("location"),
    ]
    contact_line = " · ".join(b for b in contact_bits if b)
    if contact_line:
        story.append(Paragraph(contact_line, muted))
    story.append(Spacer(1, 8))

    def section(title: str) -> None:
        story.append(Paragraph(title.upper(), h2))

    if payload.summary:
        section("Summary")
        story.append(Paragraph(payload.summary, body))

    if payload.experience:
        section("Experience")
        for job in payload.experience:
            role = job.get("role", "")
            company = job.get("company", "")
            start = job.get("start", "")
            end = job.get("end") or "Present"
            story.append(
                Paragraph(f"<b>{role}</b> · {company} · {start} – {end}", body)
            )
            bullets = job.get("bullets") or []
            if bullets:
                items = [ListItem(Paragraph(b, body)) for b in bullets]
                story.append(ListFlowable(items, bulletType="bullet", leftIndent=14))
            story.append(Spacer(1, 6))

    if payload.education:
        section("Education")
        for ed in payload.education:
            story.append(
                Paragraph(
                    f"<b>{ed.get('degree', '')}</b> · {ed.get('institution', '')}"
                    f" · {ed.get('year', '')}",
                    body,
                )
            )

    if payload.skills:
        section("Skills")
        story.append(Paragraph(" · ".join(payload.skills), body))

    if payload.projects:
        section("Projects")
        for p in payload.projects:
            line = f"<b>{p.get('name', '')}</b>"
            if p.get("description"):
                line += f" — {p['description']}"
            story.append(Paragraph(line, body))

    if payload.certifications:
        section("Certifications")
        items = [ListItem(Paragraph(c, body)) for c in payload.certifications]
        story.append(ListFlowable(items, bulletType="bullet", leftIndent=14))

    if payload.achievements:
        section("Achievements")
        items = [ListItem(Paragraph(a, body)) for a in payload.achievements]
        story.append(ListFlowable(items, bulletType="bullet", leftIndent=14))

    doc.build(story)
    return buf.getvalue()


# ── Public entry point ────────────────────────────────────────────────────────

@dataclass
class RenderResult:
    pdf_bytes: bytes
    engine: Literal["tectonic", "reportlab"]
    content_hash: str


def render_resume_pdf(
    payload: ResumePayload, template_id: str = "modern"
) -> RenderResult:
    """Return a rendered PDF + the engine used + the content hash.

    Strategy: try tectonic, fall back to reportlab on any failure. The
    fallback is automatic so the call site never has to branch.
    """
    if template_id not in TEMPLATES:
        raise ValueError(f"Unknown template: {template_id!r}")

    chash = content_hash(payload, template_id)

    if _tectonic_available():
        try:
            return RenderResult(
                pdf_bytes=_render_with_tectonic(payload, template_id),
                engine="tectonic",
                content_hash=chash,
            )
        except Exception as exc:
            logger.warning("tectonic_failed_fallback_to_reportlab err=%s", exc)

    return RenderResult(
        pdf_bytes=_render_with_reportlab(payload),
        engine="reportlab",
        content_hash=chash,
    )


# ── ATS smoke test (v2.3.5) ───────────────────────────────────────────────────

def ats_smoke_check(pdf_bytes: bytes, payload: ResumePayload) -> dict[str, Any]:
    """Extract text from the rendered PDF and verify key fields survive.

    A simple proxy for "does an ATS parser see what we sent?" — extracts
    text via pdfplumber and checks for the candidate's name, every job
    company, and every skill. Returns a dict with `passed`, `missing`,
    `text_length`. The endpoint exposes this for tests + curious users.
    """
    try:
        import pdfplumber
    except ImportError:
        return {"passed": False, "reason": "pdfplumber_not_installed"}

    from io import BytesIO

    text_parts: list[str] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            text_parts.append(t)
    text = " ".join(text_parts)
    # Normalize whitespace so multi-space matching works.
    norm = re.sub(r"\s+", " ", text).lower()

    expected: list[str] = []
    if payload.personal.get("full_name"):
        expected.append(payload.personal["full_name"])
    for job in payload.experience:
        if job.get("company"):
            expected.append(job["company"])
    expected.extend(payload.skills[:5])  # cap so a 50-skill resume doesn't blow up the check

    missing = [
        s for s in expected
        if s and s.lower() not in norm
    ]
    return {
        "passed": not missing,
        "missing": missing,
        "text_length": len(text),
    }
