"""HTML page for the browser-based lead intake demo."""


def render_demo_page() -> str:
    """Return the web demo page as self-contained HTML."""
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Lead Qualification Assistant</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4f6f8;
      --panel: #ffffff;
      --ink: #17202a;
      --muted: #5e6b78;
      --line: #d8dee6;
      --primary: #1664c0;
      --primary-dark: #0f4d94;
      --good: #0f766e;
      --warm: #a15c07;
      --cold: #586474;
      --danger: #b42318;
      --shadow: 0 14px 40px rgba(23, 32, 42, 0.08);
      --soft: #eef4f8;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.5;
    }

    header {
      background: #1664c0;
      color: #ffffff;
    }

    .header-inner,
    main {
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
    }

    .header-inner {
      padding: 34px 0 30px;
      display: flex;
      justify-content: space-between;
      gap: 24px;
      align-items: center;
      flex-wrap: wrap;
    }

    h1,
    h2,
    h3,
    p {
      margin-top: 0;
    }

    h1 {
      margin-bottom: 8px;
      font-size: clamp(1.8rem, 4vw, 3rem);
      letter-spacing: 0;
      line-height: 1.05;
    }

    .eyebrow {
      margin-bottom: 8px;
      color: #ffffff;
      font-size: 0.78rem;
      font-weight: 800;
      letter-spacing: 0;
      text-transform: uppercase;
    }

    .subtitle {
      max-width: 720px;
      margin-bottom: 0;
      color: #dbe6ef;
      font-size: 1rem;
    }

    .api-pill {
      border: 1px solid rgba(255, 255, 255, 0.28);
      border-radius: 8px;
      padding: 10px 12px;
      color: #eaf2f8;
      font-size: 0.9rem;
      white-space: nowrap;
    }

    main {
      padding: 28px 0 48px;
    }

    .value-strip {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 24px;
    }

    .value-item {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      min-height: 102px;
    }

    .value-item span {
      display: block;
      color: var(--primary);
      font-size: 0.78rem;
      font-weight: 800;
      text-transform: uppercase;
    }

    .value-item strong {
      display: block;
      margin: 5px 0 3px;
    }

    .value-item p {
      margin-bottom: 0;
      color: var(--muted);
      font-size: 0.9rem;
    }

    .workspace {
      display: grid;
      grid-template-columns: minmax(0, 0.95fr) minmax(320px, 1.05fr);
      gap: 24px;
      align-items: start;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      padding: 22px;
    }

    .results-panel {
      position: sticky;
      top: 24px;
    }

    .panel-title {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
      margin-bottom: 18px;
    }

    .panel-title h2 {
      margin-bottom: 0;
      font-size: 1.25rem;
    }

    .helper-text {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 0.9rem;
    }

    .demo-group {
      margin-bottom: 16px;
      background: #f8fafc;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
    }

    .demo-label {
      margin-bottom: 9px;
      color: var(--muted);
      font-size: 0.82rem;
      font-weight: 800;
      text-transform: uppercase;
    }

    .demo-buttons {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    button,
    select,
    input,
    textarea {
      font: inherit;
    }

    button {
      border: 0;
      border-radius: 8px;
      background: var(--primary);
      color: #ffffff;
      cursor: pointer;
      min-height: 42px;
      padding: 10px 14px;
      font-weight: 700;
    }

    button:hover {
      background: var(--primary-dark);
    }

    button.primary-action {
      min-height: 48px;
      padding: 12px 18px;
      box-shadow: 0 10px 20px rgba(22, 100, 192, 0.2);
    }

    button.secondary {
      background: #eef3f8;
      color: #17202a;
      border: 1px solid var(--line);
      min-height: 36px;
      padding: 8px 10px;
      font-size: 0.9rem;
    }

    button.secondary:hover {
      background: #dfe8f2;
    }

    button.secondary.active {
      background: #dcecff;
      border-color: var(--primary);
      color: var(--primary-dark);
    }

    button:disabled {
      cursor: wait;
      opacity: 0.72;
    }

    form {
      display: grid;
      gap: 16px;
    }

    .field-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }

    label {
      display: grid;
      gap: 6px;
      color: var(--muted);
      font-size: 0.88rem;
      font-weight: 700;
    }

    input,
    select,
    textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #ffffff;
      color: var(--ink);
      padding: 10px 11px;
      min-height: 42px;
    }

    textarea {
      min-height: 132px;
      resize: vertical;
    }

    input:focus,
    select:focus,
    textarea:focus {
      outline: 3px solid rgba(22, 100, 192, 0.18);
      border-color: var(--primary);
    }

    .actions {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      flex-wrap: wrap;
    }

    .action-copy {
      flex-basis: 100%;
      margin: 0 0 -4px;
      color: var(--muted);
      font-size: 0.9rem;
      font-weight: 700;
    }

    .status {
      color: var(--muted);
      font-size: 0.92rem;
      margin: 0;
    }

    .status.error {
      color: var(--danger);
      font-weight: 700;
    }

    .result-empty {
      min-height: 420px;
      color: var(--muted);
      border: 1px dashed var(--line);
      border-radius: 8px;
      padding: 22px;
      background: #fbfcfe;
    }

    .result-empty h3 {
      color: var(--ink);
      margin-bottom: 8px;
      font-size: 1.1rem;
    }

    .empty-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 18px;
    }

    .empty-card {
      background: #ffffff;
      border: 1px solid var(--line);
      border-radius: 8px;
      min-height: 86px;
      padding: 12px;
    }

    .empty-card span {
      display: block;
      color: var(--primary);
      font-size: 0.78rem;
      font-weight: 800;
      text-transform: uppercase;
    }

    .empty-card p {
      margin: 5px 0 0;
      color: var(--muted);
      font-size: 0.9rem;
    }

    .result-stack {
      display: grid;
      gap: 14px;
    }

    .report-hero {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #f8fbff;
      padding: 16px;
    }

    .report-hero-top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }

    .report-hero h3 {
      margin-bottom: 4px;
      font-size: 1.15rem;
    }

    .report-hero p {
      margin-bottom: 0;
      color: var(--muted);
    }

    .report-score {
      color: var(--primary);
      font-size: 2rem;
      font-weight: 800;
      line-height: 1;
      white-space: nowrap;
    }

    .report-score span {
      color: var(--muted);
      font-size: 0.95rem;
    }

    .metric-row {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }

    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: #fbfcfe;
      min-height: 96px;
    }

    .metric span {
      display: block;
      color: var(--muted);
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
    }

    .metric strong {
      display: block;
      margin-top: 8px;
      font-size: 1.35rem;
      overflow-wrap: anywhere;
    }

    .action-card {
      border-left: 4px solid var(--primary);
      background: var(--soft);
      border-radius: 8px;
      padding: 14px;
    }

    .action-card span {
      display: block;
      color: var(--muted);
      font-size: 0.78rem;
      font-weight: 800;
      text-transform: uppercase;
    }

    .action-card strong {
      display: block;
      margin-top: 6px;
      font-size: 1.08rem;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 5px 10px;
      color: #ffffff;
      font-size: 0.78rem;
      font-weight: 800;
      text-transform: uppercase;
    }

    .badge.hot {
      background: var(--good);
    }

    .badge.warm {
      background: var(--warm);
    }

    .badge.cold {
      background: var(--cold);
    }

    .result-section {
      border-top: 1px solid var(--line);
      padding-top: 14px;
    }

    .result-section h3 {
      margin-bottom: 8px;
      font-size: 0.98rem;
    }

    .message-box,
    .path-box {
      background: #f8fafc;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    .breakdown {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
      color: var(--muted);
      font-size: 0.9rem;
    }

    .breakdown div {
      background: #f8fafc;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
    }

    .crm-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }

    .crm-grid div {
      background: #f8fafc;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      overflow-wrap: anywhere;
    }

    .crm-grid span {
      display: block;
      color: var(--muted);
      font-size: 0.75rem;
      font-weight: 800;
      text-transform: uppercase;
    }

    footer {
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 0 0 34px;
      color: var(--muted);
      font-size: 0.9rem;
    }

    @media (max-width: 860px) {
      .results-panel {
        position: static;
      }

      .workspace,
      .field-grid,
      .metric-row,
      .breakdown,
      .value-strip,
      .empty-grid,
      .crm-grid {
        grid-template-columns: 1fr;
      }

      .panel-title {
        align-items: flex-start;
        flex-direction: column;
      }

      .api-pill {
        white-space: normal;
      }
    }
  </style>
