"""Simple inbound rate limiting for expensive lead processing routes."""

from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic

from fastapi import Request

from app.config import (
    LEAD_PROCESS_RATE_LIMIT_PER_MINUTE,
    LEAD_PROCESS_RATE_LIMIT_WINDOW_SECONDS,
)


@dataclass(frozen=True)
class RateLimitResult:
    """Result of one rate-limit check."""

    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int
    reset_seconds: int


class FixedWindowRateLimiter:
    """In-memory fixed-window limiter keyed by client identifier."""

    def __init__(
        self,
        *,
        limit: int,
        window_seconds: int,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self.limit = max(0, int(limit))
        self.window_seconds = max(1, int(window_seconds))
        self.clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> RateLimitResult:
        """Record one attempt and return whether it is allowed."""
        if self.limit <= 0:
            return RateLimitResult(
                allowed=True,
                limit=0,
                remaining=0,
                retry_after_seconds=0,
                reset_seconds=0,
            )

        now = self.clock()
        hits = self._hits[key]
        window_start = now - self.window_seconds

        while hits and hits[0] <= window_start:
            hits.popleft()

        if len(hits) >= self.limit:
            retry_after = max(1, round((hits[0] + self.window_seconds) - now))
            return RateLimitResult(
                allowed=False,
                limit=self.limit,
                remaining=0,
                retry_after_seconds=retry_after,
                reset_seconds=retry_after,
            )

        hits.append(now)
        remaining = max(0, self.limit - len(hits))
        reset_seconds = max(0, round((hits[0] + self.window_seconds) - now))

        return RateLimitResult(
            allowed=True,
            limit=self.limit,
            remaining=remaining,
            retry_after_seconds=0,
            reset_seconds=reset_seconds,
        )


lead_process_rate_limiter = FixedWindowRateLimiter(
    limit=LEAD_PROCESS_RATE_LIMIT_PER_MINUTE,
    window_seconds=LEAD_PROCESS_RATE_LIMIT_WINDOW_SECONDS,
)


def get_rate_limit_key(request: Request) -> str:
    """Return a conservative client key for public lead processing limits."""
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()

    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def build_rate_limit_headers(result: RateLimitResult) -> dict[str, str]:
    """Return standard rate-limit headers for one check."""
    headers = {
        "X-RateLimit-Limit": str(result.limit),
        "X-RateLimit-Remaining": str(result.remaining),
        "X-RateLimit-Reset": str(result.reset_seconds),
    }

    if not result.allowed:
        headers["Retry-After"] = str(result.retry_after_seconds)

    return headers
