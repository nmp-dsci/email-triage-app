const state = {
  data: null,
  selected: "methodology",
};

const view = document.getElementById("view");
const list = document.getElementById("case-list");

loadData();

async function loadData() {
  try {
    const embedded = window.EMAIL_TRIAGE_EVALS;
    state.data = embedded ?? (await fetchEvalJson());
    renderList();
    render();
  } catch (error) {
    view.innerHTML = `<section class="section band"><h1>No eval data</h1><p class="lede">Run <code>uv run --prerelease=allow python evals/run_evals.py --offline</code> to generate the static evaluation artifact.</p><pre>${escapeHtml(String(error))}</pre></section>`;
  }
}

async function fetchEvalJson() {
  const response = await fetch("data/evals.json");
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-case-id]");
  if (!button) return;
  state.selected = button.dataset.caseId;
  document.querySelectorAll("[data-case-id]").forEach((item) => item.classList.remove("active"));
  button.classList.add("active");
  render();
});

function renderList() {
  const cases = Array.isArray(state.data.cases) ? state.data.cases : [];
  if (!cases.length) {
    list.innerHTML = `<div class="empty-list">No eval conversations found.</div>`;
    return;
  }
  list.innerHTML = cases
    .map((item) => {
      const priority = item.output?.overall_priority ?? "no response";
      return `<button class="case-button" data-case-id="${escapeAttr(item.id)}">
        <span class="case-status ${escapeAttr(item.status)}"></span>
        <span>
          <strong>${escapeHtml(item.title)}</strong>
          <small>${escapeHtml(item.status)} · ${escapeHtml(priority)}</small>
        </span>
      </button>`;
    })
    .join("");
}

function render() {
  if (state.selected === "methodology") {
    renderMethodology();
    return;
  }
  const item = state.data.cases.find((caseItem) => caseItem.id === state.selected);
  if (!item) {
    renderMethodology();
    return;
  }
  renderCase(item);
}

function renderMethodology() {
  const config = state.data.config ?? {};
  const cases = Array.isArray(state.data.cases) ? state.data.cases : [];
  const passed = cases.filter((item) => item.status === "passed").length;
  view.innerHTML = `
    <section class="section">
      <h1>Methodology</h1>
      <p class="lede">${escapeHtml(state.data.methodology?.summary_md ?? "")}</p>
    </section>
    <section class="section grid">
      <div class="metric"><span>Eval conversations</span><strong>${escapeHtml(cases.length)}</strong></div>
      <div class="metric"><span>Passed</span><strong>${escapeHtml(passed)} / ${escapeHtml(cases.length)}</strong></div>
      <div class="metric"><span>Generated</span><strong>${escapeHtml(state.data.generated_at ?? "")}</strong></div>
    </section>
    <section class="section band">
      <h2>Solution Flow</h2>
      <img class="diagram" src="${escapeAttr(state.data.methodology?.diagram ?? "methodology/solution-diagram.svg")}" alt="Solution diagram" />
    </section>
    <section class="section grid">
      <div class="metric"><span>Provider</span><strong>${escapeHtml(config.llm_provider ?? "")}</strong></div>
      <div class="metric"><span>Model</span><strong>${escapeHtml(config.llm_model ?? "")}</strong></div>
      <div class="metric"><span>Region</span><strong>${escapeHtml(config.region ?? "")}</strong></div>
      <div class="metric"><span>Auth</span><strong>${escapeHtml(config.auth ?? "")}</strong></div>
    </section>
    <section class="section grid">
      ${vocabBlock("Categories", config.categories)}
      ${vocabBlock("Priorities", config.priorities)}
    </section>`;
}

function renderCase(item) {
  const output = item.output ?? {};
  view.innerHTML = `
    <section class="section">
      <h1>${escapeHtml(item.title)}</h1>
      <p class="lede">Run ${escapeHtml(item.run_id ?? "none")} · HTTP ${escapeHtml(item.http_status)} · ${escapeHtml(item.duration_ms)}ms</p>
    </section>
    <section class="section grid">
      <div class="metric"><span>Status</span><strong>${escapeHtml(item.status)}</strong></div>
      <div class="metric"><span>Overall priority</span><strong>${escapeHtml(output.overall_priority ?? "")}</strong></div>
      <div class="metric"><span>Task count</span><strong>${escapeHtml((output.tasks ?? []).length)}</strong></div>
    </section>
    <section class="section band">
      <h2>Checks</h2>
      <div class="checks">${(item.checks ?? []).map(checkTemplate).join("")}</div>
    </section>
    <section class="section band">
      <h2>Request</h2>
      ${requestTemplate(item.request ?? {})}
      <details class="raw-json"><summary>Raw Power Automate JSON</summary><pre>${escapeHtml(JSON.stringify(item.request, null, 2))}</pre></details>
    </section>
    <section class="section band">
      <h2>Output</h2>
      ${tasksTableTemplate(output.tasks ?? [])}
      <p class="reasoning">${escapeHtml(output.reasoning ?? "")}</p>
    </section>
    <section class="section">
      <details open><summary>Trace / Interim Steps</summary>${traceTemplate(item.trace ?? [])}</details>
    </section>`;
}

