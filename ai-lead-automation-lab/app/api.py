"""FastAPI webhook endpoints for the AI Lead Intake Automation System."""

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.automation.logger import setup_logger
from app.automation.storage import list_saved_outputs, load_saved_output
from app.automation.workflow import process_lead
from app.demo_page import render_demo_page
from app.history_page import render_history_detail_page, render_history_page


STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="AI Lead Intake Automation API",
    description="Webhook API for processing and qualifying inbound leads.",
    version="0.1.0",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
logger = setup_logger()


@app.get("/", response_class=HTMLResponse)
def demo_home() -> str:
    """Serve the browser-based lead intake demo."""
    return render_demo_page()


@app.get("/demo", response_class=HTMLResponse)
def demo_page() -> str:
    """Serve the browser-based lead intake demo."""
    return render_demo_page()


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return a simple API health check."""
    return {"status": "ok"}


@app.get("/history", response_class=HTMLResponse)
def lead_history_page(classification: str = "all", page: int = 1) -> str:
    """Serve a browser page for reviewing saved processed leads."""
    return render_history_page(
        history_rows=list_saved_outputs(),
        selected_classification=classification,
        page=page,
    )


@app.get("/api/history")
def lead_history_api() -> dict[str, Any]:
    """Return saved processed lead history as JSON."""
    return {"leads": list_saved_outputs()}


@app.get("/history/{file_name}", response_class=HTMLResponse)
def lead_history_detail_page(file_name: str) -> str:
    """Serve a browser page for reviewing one saved processed lead."""
    try:
        result = load_saved_output(file_name)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    return render_history_detail_page(result=result, file_name=file_name)


@app.get("/api/history/{file_name}")
def lead_history_detail_api(file_name: str) -> dict[str, Any]:
    """Return one saved processed lead result as JSON."""
    try:
        return load_saved_output(file_name)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


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
