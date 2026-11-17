import threading
import time

import pytest
from fastapi.testclient import TestClient

import main
from analysis import AnalysisError
from limits import AnalysisQueue, RateLimiter
from messages import msg
from prompts import ClauseFlag, ContractSummary

CONTRACT = "The Contractor shall deliver the work. Payment is due within 90 days of invoice. " * 2

SUMMARY = ContractSummary(
    contract_type="Freelance services agreement",
    parties=["Acme Ltd", "Jane Doe"],
    overview="Jane builds a website for Acme.",
    key_terms=["Payment in 90 days"],
)
FLAGS = [
    ClauseFlag(
        clause_text="Payment is due within 90 days of invoice.",
        risk_level="Medium",
        explanation="Slow.",
    )
]


@pytest.fixture(autouse=True)
def fresh_limits(monkeypatch):
    monkeypatch.setattr(main, "rate_limiter", RateLimiter(100, 1000))
    monkeypatch.setattr(main, "analysis_queue", AnalysisQueue(2, 0.1))


@pytest.fixture
def ok_analysis(monkeypatch):
    calls = []

    def fake(text, lang="en"):
        calls.append((text, lang))
        return SUMMARY, FLAGS

    monkeypatch.setattr(main, "analyze_contract", fake)
    return calls


@pytest.fixture
def client():
    return TestClient(main.app)


def test_health_returns_ok(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_config_exposes_public_limits(client):
    body = client.get("/api/config").json()
    assert body == {"max_file_mb": 10, "max_chars": main.MAX_CHARS, "max_flags": 12}


def test_sample_returns_demo_contract(client):
    r = client.get("/api/sample")
    assert r.status_code == 200 and len(r.json()["text"]) > 100


def test_unknown_api_route_is_404(client):
    assert client.get("/api/nope").status_code == 404


def test_pasted_text_analysis_returns_full_contract_shape(client, ok_analysis):
    r = client.post("/api/analyze", data={"text": CONTRACT, "lang": "en"})
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"full_text", "summary", "flags"}
    assert body["full_text"] == CONTRACT.strip()
    assert body["summary"] == {
        "contract_type": "Freelance services agreement",
        "parties": ["Acme Ltd", "Jane Doe"],
        "overview": "Jane builds a website for Acme.",
        "key_terms": ["Payment in 90 days"],
    }
    assert body["flags"] == [
        {
            "clause_text": "Payment is due within 90 days of invoice.",
            "risk_level": "Medium",
            "explanation": "Slow.",
        }
    ]


def test_language_is_passed_to_analysis(client, ok_analysis):
    client.post("/api/analyze", data={"text": CONTRACT, "lang": "kk"})
    assert ok_analysis[0][1] == "kk"


def test_txt_upload_is_analyzed(client, ok_analysis):
    r = client.post("/api/analyze", files={"file": ("c.txt", CONTRACT.encode(), "text/plain")})
    assert r.status_code == 200


def test_no_input_returns_400(client):
    r = client.post("/api/analyze", data={"lang": "en"})
    assert r.status_code == 400
    assert r.json()["detail"] == msg("no_input", "en")


def test_blank_text_returns_400(client):
    assert client.post("/api/analyze", data={"text": "   "}).status_code == 400


def test_too_short_pasted_text_returns_400(client, ok_analysis):
    r = client.post("/api/analyze", data={"text": "hi there", "lang": "en"})
    assert r.status_code == 400
    assert r.json()["detail"] == msg("text_too_short", "en")
    assert ok_analysis == []


def test_too_long_text_returns_413(client, ok_analysis):
    r = client.post("/api/analyze", data={"text": "a" * (main.MAX_CHARS + 1)})
    assert r.status_code == 413


def test_unsupported_file_returns_400(client):
    r = client.post(
        "/api/analyze", files={"file": ("x.exe", b"MZ" * 50, "application/octet-stream")}
    )
    assert r.status_code == 400
    assert "exe" in r.json()["detail"]


