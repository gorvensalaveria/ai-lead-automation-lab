"""Entry point for the AI Lead Intake Automation System."""

from pathlib import Path

from app.automation.classifier import classify_lead
from app.automation.lead_loader import load_lead
from app.automation.message_generator import generate_follow_up_message
from app.automation.scorer import score_lead
from app.automation.storage import build_result, save_output
from app.automation.summarizer import summarize_lead


def main() -> None:
    """Run the local AI lead intake workflow for a sample lead."""
    sample_lead_path = Path("data/leads/lead_004_saas.json")
    lead = load_lead(sample_lead_path)

    contact = lead["contact"]
    lead_details = lead["lead_details"]

    print("AI Lead Intake Automation System - Milestone 8")
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

    try:
        follow_up_message = generate_follow_up_message(
            lead=lead,
            summary=summary,
            classification=classification,
            score=score,
        )
    except RuntimeError as error:
        print(f"\nAI follow-up message skipped: {error}")
        return

    print("\nFollow-Up Message Draft:")
    print(follow_up_message)

    result = build_result(
        lead=lead,
        summary=summary,
        classification=classification,
        score=score,
        follow_up_message=follow_up_message,
    )
    output_path = save_output(result)

    print("\nSaved Output:")
    print(output_path)


if __name__ == "__main__":
    main()
