# backend/tests/test_remote_ok.py
# Unit tests for the pure-logic helpers in the Remote OK scraper.
# No network call, no browser - safe to run in CI.

from backend.scrapers.remote_ok import tags_for, _strip_html


def test_tags_for_known_role():
    tags = tags_for("Python backend developer")
    assert tags is not None
    assert "python" in tags
    assert "backend" in tags


def test_tags_for_deduplicates_and_preserves_order():
    tags = tags_for("devops and automation")
    assert tags is not None
    assert len(tags) == len(set(tags))  # no duplicates


def test_tags_for_unknown_role_returns_none():
    assert tags_for("underwater basket weaving") is None


def test_tags_for_empty_input_returns_none():
    assert tags_for("") is None
    assert tags_for(None) is None


def test_strip_html_removes_tags_and_unescapes_entities():
    raw = "<p>Python &amp; FastAPI</p><br><span>role</span>"
    result = _strip_html(raw)
    assert "<" not in result
    assert ">" not in result
    assert "&amp;" not in result
    assert "Python & FastAPI" in result


def test_strip_html_handles_empty_input():
    assert _strip_html("") == ""
    assert _strip_html(None) == ""


def test_strip_html_collapses_blank_lines():
    raw = "line one\n\n\n\nline two"
    result = _strip_html(raw)
    assert "\n\n\n" not in result
