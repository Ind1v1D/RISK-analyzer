import json
from types import SimpleNamespace

import pytest
from google.genai import errors as genai_errors

import analysis
from analysis import AnalysisError, _is_fallback_worthy, _is_quota, _is_transient, _parse, _postprocess
from prompts import MAX_FLAGS, AnalysisResult, ClauseFlag, ContractSummary, build_system_prompt


def flag(text, level="Medium", why="because"):
    return ClauseFlag(clause_text=text, risk_level=level, explanation=why)


def api_error(code, status="X"):
    return genai_errors.APIError(
        code, {"error": {"code": code, "status": status, "message": "boom 500 429"}}
    )


SUMMARY = {"contract_type": "T", "parties": ["A"], "overview": "o", "key_terms": ["k"]}


# ---- _postprocess -------------------------------------------------------------

def test_duplicates_keep_most_severe_flag():
    out = _postprocess([flag("Pay later", "Low"), flag("pay  LATER", "High")])
    assert len(out) == 1 and out[0].risk_level == "High"


def test_empty_excerpts_are_dropped():
    assert _postprocess([flag("   ")]) == []


def test_order_is_severity_then_position_in_contract():
    text = "alpha clause. beta clause. gamma clause. delta clause."
    flags = [
        flag("delta clause.", "Low"), flag("gamma clause.", "High"),
        flag("alpha clause.", "Low"), flag("beta clause.", "High"),
    ]
    out = _postprocess(flags, text)
    assert [f.clause_text for f in out] == [
        "beta clause.", "gamma clause.", "alpha clause.", "delta clause."
    ]


def test_result_does_not_depend_on_model_listing_order():
    text = "one. two. three."
    a = [flag("one.", "High"), flag("two.", "High"), flag("three.", "Medium")]
    assert _postprocess(a, text) == _postprocess(list(reversed(a)), text)


def test_cap_keeps_most_serious_flags():
    flags = [flag(f"low {i}", "Low") for i in range(MAX_FLAGS)] + [flag("the big one", "High")]
    out = _postprocess(flags)
    assert len(out) == MAX_FLAGS
    assert out[0].clause_text == "the big one"


def test_prompt_and_cap_use_same_limit():
    assert f"at most {MAX_FLAGS} flags" in build_system_prompt("en")
    assert MAX_FLAGS == 12


# ---- _parse -------------------------------------------------------------------

def test_missing_summary_defaults_to_empty_summary():
    result = _parse(SimpleNamespace(parsed=None, text=json.dumps({"flags": []})))
    assert result.summary == ContractSummary()


def test_parse_uses_sdk_parsed_object():
    parsed = AnalysisResult(summary=ContractSummary(**SUMMARY), flags=[])
    assert _parse(SimpleNamespace(parsed=parsed, text=None)) is parsed


def test_parse_reads_raw_json_text():
    raw = json.dumps(
        {"summary": SUMMARY, "flags": [{"clause_text": "x", "risk_level": "Low", "explanation": "y"}]}
    )
    result = _parse(SimpleNamespace(parsed=None, text=raw))
    assert result.flags[0].clause_text == "x"


def test_parse_empty_response_raises_analysis_error():
    with pytest.raises(AnalysisError):
        _parse(SimpleNamespace(parsed=None, text=""))


@pytest.mark.parametrize(
    "raw", ["not json", json.dumps({"flags": "nope"}), json.dumps({"summary": SUMMARY})]
)
def test_parse_invalid_output_raises_analysis_error(raw):
    with pytest.raises(AnalysisError):
        _parse(SimpleNamespace(parsed=None, text=raw))


# ---- status-code classification ----------------------------------------------

@pytest.mark.parametrize("code", [429, 500, 503])
def test_retryable_codes_are_transient(code):
    assert _is_transient(api_error(code))


@pytest.mark.parametrize("code", [400, 401, 403, 404])
def test_client_errors_are_not_transient(code):
    assert not _is_transient(api_error(code))