function vocabBlock(title, items = []) {
  return `<div class="band"><h2>${escapeHtml(title)}</h2>${items
    .map((item) => `<p><strong>${escapeHtml(item.label)}</strong><br /><span class="lede">${escapeHtml(item.definition)}</span></p>`)
    .join("")}</div>`;
}

function requestTemplate(request) {
  const attachments = Array.isArray(request.attachments) ? request.attachments : [];
  const body = htmlToText(request.body || request.bodyPreview || "");
  return `<article class="email-preview">
    <header class="email-header">
      <div>
        <span>From</span>
        <strong>${escapeHtml(request.from ?? request.sender ?? "")}</strong>
      </div>
      <div>
        <span>To</span>
        <strong>${escapeHtml(request.to ?? "")}</strong>
      </div>
      <div>
        <span>Importance</span>
        <strong>${escapeHtml(request.importance ?? "")}</strong>
      </div>
      <div>
        <span>Received</span>
        <strong>${escapeHtml(request.receivedDateTime ?? "")}</strong>
      </div>
    </header>
    <div class="email-subject">${escapeHtml(request.subject ?? "")}</div>
    <div class="email-body">${escapeHtml(body)}</div>
    <div class="attachment-row">
      <span>Attachments</span>
      ${
        attachments.length
          ? attachments.map((attachment) => attachmentTemplate(attachment)).join("")
          : '<strong class="muted-text">None</strong>'
      }
    </div>
  </article>`;
}

function attachmentTemplate(attachment) {
  const size = attachment.size ? `${Math.round(Number(attachment.size) / 1024)} KB` : "";
  return `<strong>${escapeHtml(attachment.name ?? "")}${size ? ` · ${escapeHtml(size)}` : ""}</strong>`;
}

function tasksTableTemplate(tasks) {
  if (!tasks.length) {
    return `<p class="lede">No structured tasks were returned.</p>`;
  }
  return `<div class="table-wrap">
    <table class="tasks-table">
      <thead>
        <tr>
          <th>Task</th>
          <th>Category</th>
          <th>Urgency</th>
          <th>Due</th>
          <th>Source</th>
          <th>Confidence</th>
        </tr>
      </thead>
      <tbody>
        ${tasks.map(taskRowTemplate).join("")}
      </tbody>
    </table>
  </div>`;
}

function taskRowTemplate(task) {
  return `<tr>
    <td><strong>#${escapeHtml(task.task_id)}</strong> ${escapeHtml(task.summary)}</td>
    <td>${escapeHtml(task.category)}</td>
    <td><span class="priority priority-${escapeAttr(task.priority)}">${escapeHtml(task.priority)}</span></td>
    <td>${escapeHtml(task.due_date ?? "-")}</td>
    <td>${escapeHtml(task.source ?? "-")}</td>
    <td>${task.confidence == null ? "-" : `${Math.round(Number(task.confidence) * 100)}%`}</td>
  </tr>`;
}

function checkTemplate(check) {
  return `<div class="check ${check.ok ? "pass" : "fail"}">
    <strong>${escapeHtml(check.ok ? "Pass" : "Fail")}</strong> ${escapeHtml(check.name)}
    ${check.detail ? `<small>${escapeHtml(JSON.stringify(check.detail))}</small>` : ""}
  </div>`;
}

function traceTemplate(trace) {
  if (!trace.length) return "<p>No trace artifacts found.</p>";
  return trace
    .map((item) => `<details><summary>Step ${escapeHtml(item.step)} · ${escapeHtml(item.type ?? "artifact")}</summary><pre>${escapeHtml(JSON.stringify(item, null, 2))}</pre></details>`)
    .join("");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}

function htmlToText(value) {
  const withoutTags = String(value ?? "")
    .replace(/<br\s*\/?\s*>/gi, "\n")
    .replace(/<\/p>/gi, "\n\n")
    .replace(/<\/li>/gi, "\n")
    .replace(/<[^>]+>/g, " ");
  return decodeEntities(withoutTags)
    .replace(/[ \t]+/g, " ")
    .replace(/\n\s+/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function decodeEntities(value) {
  const entities = {
    amp: "&",
    lt: "<",
    gt: ">",
    quot: '"',
    apos: "'",
    nbsp: " ",
    mdash: "-",
    ndash: "-",
  };
  return value.replace(/&([a-z]+);/gi, (_, entity) => entities[entity.toLowerCase()] ?? _);
}
