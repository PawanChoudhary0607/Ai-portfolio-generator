"""Unit tests for src/parsing/normalizer.py."""

from __future__ import annotations

from src.parsing.normalizer import clean_list, clean_skills, clean_text


# ── clean_text ────────────────────────────────────────────────────────────────

def test_clean_text_strips_whitespace():
    assert clean_text("  hello  ") == "hello"


def test_clean_text_none_returns_none():
    assert clean_text(None) is None


def test_clean_text_empty_string_returns_none():
    assert clean_text("   ") is None


def test_clean_text_replaces_fi_ligature():
    assert clean_text("pro\ufb01le") == "profile"


def test_clean_text_replaces_fl_ligature():
    assert clean_text("\ufb02ow") == "flow"


def test_clean_text_replaces_en_dash():
    assert clean_text("2022\u20132023") == "2022-2023"


def test_clean_text_replaces_non_breaking_space():
    assert clean_text("hello\u00a0world") == "hello world"


def test_clean_text_replaces_curly_quotes():
    assert clean_text("\u2018hello\u2019") == "'hello'"


# ── clean_skills ──────────────────────────────────────────────────────────────

def test_clean_skills_deduplicates_case_insensitive():
    result = clean_skills(["Python", "python", "PYTHON"])
    assert result == ["Python"]


def test_clean_skills_preserves_canonical_capitalisation():
    result = clean_skills(["AWS", "aws"])
    assert result == ["AWS"]


def test_clean_skills_removes_empty_strings():
    result = clean_skills(["Python", "", "  ", "Docker"])
    assert "" not in result
    assert "  " not in result
    assert "Python" in result
    assert "Docker" in result


def test_clean_skills_preserves_order_first_occurrence_wins():
    result = clean_skills(["React", "FastAPI", "react"])
    assert result.index("React") < result.index("FastAPI")
    assert "react" not in result


def test_clean_skills_empty_list():
    assert clean_skills([]) == []


def test_clean_skills_mixed_capitalisation():
    result = clean_skills(["machine learning", "Machine Learning"])
    assert len(result) == 1
    assert result[0] == "machine learning"


# ── clean_list ────────────────────────────────────────────────────────────────

def test_clean_list_strips_items():
    assert clean_list(["  a  ", "b "]) == ["a", "b"]


def test_clean_list_removes_empty():
    assert clean_list(["a", "", "  ", "b"]) == ["a", "b"]


def test_clean_list_empty_input():
    assert clean_list([]) == []
