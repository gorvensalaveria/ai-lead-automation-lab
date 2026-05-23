"""Shared workflow helpers for CLI and API entry points."""

from pathlib import Path
from typing import Any

from app.automation.classifier import classify_lead
from app.automation.lead_loader import load_lead, validate_lead
from app.automation.logger import setup_logger
from app.automation.message_generator import generate_follow_up_message
from app.automation.scorer import score_lead
from app.automation.storage import build_result, save_output
from app.automation.summarizer import summarize_lead


logger = setup_logger()


def process_lead(
    lead: dict[str, Any],
    output_dir: str | Path = "data/outputs",
) -> tuple[dict[str, Any], Path]:
    """Validate and process one lead dictionary through the full workflow."""
    validate_lead(lead)
    logger.info("Lead validated: %s", lead["lead_id"])

    summary = summarize_lead(lead)
    logger.info("Lead summarized: %s", lead["lead_id"])

    classification = classify_lead(lead)
    logger.info("Lead classified as %s: %s", classification, lead["lead_id"])

    score = score_lead(lead, classification)
    logger.info(
        "Lead scored %s/%s: %s",
        score["total_score"],
        score["max_score"],
        lead["lead_id"],
    )

    follow_up_message = generate_follow_up_message(
        lead=lead,
        summary=summary,
        classification=classification,
        score=score,
    )
    logger.info("Follow-up message generated: %s", lead["lead_id"])

    result = build_result(
        lead=lead,
        summary=summary,
        classification=classification,
        score=score,
        follow_up_message=follow_up_message,
    )
    output_path = save_output(result, output_dir=output_dir)
    logger.info("Workflow output saved: %s", output_path)

    return result, output_path


def process_lead_file(
    lead_file: str | Path,
    output_dir: str | Path = "data/outputs",
) -> tuple[dict[str, Any], Path]:
    """Load and process one lead JSON file."""
    logger.info("Starting workflow for lead file: %s", lead_file)
    lead = load_lead(lead_file)
    logger.info("Lead loaded from file: %s", lead["lead_id"])

    result, output_path = process_lead(lead=lead, output_dir=output_dir)
    logger.info("Workflow completed successfully: %s", lead["lead_id"])

    return result, output_path
