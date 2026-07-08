# backend/tests/test_api.py
# Exercises the FastAPI endpoints that don't need a browser, a live scrape,
# or backend/chat (local-only, not committed - see README) to run in CI.

import backend.main as main
from fastapi.testclient import TestClient

client = TestClient(main.app)


def test_hello():
    res = client.get("/api/hello")
    assert res.status_code == 200
    assert res.json() == {"message": "Hello from FastAPI!"}


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"ok": True}


def test_profile_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # never touch the real profil.json
    payload = {
        "name": "Ada Lovelace",
        "title": "Software Engineer",
        "email": "ada@example.com",
        "phone": "",
        "location": "Paris",
        "github": "",
        "summary": "",
        "skills": "",
        "experience": "",
        "education_text": "",
    }
    res = client.post("/api/profile", json=payload)
    assert res.status_code == 200
    assert res.json() == {"ok": True}

    res = client.get("/api/profile")
    assert res.status_code == 200
    assert res.json()["name"] == "Ada Lovelace"


def test_profile_empty_when_no_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    res = client.get("/api/profile")
    assert res.status_code == 200
    assert res.json() == {}


def test_likes_saves_and_dedupes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # never touch the real liked_jobs.json
    monkeypatch.setattr(main, "LIKED_FILE", tmp_path / "liked_jobs.json")

    jobs = [{"url": "https://example.com/job/1", "title": "Dev"}]
    res = client.post("/api/likes", json={"jobs": jobs})
    assert res.status_code == 200
    assert res.json() == {"saved": 1, "total": 1}

    # Posting the same URL again should not create a duplicate
    res = client.post("/api/likes", json={"jobs": jobs})
    assert res.status_code == 200
    assert res.json() == {"saved": 0, "total": 1}


def test_chat_returns_503_when_chat_module_missing():
    # backend/chat/ is local-only and not committed (see README), so in a
    # fresh CI checkout this must degrade gracefully instead of crashing.
    from pathlib import Path

    chat_dir = Path(main.__file__).parent / "chat"
    if chat_dir.exists():
        import pytest
        pytest.skip("backend/chat/ is present in this environment")

    res = client.post("/api/chat", json={"message": "hello"})
    assert res.status_code == 503
