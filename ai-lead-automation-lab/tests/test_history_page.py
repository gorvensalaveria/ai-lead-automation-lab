from app.history_page import render_history_detail_page, render_history_page


def history_row(index: int, classification: str) -> dict:
    return {
        "file_name": f"lead_{index}.json",
        "processed_at": f"2026-05-25T10:0{index}:00+00:00",
        "contact_name": f"Contact {index}",
        "company": f"Company {index}",
        "classification": classification,
        "lead_score": 80,
        "max_score": 100,
        "lead_rating": "high",
        "recommended_next_action": "Reply quickly.",
    }


def test_history_page_shows_five_rows_per_page():
    rows = [history_row(index, "hot") for index in range(1, 7)]

    html = render_history_page(rows, page=1)

    assert "Contact 1" in html
    assert "Contact 5" in html
    assert "Contact 6" not in html
    assert 'class="history-page-link active"' in html
    assert "Page 1 of 2" in html
    assert ">Previous</a>" in html
    assert ">Next</a>" in html
    assert "/history?page=2" in html
    assert 'href="/history/lead_1.json"' in html


def test_history_page_filters_by_classification():
    rows = [
        history_row(1, "hot"),
        history_row(2, "warm"),
        history_row(3, "cold"),
    ]

    html = render_history_page(rows, selected_classification="warm")

    assert "Contact 2" in html
    assert "Contact 1" not in html
    assert "Contact 3" not in html
    assert "/history?classification=warm&amp;page=1" not in html
    assert "/history?classification=warm&page=1" in html
    assert '<span class="filter-label">Warm</span>' in html
    assert '<span class="filter-count">1</span>' in html


def test_history_detail_page_shows_saved_lead_sections():
    result = {
        "processed_at": "2026-05-25T10:00:00+00:00",
        "lead": {
            "lead_id": "lead_test",
            "source": "website_form",
            "business_type": "SaaS",
            "contact": {
                "first_name": "Ana",
                "last_name": "Santos",
                "email": "ana@example.com",
                "phone": "+63 917 555 0123",
                "company": "Santos Software",
            },
            "lead_details": {
                "service_interest": "lead automation",
                "preferred_contact_method": "email",
            },
        },
        "ai_outputs": {
            "summary": "Ana wants lead automation.",
            "classification": "hot",
            "score": {
                "total_score": 100,
                "max_score": 100,
                "rating": "high",
                "breakdown": {
                    "fit": 25,
                    "urgency": 25,
                    "budget": 25,
                    "intent": 25,
                },
            },
            "follow_up_message": "Hi Ana, thanks for reaching out.",
        },
        "crm_ready": {
            "lead_id": "lead_test",
            "source": "website_form",
            "processed_at": "2026-05-25T10:00:00+00:00",
            "contact_name": "Ana Santos",
            "email": "ana@example.com",
            "phone": "+63 917 555 0123",
            "company": "Santos Software",
            "business_type": "SaaS",
            "service_interest": "lead automation",
            "preferred_contact_method": "email",
            "classification": "hot",
            "lead_score": 100,
            "max_score": 100,
            "lead_rating": "high",
            "score_breakdown": {
                "fit": 25,
                "urgency": 25,
                "budget": 25,
                "intent": 25,
            },
            "recommended_next_action": "Reply quickly and offer a discovery call.",
            "summary": "Ana wants lead automation.",
            "follow_up_message": "Hi Ana, thanks for reaching out.",
        },
    }

    html = render_history_detail_page(result, "lead_test.json")

    assert "Lead Detail Review" in html
    assert "Ana Santos at Santos Software" in html
    assert "Reply quickly and offer a discovery call." in html
    assert "Ana wants lead automation." in html
    assert "Hi Ana, thanks for reaching out." in html
    assert "CRM-Ready Fields" in html
    assert "lead_test.json" in html
