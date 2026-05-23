    const demoLeads = {
      hot: {
        first_name: "Noah",
        last_name: "Mitchell",
        email: "noah.mitchell@example.com",
        phone: "+1 646 555 0142",
        company: "PipelineMetric",
        source: "demo_request_form",
        business_type: "saas",
        timeline: "urgent",
        budget_range: "USD 2,000 - USD 5,000",
        preferred_contact_method: "phone",
        service_interest: "sales workflow automation",
        message: "We need a better way to qualify inbound demo requests before our sales team spends time on calls. We use HubSpot and Slack."
      },
      warm: {
        first_name: "Melissa",
        last_name: "Carter",
        email: "melissa.carter@example.com",
        phone: "+1 415 555 0188",
        company: "Carter Growth Coaching",
        source: "facebook_ad",
        business_type: "coaching",
        timeline: "next_60_days",
        budget_range: "budget not finalized",
        preferred_contact_method: "email",
        service_interest: "client acquisition workflow review",
        message: "I run a small consulting business and I am exploring ways to make client acquisition more consistent. I am still comparing options and would like to understand what a starter workflow could look like."
      },
      cold: {
        first_name: "Taylor",
        last_name: "Morgan",
        email: "taylor.morgan@example.com",
        phone: "+1 206 555 0117",
        company: "Morgan Studio",
        source: "website_form",
        business_type: "other",
        timeline: "not_sure",
        budget_range: "unknown",
        preferred_contact_method: "email",
        service_interest: "general information",
        message: "I am just browsing options and collecting information for a possible project later this year."
      }
    };

    const form = document.querySelector("#lead-form");
    const status = document.querySelector("#status");
    const results = document.querySelector("#results");
    const submitButton = document.querySelector("#submit-button");
    const demoButtons = document.querySelectorAll("[data-demo]");
    const emptyResultsHtml = results.innerHTML;

    function fillDemoLead(kind) {
      const lead = demoLeads[kind];

      if (!lead) {
        return;
      }

      Object.entries(lead).forEach(([key, value]) => {
        const field = form.elements[key];

        if (field) {
          field.value = value;
          field.dispatchEvent(new Event("change", {bubbles: true}));
        }
      });

      demoButtons.forEach((button) => {
        button.classList.toggle("active", button.dataset.demo === kind);
      });

      results.className = "result-empty";
      results.innerHTML = emptyResultsHtml;
      status.textContent = `${lead.first_name}'s sample lead loaded. Click Process Lead to run the workflow.`;
      status.classList.remove("error");
    }

    function buildLeadPayload(values) {
      return {
        lead_id: `web_${Date.now()}`,
        source: values.source,
        submitted_at: new Date().toISOString(),
        business_type: values.business_type,
        contact: {
          first_name: values.first_name,
          last_name: values.last_name,
          email: values.email,
          phone: values.phone,
          company: values.company
        },
        lead_details: {
          service_interest: values.service_interest,
          message: values.message,
          budget_range: values.budget_range,
          timeline: values.timeline,
          preferred_contact_method: values.preferred_contact_method
        }
      };
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function renderAiText(value) {
      return escapeHtml(value)
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/\n/g, "<br>");
    }

    function getClassificationReason(classification, score) {
      const breakdown = score.breakdown;

      if (classification === "hot") {
        return `This lead scored high because it has strong fit (${breakdown.fit}), urgency (${breakdown.urgency}), budget clarity (${breakdown.budget}), and intent (${breakdown.intent}).`;
      }

      if (classification === "warm") {
        return `This lead has potential, with a score of ${score.total_score}/${score.max_score}. A qualifying question can confirm timing, budget, or decision intent.`;
      }

      return `This lead scored ${score.total_score}/${score.max_score}, so it is better suited for nurture content or a lighter follow-up.`;
    }

    function renderResults(data) {
      const result = data.result;
      const ai = result.ai_outputs;
      const crm = result.crm_ready || {};
      const score = ai.score;
      const breakdown = score.breakdown;
      const classification = ai.classification.toLowerCase();
      const classificationClass = ["hot", "warm", "cold"].includes(classification) ? classification : "cold";
      const recommendedAction = crm.recommended_next_action || "Review the lead and choose the next follow-up step.";
      const classificationReason = getClassificationReason(classificationClass, score);
      const contactName = crm.contact_name || "Processed lead";
      const company = crm.company || "Unknown company";

      results.className = "result-stack";
      results.innerHTML = `
        <div class="report-hero">
          <div class="report-hero-top">
            <div>
              <h3>${escapeHtml(contactName)} at ${escapeHtml(company)}</h3>
              <p>${escapeHtml(crm.service_interest || "Lead qualification report")}</p>
            </div>
            <div class="report-score">${escapeHtml(score.total_score)}<span>/${escapeHtml(score.max_score)}</span></div>
          </div>
          <div class="action-card">
            <span>Recommended Next Action</span>
            <strong>${escapeHtml(recommendedAction)}</strong>
          </div>
        </div>

        <div class="metric-row">
          <div class="metric classification-card ${escapeHtml(classificationClass)}">
            <span>Classification</span>
            <strong><span class="badge ${escapeHtml(classificationClass)}">${escapeHtml(ai.classification)}</span></strong>
          </div>
          <div class="metric">
            <span>Lead Score</span>
            <strong>${escapeHtml(score.total_score)}/${escapeHtml(score.max_score)}</strong>
          </div>
          <div class="metric">
            <span>Rating</span>
            <strong>${escapeHtml(score.rating)}</strong>
          </div>
        </div>

        <div class="result-section">
          <h3>AI Summary</h3>
          <p>${renderAiText(ai.summary)}</p>
        </div>

        <div class="result-section">
          <h3>Why This Lead Is ${escapeHtml(ai.classification)}</h3>
          <p>${escapeHtml(classificationReason)}</p>
        </div>

        <div class="result-section">
          <h3>Score Breakdown</h3>
          <div class="breakdown">
            <div>Fit: <strong>${escapeHtml(breakdown.fit)}</strong></div>
            <div>Urgency: <strong>${escapeHtml(breakdown.urgency)}</strong></div>
            <div>Budget: <strong>${escapeHtml(breakdown.budget)}</strong></div>
            <div>Intent: <strong>${escapeHtml(breakdown.intent)}</strong></div>
          </div>
        </div>

        <div class="result-section">
          <h3>Follow-Up Draft</h3>
          <div class="message-box">${renderAiText(ai.follow_up_message)}</div>
        </div>

        <div class="result-section">
          <h3>CRM-Ready Fields</h3>
          <div class="crm-grid">
            <div><span>Contact</span>${escapeHtml(crm.contact_name || "")}</div>
            <div><span>Company</span>${escapeHtml(crm.company || "")}</div>
            <div><span>Email</span>${escapeHtml(crm.email || "")}</div>
            <div><span>Service Interest</span>${escapeHtml(crm.service_interest || "")}</div>
          </div>
        </div>

        <div class="result-section">
          <h3>Saved Output Path</h3>
          <div class="path-box">${escapeHtml(data.output_path)}</div>
        </div>
      `;
    }

    demoButtons.forEach((button) => {
      button.addEventListener("click", (event) => {
        event.preventDefault();
        fillDemoLead(button.dataset.demo);
      });
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(form).entries());
      const payload = buildLeadPayload(values);

      submitButton.disabled = true;
      status.textContent = "Processing lead...";
      status.classList.remove("error");

      try {
        const response = await fetch("/webhooks/leads", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || "Unable to process lead.");
        }

        status.textContent = "Lead processed and saved.";
        renderResults(data);
      } catch (error) {
        status.textContent = error.message;
        status.classList.add("error");
      } finally {
        submitButton.disabled = false;
      }
    });

    fillDemoLead("hot");
