import json
import logging

from app.automation.logger import log_structured_event


def test_log_structured_event_writes_json(caplog):
    logger = logging.getLogger("test_structured_logger")
    logger.setLevel(logging.INFO)
    logger.propagate = True

    with caplog.at_level(logging.INFO):
        log_structured_event(
            logger=logger,
            event="api_request_completed",
            request_id="request-123",
            path="/health",
            status_code=200,
        )

    payload = json.loads(caplog.records[-1].message)

    assert payload["event"] == "api_request_completed"
    assert payload["request_id"] == "request-123"
    assert payload["path"] == "/health"
    assert payload["status_code"] == 200
