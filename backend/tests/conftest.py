import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def _no_real_gemini(monkeypatch):
    """Safety net: tests must never reach the real API or sleep on retries."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    import analysis

    monkeypatch.setattr(analysis.time, "sleep", lambda s: None)