def test_oversize_file_returns_413(client, monkeypatch):
    monkeypatch.setattr(main, "MAX_FILE_BYTES", 1000)
    r = client.post("/api/analyze", files={"file": ("big.txt", b"a" * 1001, "text/plain")})
    assert r.status_code == 413


def test_file_exactly_at_limit_is_accepted(client, ok_analysis, monkeypatch):
    content = (CONTRACT * 5).encode()[:1000]
    monkeypatch.setattr(main, "MAX_FILE_BYTES", len(content))
    r = client.post("/api/analyze", files={"file": ("ok.txt", content, "text/plain")})
    assert r.status_code == 200


def test_rate_limit_returns_429_with_retry_after(client, ok_analysis, monkeypatch):
    monkeypatch.setattr(main, "rate_limiter", RateLimiter(2, 1000))
    for _ in range(2):
        assert client.post("/api/analyze", data={"text": CONTRACT}).status_code == 200
    r = client.post("/api/analyze", data={"text": CONTRACT})
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) >= 1
    assert r.json()["detail"]


def test_validation_failures_do_not_count_against_rate_limit(client, ok_analysis, monkeypatch):
    monkeypatch.setattr(main, "rate_limiter", RateLimiter(1, 1000))
    for _ in range(3):
        assert client.post("/api/analyze", data={"lang": "en"}).status_code == 400
    assert client.post("/api/analyze", data={"text": CONTRACT}).status_code == 200


def test_ai_quota_error_returns_429_with_retry_after(client, monkeypatch):
    def boom(text, lang="en"):
        raise AnalysisError(msg("ai_quota", lang), status=429, retry_after=60)

    monkeypatch.setattr(main, "analyze_contract", boom)
    r = client.post("/api/analyze", data={"text": CONTRACT})
    assert r.status_code == 429
    assert r.headers["Retry-After"] == "60"
    assert r.json()["detail"] == msg("ai_quota", "en")


def test_ai_failure_returns_502_with_generic_message(client, monkeypatch):
    def boom(text, lang="en"):
        raise AnalysisError(msg("ai_failed", lang))

    monkeypatch.setattr(main, "analyze_contract", boom)
    r = client.post("/api/analyze", data={"text": CONTRACT})
    assert r.status_code == 502
    assert r.json()["detail"] == msg("ai_failed", "en")


@pytest.mark.parametrize("lang", ["ru", "kk"])
def test_errors_are_translated(client, lang):
    r = client.post("/api/analyze", data={"lang": lang})
    assert r.json()["detail"] == msg("no_input", lang)
    assert r.json()["detail"] != msg("no_input", "en")


def _slow_analysis(monkeypatch):
    release = threading.Event()
    started = threading.Event()

    def slow(text, lang="en"):
        started.set()
        release.wait(5)
        return SUMMARY, FLAGS

    monkeypatch.setattr(main, "analyze_contract", slow)
    return started, release


def test_server_busy_returns_503_when_queue_is_full(client, monkeypatch):
    started, release = _slow_analysis(monkeypatch)
    monkeypatch.setattr(main, "analysis_queue", AnalysisQueue(1, 0.1))

    first = {}
    t = threading.Thread(
        target=lambda: first.update(r=client.post("/api/analyze", data={"text": CONTRACT}))
    )
    t.start()
    assert started.wait(3)
    r = client.post("/api/analyze", data={"text": CONTRACT, "lang": "ru"})
    release.set()
    t.join()
    assert r.status_code == 503
    assert r.json()["detail"] == msg("server_busy", "ru")
    assert first["r"].status_code == 200


def test_health_stays_responsive_during_analysis(client, monkeypatch):
    started, release = _slow_analysis(monkeypatch)
    t = threading.Thread(target=lambda: client.post("/api/analyze", data={"text": CONTRACT}))
    t.start()
    assert started.wait(3)
    t0 = time.time()
    assert TestClient(main.app).get("/api/health").status_code == 200
    assert time.time() - t0 < 1
    release.set()
    t.join()


