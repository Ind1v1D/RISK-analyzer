"""Per-client rate limiting and the Gemini concurrency queue (TD-4).

Everything is in-memory and per server process: fine for a single-instance MVP
deployment, but counters reset on restart and are not shared between workers.

Counting policy:
  * File uploads are counted BEFORE parsing (parsing a 10 MB PDF is expensive),
    so even uploads that later fail with 400/413 use up one hit.
  * Pasted text is counted only after it passed validation (not empty, long
    enough, not too long), so a user fixing a typo is not punished.
  * Requests rejected by the body-size middleware or with "no input" are free.
Memory is bounded: at most MAX_TRACKED_CLIENTS clients are remembered (least
recently seen are dropped first), and idle clients expire after a day.
"""

import math
import os
import threading
import time
from collections import OrderedDict, deque
from typing import Callable

from dotenv import load_dotenv
from fastapi import Request

load_dotenv()  # limits are read from env at import time


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = max(1, int(retry_after))
        super().__init__(f"rate limit exceeded, retry in {self.retry_after}s")


class RateLimiter:
    """Sliding-window limiter: `per_minute` per 60 s and `per_day` per 86400 s."""

    def __init__(
        self,
        per_minute: int,
        per_day: int,
        clock: Callable[[], float] = time.time,
        max_clients: int = 10_000,
    ):
        self.per_minute = per_minute
        self.per_day = per_day
        self._clock = clock
        self._lock = threading.Lock()
        self._hits: OrderedDict[str, deque] = OrderedDict()
        self.max_clients = max_clients

    def check(self, client: str) -> None:
        """Record a hit for `client` or raise RateLimitExceeded."""
        now = self._clock()
        with self._lock:
            # Expire idle clients from the least-recently-seen end (O(1) amortized).
            while self._hits:
                oldest = next(iter(self._hits))
                newest_hit = self._hits[oldest][-1] if self._hits[oldest] else 0
                if now - newest_hit >= 86400:
                    del self._hits[oldest]
                else:
                    break

            hits = self._hits.get(client)
            if hits is None:
                hits = self._hits[client] = deque()
            self._hits.move_to_end(client)
            while hits and now - hits[0] >= 86400:
                hits.popleft()

            recent = [t for t in hits if now - t < 60]
            if self.per_minute > 0 and len(recent) >= self.per_minute:
                wait = 60 - (now - recent[-self.per_minute])
                raise RateLimitExceeded(math.ceil(wait))
            if self.per_day > 0 and len(hits) >= self.per_day:
                wait = 86400 - (now - hits[-self.per_day])
                raise RateLimitExceeded(math.ceil(wait))

            hits.append(now)
            while len(self._hits) > self.max_clients:
                self._hits.popitem(last=False)


class Busy(Exception):
    """No analysis slot became free within the queue timeout."""


class AnalysisQueue:
    """At most `max_concurrent` analyses at once; extras wait up to `timeout`."""

    def __init__(self, max_concurrent: int, timeout: float):
        self._sem = threading.BoundedSemaphore(max(1, max_concurrent))
        self.timeout = timeout

    def __enter__(self):
        if not self._sem.acquire(timeout=self.timeout):
            raise Busy()
        return self

    def __exit__(self, *exc):
        self._sem.release()
        return False


def client_id(request: Request) -> str:
    """Client IP.

    X-Forwarded-For is only used when TRUST_PROXY=1. Clients can put anything
    at the START of that header, while each trusted proxy appends the address
    it saw at the END; so we take the entry TRUSTED_PROXY_HOPS from the end
    (1 = last entry = the peer our single proxy saw).
    """
    if os.getenv("TRUST_PROXY", "0") == "1":
        hops = max(1, _env_int("TRUSTED_PROXY_HOPS", 1))
        entries = [e.strip() for e in request.headers.get("x-forwarded-for", "").split(",") if e.strip()]
        if len(entries) >= hops:
            return entries[-hops]
    return request.client.host if request.client else "unknown"


rate_limiter = RateLimiter(
    _env_int("RATE_LIMIT_PER_MINUTE", 5),
    _env_int("RATE_LIMIT_PER_DAY", 50),
    max_clients=_env_int("MAX_TRACKED_CLIENTS", 10_000),
)
analysis_queue = AnalysisQueue(
    _env_int("MAX_CONCURRENT_ANALYSES", 2), float(_env_int("QUEUE_TIMEOUT_SECONDS", 30))
)
