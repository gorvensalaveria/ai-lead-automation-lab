from app.rate_limiter import (
    FixedWindowRateLimiter,
    build_rate_limit_headers,
)


def test_fixed_window_rate_limiter_allows_until_limit():
    now = {"value": 100.0}
    limiter = FixedWindowRateLimiter(
        limit=2,
        window_seconds=60,
        clock=lambda: now["value"],
    )

    first = limiter.check("client")
    second = limiter.check("client")
    third = limiter.check("client")

    assert first.allowed
    assert first.remaining == 1
    assert second.allowed
    assert second.remaining == 0
    assert not third.allowed
    assert third.retry_after_seconds == 60


def test_fixed_window_rate_limiter_resets_after_window():
    now = {"value": 100.0}
    limiter = FixedWindowRateLimiter(
        limit=1,
        window_seconds=60,
        clock=lambda: now["value"],
    )

    assert limiter.check("client").allowed
    assert not limiter.check("client").allowed

    now["value"] = 161.0

    result = limiter.check("client")

    assert result.allowed
    assert result.remaining == 0


def test_fixed_window_rate_limiter_is_keyed_per_client():
    limiter = FixedWindowRateLimiter(limit=1, window_seconds=60, clock=lambda: 100.0)

    assert limiter.check("client-a").allowed
    assert limiter.check("client-b").allowed
    assert not limiter.check("client-a").allowed


def test_build_rate_limit_headers_includes_retry_after_when_blocked():
    limiter = FixedWindowRateLimiter(limit=1, window_seconds=60, clock=lambda: 100.0)
    limiter.check("client")
    blocked = limiter.check("client")

    headers = build_rate_limit_headers(blocked)

    assert headers["X-RateLimit-Limit"] == "1"
    assert headers["X-RateLimit-Remaining"] == "0"
    assert headers["Retry-After"] == "60"
