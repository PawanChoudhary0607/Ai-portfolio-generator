"""Unit tests for src/parsing/section_detector.py."""

from __future__ import annotations

import pytest

from src.parsing.section_detector import detect

FIXTURE = (
    "Pawan Choudhary\npawan@example.com\n\n"
    "Summary\nPassionate AI/ML engineer.\n\n"
    "Skills\nPython, Machine Learning, AWS\n\n"
    "Experience\nSoftware Engineer — Acme Corp\nJan 2023 – Present\n\n"
    "Education\nBTech CSE\nXYZ University\n\n"
    "Projects\nAI Portfolio Generator\n\n"
    "Certifications\nAWS Certified Developer\n"
)


def test_returns_all_canonical_keys():
    result = detect(FIXTURE)
    for key in ["summary", "skills", "experience", "education", "projects", "certifications"]:
        assert key in result


def test_skills_detected():
    result = detect(FIXTURE)
    assert result["skills"] is not None
    assert "Python" in result["skills"]


def test_summary_detected():
    result = detect(FIXTURE)
    assert result["summary"] is not None
    assert "AI/ML" in result["summary"]


def test_experience_detected():
    result = detect(FIXTURE)
    assert result["experience"] is not None
    assert "Acme Corp" in result["experience"]


def test_education_detected():
    result = detect(FIXTURE)
    assert result["education"] is not None
    assert "BTech" in result["education"]


def test_projects_detected():
    result = detect(FIXTURE)
    assert result["projects"] is not None
    assert "AI Portfolio" in result["projects"]


def test_certifications_detected():
    result = detect(FIXTURE)
    assert result["certifications"] is not None
    assert "AWS" in result["certifications"]


def test_missing_section_returns_none():
    result = detect("Just some plain text with no headers at all.")
    for key in ["summary", "skills", "experience", "education", "projects", "certifications"]:
        assert result[key] is None


def test_case_insensitive_headers():
    text = "SKILLS\nPython\nMachine Learning\n"
    result = detect(text)
    assert result["skills"] is not None


def test_header_with_colon():
    text = "Skills:\nPython, Docker\n"
    result = detect(text)
    assert result["skills"] is not None


def test_alternate_header_work_history():
    text = "Work History\nEngineer at Acme\n"
    result = detect(text)
    assert result["experience"] is not None


def test_alternate_header_technical_skills():
    text = "Technical Skills\nPython, AWS\n"
    result = detect(text)
    assert result["skills"] is not None


def test_no_bleed_between_sections():
    result = detect(FIXTURE)
    # Skills block should not contain experience text
    assert "Acme Corp" not in (result["skills"] or "")


def test_empty_string_returns_all_none():
    result = detect("")
    for val in result.values():
        assert val is None
