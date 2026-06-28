"""Prompt builder — converts ResumeSchema into a structured Ollama prompt.

Rules enforced by this module:
- The model is instructed to return JSON only.
- No markdown fences, no prose, no explanation outside the JSON object.
- Every required AIAnalysisSchema field is explicitly named in the prompt.
"""

from __future__ import annotations

from src.schemas.resume import ResumeSchema


_SYSTEM_INSTRUCTIONS = """\
You are a professional resume analyst and career advisor.
Analyze the resume data provided and return a JSON object only.
Do not include markdown, code fences, explanations, or any text outside the JSON.
The response must be a single valid JSON object with exactly these keys:
- strengths: list of strings (what the candidate does well)
- weaknesses: list of strings (areas that need improvement)
- missing_skills: list of strings (skills absent but expected for their level)
- recommended_projects: list of strings (specific project ideas to strengthen portfolio)
- recommended_career_paths: list of strings (realistic career directions)
- portfolio_sections: list of strings (sections to include in their portfolio)
- summary: string (a professional third-person summary paragraph)

Every key must be present. Lists must contain at least one item. Summary must be non-empty.
Return only the JSON object. Nothing else.\
"""


def _format_resume(resume: ResumeSchema) -> str:
    """Render a ResumeSchema as plain text for embedding in the prompt."""
    lines: list[str] = []

    if resume.personal:
        if resume.personal.name:
            lines.append(f"Name: {resume.personal.name}")
        if resume.personal.email:
            lines.append(f"Email: {resume.personal.email}")
        if resume.personal.location:
            lines.append(f"Location: {resume.personal.location}")
        if resume.personal.linkedin:
            lines.append(f"LinkedIn: {resume.personal.linkedin}")

    if resume.summary:
        lines.append(f"\nSummary:\n{resume.summary}")

    if resume.skills:
        lines.append(f"\nSkills:\n{', '.join(resume.skills)}")

    if resume.experience_raw:
        lines.append(f"\nExperience:\n{resume.experience_raw}")

    if resume.education_raw:
        lines.append(f"\nEducation:\n{resume.education_raw}")

    if resume.projects_raw:
        lines.append(f"\nProjects:\n{resume.projects_raw}")

    if resume.certifications_raw:
        lines.append(f"\nCertifications:\n{resume.certifications_raw}")

    if resume.raw_text and not lines:
        # Fallback: no structured fields parsed — send raw text
        lines.append(f"Resume Text:\n{resume.raw_text}")

    return "\n".join(lines)


def build_prompt(resume: ResumeSchema) -> str:
    """Build the full prompt string to send to Ollama.

    Returns a single string combining system instructions and resume data.
    """
    resume_text = _format_resume(resume)

    return f"""{_SYSTEM_INSTRUCTIONS}

---RESUME DATA---
{resume_text}
---END RESUME---

Return the JSON object now:"""
