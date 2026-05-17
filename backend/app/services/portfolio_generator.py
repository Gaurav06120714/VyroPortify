"""Portfolio generation service.

Two classes:
  ContentEnhancer  — calls Claude to generate taglines, about text, enhanced descriptions
  TemplateInjector — renders a Jinja2 HTML template with parsed + enhanced data
"""

import json
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.security_config import security_settings
from app.services.ai_client import call_ai

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

_ENHANCE_SYSTEM = """You are a world-class copywriter specializing in personal branding for tech professionals.
Given parsed resume data, generate enhanced portfolio content.
Return ONLY valid JSON — no markdown, no code fences, no explanation.

Generate these fields:
{
  "hero_tagline": "A punchy 8-12 word tagline that captures the person's unique value (e.g. 'Building scalable systems that serve millions of users')",
  "hero_description": "2-sentence value proposition highlighting what makes them stand out",
  "about_paragraph": "4-sentence personal story: who they are, what drives them, what they build, what they're looking for",
  "title": "Clean professional title if not already strong (e.g. 'Full Stack Engineer' or 'Senior Backend Developer')"
}

Rules:
- Use the person's actual experience and skills — don't invent things
- Be specific, not generic ("reduced API latency by 40%" not "improved performance")
- Professional yet personable tone
- Show impact and technical depth"""


class ContentEnhancer:
    """Calls Claude to generate enhanced portfolio copy from parsed resume data."""

    def enhance(self, parsed_data: dict) -> dict:
        """Generate enhanced content fields for a portfolio.

        Args:
            parsed_data: ResumeData dict (from resume_parser).

        Returns:
            Dict with hero_tagline, hero_description, about_paragraph, title.
            Falls back to safe defaults on failure — never raises.
        """
        # Serialize and truncate parsed_data before embedding in the prompt.
        # Resume data originates from user-uploaded files or form input — either
        # can contain crafted text designed to hijack the AI system prompt.
        raw_json = json.dumps(parsed_data, indent=2)
        max_len = security_settings.MAX_TEXT_LENGTH_FOR_AI
        if len(raw_json) > max_len:
            logger.warning(
                "ContentEnhancer: truncating parsed_data JSON from %d to %d chars",
                len(raw_json),
                max_len,
            )
            raw_json = raw_json[:max_len]

        try:
            text = call_ai(
                prompt=f"Enhance this resume data:\n\n{raw_json}",
                system=_ENHANCE_SYSTEM,
                max_tokens=1024,
            )
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            return json.loads(text)
        except Exception as exc:
            logger.warning("ContentEnhancer failed (using fallbacks): %s", exc)
            return {
                "hero_tagline": parsed_data.get("summary", "")[:80] if parsed_data.get("summary") else "",
                "hero_description": parsed_data.get("summary", ""),
                "about_paragraph": parsed_data.get("summary", ""),
                "title": parsed_data.get("title", "Software Engineer"),
                "_ai_failed": True,
            }


class TemplateInjector:
    """Renders a Jinja2 portfolio template with parsed + enhanced data."""

    def __init__(self) -> None:
        self._envs: dict[str, Environment] = {}

    def _get_env(self, template_id: str) -> Environment:
        if template_id not in self._envs:
            template_dir = _TEMPLATES_DIR / template_id
            if not template_dir.exists():
                raise ValueError(f"Template '{template_id}' not found at {template_dir}")
            self._envs[template_id] = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=select_autoescape(["html"]),
            )
        return self._envs[template_id]

    def inject(self, template_id: str, parsed_data: dict, enhanced: dict) -> str:
        """Render the template with resume + enhanced data merged.

        Args:
            template_id: 'aurora' | 'minimal' | 'cyber'
            parsed_data:  ResumeData as dict
            enhanced:     ContentEnhancer output dict

        Returns:
            Rendered HTML string.
        """
        env = self._get_env(template_id)
        tmpl = env.get_template("template.html")

        # Merge: enhanced fields override parsed where both exist
        ctx = {**parsed_data}
        for key, val in enhanced.items():
            if val:
                ctx[key] = val

        # Normalise nested objects to plain dicts for Jinja2
        ctx = _normalise(ctx)
        return tmpl.render(**ctx)


def _normalise(obj):
    """Recursively convert Pydantic models / objects to plain dicts/lists."""
    if hasattr(obj, "model_dump"):
        return _normalise(obj.model_dump())
    if isinstance(obj, dict):
        return {k: _normalise(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalise(i) for i in obj]
    return obj


# Module-level singletons
content_enhancer = ContentEnhancer()
template_injector = TemplateInjector()