def test_digits_in_error_text_do_not_cause_false_match():
    # message contains "500" and "429" but the structured status is 400
    assert not _is_transient(api_error(400))


def test_quota_detected_from_429_code():
    assert _is_quota(api_error(429, "RESOURCE_EXHAUSTED"))
    assert not _is_quota(api_error(503, "UNAVAILABLE"))


def test_404_is_fallback_worthy_but_not_retried():
    err = api_error(404, "NOT_FOUND")
    assert _is_fallback_worthy(err) and not _is_transient(err)


def test_auth_error_is_not_fallback_worthy():
    assert not _is_fallback_worthy(api_error(403, "PERMISSION_DENIED"))


def test_network_timeout_without_status_is_transient():
    assert _is_transient(TimeoutError("read timed out"))
    assert _is_transient(RuntimeError("connection reset by peer"))


def test_random_exception_with_digits_is_not_transient():
    assert not _is_transient(ValueError("bad value 500 items"))


# ---- fallback model selection --------------------------------------------------

def _client(*names):
    entries = [SimpleNamespace(name=f"models/{n}", supported_actions=["generateContent"]) for n in names]
    return SimpleNamespace(models=SimpleNamespace(list=lambda: entries))


def test_fallback_skips_preview_and_experimental_models():
    c = _client(
        "gemini-3.6-flash-lite-preview", "gemini-3.6-flash-exp", "gemini-3.6-flash-tts",
        "gemini-3.6-flash-image", "gemini-3.6-flash-live", "gemini-3.5-flash",
    )
    assert analysis._pick_fallback_model(c) == "gemini-3.5-flash"


def test_fallback_prefers_lite_and_is_deterministic():
    names = ["gemini-3.6-flash-lite-b", "gemini-3.6-flash-lite-a", "gemini-3.6-flash-x"]
    assert analysis._pick_fallback_model(_client(*names)) == "gemini-3.6-flash-lite-a"
    assert analysis._pick_fallback_model(_client(*reversed(names))) == "gemini-3.6-flash-lite-a"


def test_fallback_none_when_only_unstable_models():
    assert analysis._pick_fallback_model(_client("gemini-x-preview")) is None


# ---- analyze_contract error mapping ---------------------------------------------

class FakeModels:
    def __init__(self, error, listing=()):
        self.error = error
        self.calls = 0
        self.models_called = []
        self.listing = list(listing)

    def generate_content(self, **kw):
        self.calls += 1
        self.models_called.append(kw["model"])
        raise self.error

    def list(self):
        return self.listing


def _patch_client(monkeypatch, exc, listing=()):
    models = FakeModels(exc, listing)
    monkeypatch.setattr(
        analysis.genai, "Client", lambda api_key, **kw: SimpleNamespace(models=models, kw=kw)
    )
    return models


def test_persistent_429_becomes_quota_error_with_retry_after(monkeypatch):
    models = _patch_client(monkeypatch, api_error(429, "RESOURCE_EXHAUSTED"))
    with pytest.raises(AnalysisError) as err:
        analysis.analyze_contract("text", "en")
    assert err.value.status == 429 and err.value.retry_after
    assert models.calls == 1  # no backoff retries on quota


def test_persistent_503_becomes_generic_502(monkeypatch):
    _patch_client(monkeypatch, api_error(503, "UNAVAILABLE"))
    with pytest.raises(AnalysisError) as err:
        analysis.analyze_contract("text", "en")
    assert err.value.status == 502


def test_raw_gemini_error_text_is_never_shown_to_user(monkeypatch):
    _patch_client(monkeypatch, api_error(400, "INVALID_ARGUMENT"))
    with pytest.raises(AnalysisError) as err:
        analysis.analyze_contract("text", "en")
    assert "boom" not in str(err.value)
    assert "APIError" not in str(err.value)


