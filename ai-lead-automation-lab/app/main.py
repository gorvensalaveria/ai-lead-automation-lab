"""Entry point for the AI Lead Intake Automation System."""

from pathlib import Path

from app.automation.classifier import classify_lead
from app.automation.lead_loader import load_lead
from app.automation.scorer import score_lead
from app.automation.summarizer import summarize_lead


def main() -> None:
    """Load, validate, summarize, classify, and score a sample lead."""
    sample_lead_path = Path("data/leads/lead_004_saas.json")
    lead = load_lead(sample_lead_path)

    contact = lead["contact"]
    lead_details = lead["lead_details"]

    print("AI Lead Intake Automation System - Milestone 6")
    print(f"Loaded lead: {lead['lead_id']}")
    print(f"Business type: {lead['business_type']}")
    print(f"Contact: {contact['first_name']} {contact['last_name']}")
    print(f"Company: {contact['company']}")
    print(f"Interest: {lead_details['service_interest']}")
    print("Status: Lead data loaded and validated successfully.")

    try:
        summary = summarize_lead(lead)
    except RuntimeError as error:
        print(f"AI summary skipped: {error}")
        return

    print("\nAI Summary:")
    print(summary)

    try:
        classification = classify_lead(lead)
    except RuntimeError as error:
        print(f"\nAI classification skipped: {error}")
        return

    print("\nAI Classification:")
    print(classification)

    score = score_lead(lead, classification)
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


if __name__ == "__main__":
    main()
