"""Resume builder service.

Converts structured form data (from the AI Resume Builder UI) into the same
ResumeData format produced by the file-upload parser, using Claude to fill in
any gaps and make the content richer.
"""

import json
import logging

from app.services.ai_client import call_ai
from app.services.resume_parser import (
    Education,
    Project,
    ResumeData,
    WorkExperience,
    sanitize_for_ai,  # shared prompt injection protection
)

logger = logging.getLogger(__name__)

_SYSTEM = """You are an expert resume writer and career coach. Given raw form data from a user
who is building their resume, you will produce a polished, structured JSON resume.

Your job:
1. Expand terse bullet points into concise but impactful achievement statements (start with strong action verbs, quantify where possible).
2. Write a compelling professional summary (3–4 sentences) from the user's career goal and background.
3. Ensure the output is valid JSON matching the schema exactly.

Return ONLY valid JSON — no markdown fences, no commentary."""

_SCHEMA_HINT = """{
  "full_name": "string",
  "email": null,
  "phone": null,
  "location": null,
  "linkedin_url": "string or null",
  "github_url": "string or null",
  "portfolio_url": "string or null",
  "summary": "3-4 sentence professional summary",
  "work_experience": [
    {
      "company": "string",
      "title": "string",
      "start_date": null,
      "end_date": null,
      "location": null,
      "description": ["bullet 1", "bullet 2", "..."]
    }
  ],
  "education": [
    {
      "institution": "string",
      "degree": "string",
      "field": "string or null",
      "graduation_year": "string or null",
      "gpa": null
    }
  ],
  "skills": ["skill1", "skill2"],
  "projects": [
    {
      "name": "string",
      "description": "string",
      "technologies": ["tech1", "tech2"],
      "url": "string or null"
    }
  ],
  "certifications": [],
  "languages": []
}"""


def build_resume_with_claude(form_data: dict) -> ResumeData:
    """
    Takes raw builder form data and returns a polished ResumeData object.

    form_data keys:
      personal            {name, title}
      experience_summary  {years, tech_stack: []}
      work_experiences    [{company, role, achievements}, ...]
      projects            [{name, description, tech: [], link}, ...]
      education           {degree, institution, year}
      skills              []
      social_links        {github, linkedin, website}
      career_goal         str
    """
    personal = form_data.get("personal", {})
    exp_summary = form_data.get("experience_summary", {})
    work_exps = form_data.get("work_experiences", [])
    projects = form_data.get("projects", [])
    edu = form_data.get("education", {})
    skills = form_data.get("skills", [])
    social = form_data.get("social_links", {})
    career_goal = form_data.get("career_goal", "")

    # Sanitize all free-text fields before embedding in the prompt.
    # Users can type anything into achievement/description fields; we must prevent
    # them from injecting instructions that override the resume-writer system prompt.
    sanitized_achievements = [
        {
            **w,
            "achievements": sanitize_for_ai(w.get("achievements", ""), source="achievements"),
            "company": sanitize_for_ai(w.get("company", ""), source="company"),
            "role": sanitize_for_ai(w.get("role", ""), source="role"),
        }
        for w in work_exps
    ]
    sanitized_projects = [
        {
            **p,
            "name": sanitize_for_ai(p.get("name", ""), source="project_name"),
            "description": sanitize_for_ai(p.get("description", ""), source="project_desc"),
        }
        for p in projects
    ]
    sanitized_career_goal = sanitize_for_ai(career_goal, source="career_goal")
    sanitized_name = sanitize_for_ai(personal.get("name", ""), source="name")
    sanitized_title = sanitize_for_ai(personal.get("title", ""), source="title")

    user_prompt = f"""Here is the form data collected from the user:

NAME: {sanitized_name}
CURRENT TITLE: {sanitized_title}
YEARS OF EXPERIENCE: {exp_summary.get('years', '')}
PRIMARY TECH STACK: {', '.join(exp_summary.get('tech_stack', []))}

WORK EXPERIENCES:
{chr(10).join(
    f"  [{i+1}] Company: {w.get('company','')} | Role: {w.get('role','')}\\n      Achievements: {w.get('achievements','')}"
    for i, w in enumerate(sanitized_achievements) if w.get('company')
)}

PROJECTS:
{chr(10).join(
    f"  [{i+1}] {p.get('name','')} — {p.get('description','')} | Tech: {', '.join(p.get('tech',[]))} | Link: {p.get('link','')}"
    for i, p in enumerate(sanitized_projects) if p.get('name')
)}

EDUCATION: {edu.get('degree','')} from {edu.get('institution','')} ({edu.get('year','')})

SKILLS: {', '.join(skills)}

SOCIAL LINKS:
  GitHub: {social.get('github','')}
  LinkedIn: {social.get('linkedin','')}
  Website: {social.get('website','')}

CAREER GOAL: {sanitized_career_goal}

Output schema to match:
{_SCHEMA_HINT}

Produce the polished resume JSON now."""

    try:
        raw = call_ai(prompt=user_prompt, system=_SYSTEM, max_tokens=4096)
        # Strip accidental markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip().rstrip("`")

        data = json.loads(raw)
        return ResumeData(**data)

    except Exception as exc:
        logger.warning("Claude resume build failed, using fallback: %s", exc)
        # Return best-effort ResumeData from raw form fields
        return _fallback_resume_data(form_data)


def _fallback_resume_data(form_data: dict) -> ResumeData:
    personal = form_data.get("personal", {})
    exp_summary = form_data.get("experience_summary", {})
    work_exps = form_data.get("work_experiences", [])
    projects_raw = form_data.get("projects", [])
    edu = form_data.get("education", {})
    skills = form_data.get("skills", [])
    social = form_data.get("social_links", {})
    career_goal = form_data.get("career_goal", "")

    all_skills = list(set(skills + exp_summary.get("tech_stack", [])))

    return ResumeData(
        full_name=personal.get("name"),
        linkedin_url=social.get("linkedin"),
        github_url=social.get("github"),
        portfolio_url=social.get("website"),
        summary=career_goal or None,
        work_experience=[
            WorkExperience(
                company=w.get("company", ""),
                title=w.get("role", ""),
                description=[w.get("achievements", "")],
            )
            for w in work_exps
            if w.get("company")
        ],
        education=[
            Education(
                institution=edu.get("institution", ""),
                degree=edu.get("degree", ""),
                graduation_year=str(edu.get("year", "")),
            )
        ] if edu.get("institution") else [],
        skills=all_skills,
        projects=[
            Project(
                name=p.get("name", ""),
                description=p.get("description", ""),
                technologies=p.get("tech", []),
                url=p.get("link") or None,
            )
            for p in projects_raw
            if p.get("name")
        ],
    )
