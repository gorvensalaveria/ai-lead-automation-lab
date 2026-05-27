import pytest

from app.automation.openai_client import (
    calculate_retry_delay,
    is_transient_openai_error,
    retry_openai_operation,
)


class RateLimitError(Exception):
    pass


class BadRequestError(Exception):
    status_code = 400


class TemporaryServerError(Exception):
    status_code = 503


def test_retry_openai_operation_retries_transient_error_then_succeeds():
    calls = {"count": 0}
    slept = []

    def request_callable():
        calls["count"] += 1
        if calls["count"] == 1:
            raise RateLimitError("too many requests")
        return "ok"

    result = retry_openai_operation(
        operation="summary",
        request_callable=request_callable,
        max_retries=3,
        base_delay_seconds=1,
        sleeper=slept.append,
        jitter=lambda _start, _end: 0,
    )

    assert result == "ok"
    assert calls["count"] == 2
    assert slept == [1]


def test_retry_openai_operation_stops_after_max_retries():
    calls = {"count": 0}

    def request_callable():
        calls["count"] += 1
        raise TemporaryServerError("service unavailable")

    with pytest.raises(RuntimeError, match="OpenAI classification request failed"):
        retry_openai_operation(
            operation="classification",
            request_callable=request_callable,
            max_retries=2,
            base_delay_seconds=1,
            sleeper=lambda _delay: None,
            jitter=lambda _start, _end: 0,
        )

    assert calls["count"] == 3


def test_retry_openai_operation_does_not_retry_non_transient_error():
    calls = {"count": 0}

    def request_callable():
        calls["count"] += 1
        raise BadRequestError("bad request")

    with pytest.raises(RuntimeError, match="OpenAI follow_up_message request failed"):
        retry_openai_operation(
            operation="follow_up_message",
            request_callable=request_callable,
            max_retries=3,
            sleeper=lambda _delay: None,
        )

    assert calls["count"] == 1


def test_is_transient_openai_error_detects_status_and_error_name():
    assert is_transient_openai_error(RateLimitError("limit"))
    assert is_transient_openai_error(TemporaryServerError("server"))
    assert not is_transient_openai_error(BadRequestError("bad request"))


def test_calculate_retry_delay_uses_exponential_backoff_and_jitter():
    delay = calculate_retry_delay(
        attempt=3,
        base_delay_seconds=2,
        jitter=lambda _start, _end: 0.5,
    )

    assert delay == 8.5
