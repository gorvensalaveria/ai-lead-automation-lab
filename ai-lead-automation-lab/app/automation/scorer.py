"""Score leads based on fit, urgency, budget, and intent."""

from typing import Any


def score_lead(lead: dict[str, Any], classification: str) -> dict[str, Any]:
    """Generate a lead score with a simple business-friendly breakdown."""
    lead_details = lead["lead_details"]

    fit_score = score_fit(lead)
    urgency_score = score_urgency(lead_details["timeline"])
    budget_score = score_budget(lead_details["budget_range"])
    intent_score = score_intent(lead_details["message"], classification)

    total_score = fit_score + urgency_score + budget_score + intent_score

    return {
        "total_score": total_score,
        "max_score": 100,
        "rating": get_rating(total_score),
        "breakdown": {
            "fit": fit_score,
            "urgency": urgency_score,
            "budget": budget_score,
            "intent": intent_score,
        },
    }


def score_fit(lead: dict[str, Any]) -> int:
    """Score how closely the lead matches the target business types."""
    target_business_types = {
        "agency",
        "appointment_based",
        "coaching",
        "consulting",
        "ecommerce",
        "real_estate",
        "saas",
        "service_business",
    }

    business_type = lead["business_type"].lower()
    if business_type in target_business_types:
        return 25

    return 10


def score_urgency(timeline: str) -> int:
    """Score how soon the lead appears to need help."""
    timeline_value = timeline.lower()

    if timeline_value in {"urgent", "within_30_days"}:
        return 25

    if timeline_value in {"next_60_days", "this_quarter"}:
        return 18

    return 8


def score_budget(budget_range: str) -> int:
    """Score whether the lead provided a clear budget."""
    budget = budget_range.lower()

    if "usd" in budget or "php" in budget:
        return 25

    if budget and budget != "unknown":
        return 15

    return 5


def score_intent(message: str, classification: str) -> int:
    """Score buying intent from the AI classification and lead message."""
    normalized_classification = classification.lower()
    message_value = message.lower()

    if normalized_classification == "hot":
        return 25

    if normalized_classification == "warm":
        return 18

    intent_keywords = [
        "need",
        "want",
        "looking for",
        "request",
        "help",
        "automation",
        "walkthrough",
        "pricing",
    ]

    if any(keyword in message_value for keyword in intent_keywords):
        return 12

    return 5


def get_rating(total_score: int) -> str:
    """Convert a numeric score into a simple lead quality rating."""
    if total_score >= 80:
        return "high"

    if total_score >= 50:
        return "medium"

    return "low"