</head>
<body>
  <header>
    <div class="header-inner">
      <div>
        <p class="eyebrow">AI Automation Portfolio Project</p>
        <h1>AI Lead Qualification Assistant</h1>
        <p class="subtitle">Turn inbound leads into summaries, scores, recommended next actions, and ready-to-send follow-ups.</p>
      </div>
    </div>
  </header>

  <main>
    <section class="value-strip" aria-label="Business value">
      <div class="value-item">
        <span>Use Case</span>
        <strong>Website, ad, booking, and CRM leads</strong>
        <p>Useful for forms, ads, bookings, and CRM inquiries.</p>
      </div>
      <div class="value-item">
        <span>Saves Time</span>
        <strong>Reduces manual lead review</strong>
        <p>Scores help teams decide who to contact first.</p>
      </div>
      <div class="value-item">
        <span>Output</span>
        <strong>CRM-ready notes and follow-up draft</strong>
        <p>Each lead is saved as structured JSON.</p>
      </div>
    </section>

    <div class="workspace">
      <section class="panel" aria-labelledby="form-title">
        <div class="panel-title">
          <div>
            <h2 id="form-title">Lead Details</h2>
            <p class="helper-text">Enter a lead manually or load a sample scenario.</p>
          </div>
        </div>

        <div class="demo-group">
          <div class="demo-label">Try Sample Leads</div>
          <div class="demo-buttons" aria-label="Demo leads">
            <button class="secondary" type="button" data-demo="hot">Hot SaaS Demo Request</button>
            <button class="secondary" type="button" data-demo="warm">Warm Coaching Inquiry</button>
            <button class="secondary" type="button" data-demo="cold">Cold General Inquiry</button>
          </div>
        </div>

        <form id="lead-form">
          <div class="field-grid">
            <label>First Name
              <input name="first_name" required autocomplete="given-name">
            </label>
            <label>Last Name
              <input name="last_name" required autocomplete="family-name">
            </label>
            <label>Email
              <input name="email" type="email" required autocomplete="email">
            </label>
            <label>Phone
              <input name="phone" required autocomplete="tel">
            </label>
            <label>Company
              <input name="company" required autocomplete="organization">
            </label>
            <label>Source
              <select name="source" required>
                <option value="website_form">Website form</option>
                <option value="demo_request_form">Demo request form</option>
                <option value="facebook_ad">Facebook ad</option>
                <option value="email_inquiry">Email inquiry</option>
                <option value="booking_page">Booking page</option>
              </select>
            </label>
            <label>Business Type
              <select name="business_type" required>
                <option value="saas">SaaS</option>
                <option value="agency">Agency</option>
                <option value="consulting">Consulting</option>
                <option value="coaching">Coaching</option>
                <option value="ecommerce">E-commerce</option>
                <option value="real_estate">Real estate</option>
                <option value="service_business">Service business</option>
                <option value="other">Other</option>
              </select>
            </label>
            <label>Timeline
              <select name="timeline" required>
                <option value="urgent">Urgent</option>
                <option value="within_30_days">Within 30 days</option>
                <option value="next_60_days">Next 60 days</option>
                <option value="this_quarter">This quarter</option>
                <option value="not_sure">Not sure</option>
              </select>
            </label>
            <label>Budget Range
              <input name="budget_range" required>
            </label>
            <label>Preferred Contact
              <select name="preferred_contact_method" required>
                <option value="email">Email</option>
                <option value="phone">Phone</option>
                <option value="sms">SMS</option>
                <option value="whatsapp">WhatsApp</option>
              </select>
            </label>
          </div>

          <label>Service Interest
            <input name="service_interest" required>
          </label>

          <label>Lead Message
            <textarea name="message" required></textarea>
          </label>

          <div class="actions">
            <p class="action-copy">Run the AI qualification workflow</p>
            <button class="primary-action" id="submit-button" type="submit">Process Lead</button>
            <p id="status" class="status" role="status"></p>
          </div>
        </form>
      </section>

      <section class="panel results-panel" aria-labelledby="results-title">
        <div class="panel-title">
          <div>
            <h2 id="results-title">Automation Results</h2>
            <p class="helper-text">A client-friendly report appears here after processing.</p>
          </div>
        </div>
        <div id="results" class="result-empty">
          <h3>What this automation generates</h3>
          <p>Process a lead to see a report your team can review before replying.</p>
          <div class="empty-grid">
            <div class="empty-card">
              <span>AI Summary</span>
              <p>Short plain-English context for the lead.</p>
            </div>
            <div class="empty-card">
              <span>Classification</span>
              <p>Hot, warm, or cold lead priority.</p>
            </div>
            <div class="empty-card">
              <span>Lead Score</span>
              <p>Fit, urgency, budget, and intent scoring.</p>
            </div>
            <div class="empty-card">
              <span>Follow-Up Draft</span>
              <p>A ready-to-edit reply for the prospect.</p>
            </div>
            <div class="empty-card">
              <span>Next Action</span>
              <p>Simple sales recommendation.</p>
            </div>
            <div class="empty-card">
              <span>CRM Output</span>
              <p>Structured fields saved for future handoff.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  </main>

  <footer>
    Demo built with Python, FastAPI, OpenAI API, JSON storage, and pytest.
  </footer>

  <script>
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
        timeline: "this_quarter",
        budget_range: "USD 1,000 - USD 3,000",
        preferred_contact_method: "email",
        service_interest: "business coaching program",
        message: "I run a small consulting business and need help building a consistent client acquisition process. I am comparing coaching programs and want pricing details."
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
        .replace(/\\n/g, "<br>");
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
          <div class="metric">
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
  </script>
</body>
</html>
"""
