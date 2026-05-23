"""FastAPI webhook endpoints for the AI Lead Intake Automation System."""

from typing import Any

from fastapi import FastAPI, HTTPException

from app.automation.logger import setup_logger
from app.automation.workflow import process_lead


app = FastAPI(
    title="AI Lead Intake Automation API",
    description="Webhook API for processing and qualifying inbound leads.",
    version="0.1.0",
)
logger = setup_logger()


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return a simple API health check."""
    return {"status": "ok"}


@app.post("/webhooks/leads")
def process_lead_webhook(lead: dict[str, Any]) -> dict[str, Any]:
    """Process one lead from a webhook-style JSON request body."""
    try:
        result, output_path = process_lead(lead)
    except ValueError as error:
        logger.error("Webhook validation error: %s", error)
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        logger.error("Webhook processing error: %s", error)
        raise HTTPException(status_code=502, detail=str(error)) from error
    except Exception as error:
        logger.exception("Unexpected webhook error")
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while processing lead.",
        ) from error

    return {
        "status": "processed",
        "output_path": str(output_path),
        "result": result,
    }