@pytest.mark.skipif(not (main.DIST_DIR / "index.html").is_file(), reason="frontend not built")
def test_built_frontend_is_served_at_root_and_as_spa_fallback(client):
    assert "<html" in client.get("/").text.lower()
    assert "<html" in client.get("/some/client/route").text.lower()
    assert "FastAPI(" not in client.get("/%2e%2e/backend/main.py").text


# ---- body size limit, CORS, rate-limit ordering, static --------------------------

def test_declared_oversize_body_is_rejected_with_translated_413(client):
    big = b"a" * (main.MAX_FILE_BYTES + main.BODY_OVERHEAD_BYTES + 10)
    r = client.post("/api/analyze?lang=ru", files={"file": ("big.txt", big, "text/plain")})
    assert r.status_code == 413
    assert r.json()["detail"] == msg("file_too_large", "ru")


def test_streamed_body_without_content_length_is_stopped_at_limit(client, monkeypatch):
    monkeypatch.setattr(main, "MAX_FILE_BYTES", 1000)
    monkeypatch.setattr(main, "BODY_OVERHEAD_BYTES", 1000)

    def chunks():
        for _ in range(50):
            yield b"x" * 1000

    r = client.post(
        "/api/analyze", content=chunks(), headers={"content-type": "multipart/form-data; boundary=zz"}
    )
    assert r.status_code == 413
    assert r.json()["detail"] == msg("file_too_large", "en")


def test_body_limit_does_not_affect_other_routes(client):
    assert client.get("/api/health").status_code == 200


def test_cors_exposes_retry_after_header(client):
    r = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert "Retry-After" in r.headers["access-control-expose-headers"]


def test_upload_is_rate_limited_before_parsing(client, monkeypatch):
    monkeypatch.setattr(main, "rate_limiter", RateLimiter(1, 1000))
    parsed = []
    monkeypatch.setattr(main, "extract_text", lambda name, content: parsed.append(name) or CONTRACT)
    monkeypatch.setattr(main, "analyze_contract", lambda t, l="en": (SUMMARY, FLAGS))
    files = {"file": ("c.txt", b"data", "text/plain")}
    assert client.post("/api/analyze", files=files).status_code == 200
    r = client.post("/api/analyze", files=files)
    assert r.status_code == 429
    assert parsed == ["c.txt"]  # second upload never reached the parser


def test_failed_upload_parsing_still_counts_as_a_hit(client, monkeypatch):
    monkeypatch.setattr(main, "rate_limiter", RateLimiter(1, 1000))
    files = {"file": ("x.exe", b"MZ" * 50, "application/octet-stream")}
    assert client.post("/api/analyze", files=files).status_code == 400
    assert client.post("/api/analyze", files=files).status_code == 429


def test_rate_limited_message_has_no_embedded_seconds(client, ok_analysis, monkeypatch):
    monkeypatch.setattr(main, "rate_limiter", RateLimiter(1, 1000))
    client.post("/api/analyze", data={"text": CONTRACT})
    r = client.post("/api/analyze", data={"text": CONTRACT, "lang": "ru"})
    assert r.json()["detail"] == msg("rate_limited", "ru")


def test_missing_api_key_returns_503_generic_message(client, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY")
    r = client.post("/api/analyze", data={"text": CONTRACT})
    assert r.status_code == 503
    assert ".env" not in r.json()["detail"]


_has_dist = (main.DIST_DIR / "index.html").is_file()


@pytest.mark.skipif(not _has_dist, reason="frontend not built")
def test_missing_asset_returns_404_not_index_html(client):
    assert client.get("/assets/does-not-exist.js").status_code == 404
    assert client.get("/missing.png").status_code == 404


@pytest.mark.skipif(not _has_dist, reason="frontend not built")
def test_existing_asset_is_served_with_immutable_cache_header(client):
    assets = sorted((main.DIST_DIR / "assets").glob("*.*"))
    if not assets:
        pytest.skip("no built assets")
    r = client.get(f"/assets/{assets[0].name}")
    assert r.status_code == 200
    assert "immutable" in r.headers["cache-control"]
