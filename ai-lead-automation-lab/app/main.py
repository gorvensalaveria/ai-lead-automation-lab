"""Entry point for the AI Lead Intake Automation System."""

import argparse
from pathlib import Path
from typing import Any

from app.automation.logger import setup_logger
from app.automation.workflow import process_lead_file


DEFAULT_LEAD_FILE = "data/leads/lead_004_saas.json"
DEFAULT_OUTPUT_DIR = "data/outputs"
logger = setup_logger()


def parse_args() -> argparse.Namespace:
    """Parse terminal options for the local workflow."""
    parser = argparse.ArgumentParser(
        description="Run the AI Lead Intake Automation workflow.",
    )
    parser.add_argument(
        "--lead-file",
        default=DEFAULT_LEAD_FILE,
        help=f"Path to the lead JSON file. Default: {DEFAULT_LEAD_FILE}",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Folder where output JSON files will be saved. Default: {DEFAULT_OUTPUT_DIR}",
    )

    return parser.parse_args()


def run_workflow(lead_file: str | Path, output_dir: str | Path) -> dict[str, Any] | None:
    """Run the full local AI lead intake workflow."""
    print("AI Lead Intake Automation System")
    print(f"Lead file: {lead_file}")
    try:
        result, output_path = process_lead_file(lead_file=lead_file, output_dir=output_dir)
    except RuntimeError as error:
        logger.error("Workflow processing step failed: %s", error)
        print(f"Workflow skipped: {error}")
        return None

    lead = result["lead"]
    ai_outputs = result["ai_outputs"]
    summary = ai_outputs["summary"]
    classification = ai_outputs["classification"]
    score = ai_outputs["score"]
    follow_up_message = ai_outputs["follow_up_message"]
    contact = lead["contact"]
    lead_details = lead["lead_details"]

    print(f"Loaded lead: {lead['lead_id']}")
    print(f"Business type: {lead['business_type']}")
    print(f"Contact: {contact['first_name']} {contact['last_name']}")
    print(f"Company: {contact['company']}")
    print(f"Interest: {lead_details['service_interest']}")
    print("Status: Lead data loaded and validated successfully.")

    print("\nAI Summary:")
    print(summary)

    print("\nAI Classification:")
    print(classification)

    breakdown = score["breakdown"]

    print("\nLead Score:")
    print(f"{score['total_score']}/{score['max_score']} ({score['rating']})")
    print(
        "Breakdown: "
        f"fit={breakdown['fit']}, "
        f"urgency={breakdown['urgency']}, "
        f"budget={breakdown['budget']}, "
        f"intent={breakdown['intent']}"
    )

    print("\nFollow-Up Message Draft:")
    print(follow_up_message)

    print("\nSaved Output:")
    print(output_path)

    return result


def main() -> None:
    """Run the terminal workflow."""
    args = parse_args()
    try:
        run_workflow(lead_file=args.lead_file, output_dir=args.output_dir)
    except FileNotFoundError as error:
        logger.error("Lead file error: %s", error)
        print(f"Error: {error}")
    except ValueError as error:
        logger.error("Lead validation error: %s", error)
        print(f"Error: {error}")
    except Exception as error:
        logger.exception("Unexpected workflow error")
        print(f"Unexpected error: {error}")


if __name__ == "__main__":
    main()
