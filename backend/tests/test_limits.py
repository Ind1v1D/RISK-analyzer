import threading
import time
from types import SimpleNamespace

import pytest

from limits import AnalysisQueue, Busy, RateLimiter, RateLimitExceeded, client_id


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_requests_under_minute_limit_pass():
    rl = RateLimiter(3, 100, Clock())
    for _ in range(3):
        rl.check("a")


def test_request_over_minute_limit_is_rejected_with_retry_after():
    clock = Clock()
    rl = RateLimiter(2, 100, clock)
    rl.check("a")
    clock.now += 10
    rl.check("a")
    clock.now += 5
    with pytest.raises(RateLimitExceeded) as err:
        rl.check("a")
    assert err.value.retry_after == 45  # first hit leaves the window in 45 s


def test_minute_window_slides_so_client_can_retry_later():
    clock = Clock()
    rl = RateLimiter(1, 100, clock)
    rl.check("a")
    clock.now += 61
    rl.check("a")


def test_clients_are_limited_independently():
    rl = RateLimiter(1, 100, Clock())
    rl.check("a")
    rl.check("b")
    with pytest.raises(RateLimitExceeded):
        rl.check("a")


def test_daily_limit_is_enforced_across_minutes():
    clock = Clock()
    rl = RateLimiter(10, 3, clock)
    for _ in range(3):
        rl.check("a")
        clock.now += 120
    with pytest.raises(RateLimitExceeded) as err:
        rl.check("a")
    assert err.value.retry_after > 60


def test_daily_window_resets_after_24_hours():
    clock = Clock()
    rl = RateLimiter(10, 1, clock)
    rl.check("a")
    clock.now += 86401
    rl.check("a")


def test_rejected_attempts_do_not_extend_the_window():
    clock = Clock()
    rl = RateLimiter(1, 100, clock)
    rl.check("a")
    for _ in range(5):
        clock.now += 10
        with pytest.raises(RateLimitExceeded):
            rl.check("a")
    clock.now += 11  # 61 s after the only counted hit
    rl.check("a")


def test_limiter_is_thread_safe():
    rl = RateLimiter(50, 1000, time.time)
    ok = []

    def worker():
        for _ in range(20):
            try:
                rl.check("a")
                ok.append(1)
            except RateLimitExceeded:
                pass

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(ok) == 50


def test_queue_rejects_with_busy_when_all_slots_taken():
    q = AnalysisQueue(1, timeout=0.05)
    with q:
        with pytest.raises(Busy):
            with q:
                pass


def test_queue_slot_is_released_after_use_and_after_errors():
    q = AnalysisQueue(1, timeout=0.05)
    with pytest.raises(RuntimeError):
        with q:
            raise RuntimeError
    with q:
        pass


def test_queue_waiting_request_gets_slot_when_freed():
    q = AnalysisQueue(1, timeout=2)
    got = []
    q.__enter__()

    def waiter():
        with q:
            got.append(True)

    t = threading.Thread(target=waiter)
    t.start()
    time.sleep(0.1)
    q.__exit__(None, None, None)
    t.join()
    assert got == [True]


def _req(xff=None, host="9.9.9.9"):
    headers = {"x-forwarded-for": xff} if xff else {}
    return SimpleNamespace(headers=headers, client=SimpleNamespace(host=host))


def test_client_id_ignores_forwarded_header_by_default(monkeypatch):
    monkeypatch.delenv("TRUST_PROXY", raising=False)
    assert client_id(_req("1.1.1.1")) == "9.9.9.9"


def test_client_id_uses_last_forwarded_entry_when_proxy_trusted(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY", "1")
    monkeypatch.delenv("TRUSTED_PROXY_HOPS", raising=False)
    # the leading entry is attacker-supplied; the proxy appended the real one
    assert client_id(_req("6.6.6.6, 1.1.1.1")) == "1.1.1.1"


def test_spoofed_forwarded_header_cannot_change_identity(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY", "1")
    monkeypatch.delenv("TRUSTED_PROXY_HOPS", raising=False)
    a = client_id(_req("1.2.3.4, 7.7.7.7"))
    b = client_id(_req("5.6.7.8, 7.7.7.7"))
    assert a == b == "7.7.7.7"


def test_client_id_honours_trusted_proxy_hops(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY", "1")
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "2")
    assert client_id(_req("6.6.6.6, 1.1.1.1, 2.2.2.2")) == "1.1.1.1"


def test_client_id_uses_socket_when_header_has_too_few_entries(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY", "1")
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "2")
    assert client_id(_req("1.1.1.1")) == "9.9.9.9"


def test_client_id_falls_back_to_socket_without_header(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY", "1")
    monkeypatch.delenv("TRUSTED_PROXY_HOPS", raising=False)
    assert client_id(_req()) == "9.9.9.9"


def test_tracked_clients_are_capped_dropping_least_recently_seen():
    rl = RateLimiter(5, 50, Clock(), max_clients=3)
    for name in "abcd":
        rl.check(name)
    assert list(rl._hits) == ["b", "c", "d"]


def test_recently_seen_client_survives_eviction():
    rl = RateLimiter(5, 50, Clock(), max_clients=3)
    for name in "abc":
        rl.check(name)
    rl.check("a")  # refresh a
    rl.check("d")
    assert "a" in rl._hits and "b" not in rl._hits


def test_idle_clients_expire_after_a_day():
    clock = Clock()
    rl = RateLimiter(5, 50, clock)
    rl.check("old")
    clock.now += 86401
    rl.check("new")
    assert list(rl._hits) == ["new"]