def test_permanent_error_is_not_retried(monkeypatch):
    models = _patch_client(monkeypatch, api_error(400, "INVALID_ARGUMENT"))
    with pytest.raises(AnalysisError):
        analysis.analyze_contract("text", "en")
    assert models.calls == 1


def test_error_details_are_logged_server_side(monkeypatch, caplog):
    _patch_client(monkeypatch, api_error(400, "INVALID_ARGUMENT"))
    with caplog.at_level("ERROR", logger="clausecheck.analysis"):
        with pytest.raises(AnalysisError):
            analysis.analyze_contract("text", "en")
    assert "boom" in caplog.text


def test_missing_api_key_gives_error(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY")
    with pytest.raises(AnalysisError) as err:
        analysis.analyze_contract("text", "ru")
    assert "GEMINI_API_KEY" not in str(err.value)


def _lite_listing():
    return [SimpleNamespace(name="models/gemini-3.6-flash-lite", supported_actions=["generateContent"])]


def test_quota_tries_fallback_model_exactly_once_without_backoff(monkeypatch):
    sleeps = []
    monkeypatch.setattr(analysis.time, "sleep", sleeps.append)
    models = _patch_client(monkeypatch, api_error(429, "RESOURCE_EXHAUSTED"), _lite_listing())
    with pytest.raises(AnalysisError) as err:
        analysis.analyze_contract("text", "en")
    assert err.value.status == 429
    assert models.models_called == [analysis.MODEL, "gemini-3.6-flash-lite"]
    assert sleeps == []


def test_503_is_retried_with_backoff_on_same_model(monkeypatch):
    sleeps = []
    monkeypatch.setattr(analysis.time, "sleep", sleeps.append)
    models = _patch_client(monkeypatch, api_error(503, "UNAVAILABLE"))
    with pytest.raises(AnalysisError):
        analysis.analyze_contract("text", "en")
    assert models.calls == analysis.MAX_ATTEMPTS
    assert sleeps == [2, 4, 8]


def test_client_is_created_with_http_timeout_in_milliseconds(monkeypatch):
    seen = {}

    def factory(api_key, **kw):
        seen.update(kw)
        return SimpleNamespace(models=FakeModels(api_error(400)))

    monkeypatch.setattr(analysis.genai, "Client", factory)
    with pytest.raises(AnalysisError):
        analysis.analyze_contract("text", "en")
    assert seen["http_options"].timeout == int(analysis.GEMINI_TIMEOUT_SECONDS * 1000)


def test_retries_stop_when_deadline_has_no_room(monkeypatch):
    monkeypatch.setattr(analysis, "ANALYSIS_DEADLINE_SECONDS", 11)
    sleeps = []
    monkeypatch.setattr(analysis.time, "sleep", sleeps.append)
    models = _patch_client(monkeypatch, api_error(503, "UNAVAILABLE"))
    with pytest.raises(AnalysisError) as err:
        analysis.analyze_contract("text", "en")
    assert err.value.status == 502
    assert models.calls == 1 and sleeps == []


def test_total_budget_stays_below_frontend_timeout():
    assert analysis.ANALYSIS_DEADLINE_SECONDS + 30 < 150


def test_call_timeout_never_exceeds_remaining_budget():
    seen = []

    class M:
        def generate_content(self, **kw):
            seen.append(kw["config"].http_options.timeout)
            raise api_error(400)

    analysis._generate(SimpleNamespace(models=M()), "m", "t", "en", analysis.time.monotonic() + 20)
    assert seen and seen[0] <= 20_000


def test_missing_api_key_message_is_generic_and_hint_is_logged(monkeypatch, caplog):
    monkeypatch.delenv("GEMINI_API_KEY")
    with caplog.at_level("ERROR", logger="clausecheck.analysis"):
        with pytest.raises(AnalysisError) as err:
            analysis.analyze_contract("text", "en")
    assert ".env" not in str(err.value)
    assert "GEMINI_API_KEY" in caplog.text
