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
      <h2>Output</h2>
      ${(output.tasks ?? []).map(taskTemplate).join("")}
      <p>${escapeHtml(output.reasoning ?? "")}</p>
    </section>
    <section class="section">
      <details open><summary>Request</summary><pre>${escapeHtml(JSON.stringify(item.request, null, 2))}</pre></details>
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

function taskTemplate(task) {
  return `<div class="task">
    <div class="chips">
      <span class="chip">#${escapeHtml(task.task_id)}</span>
      <span class="chip">${escapeHtml(task.category)}</span>
      <span class="chip">${escapeHtml(task.priority)}</span>
      <span class="chip">${escapeHtml(task.source)}</span>
      ${task.due_date ? `<span class="chip">${escapeHtml(task.due_date)}</span>` : ""}
    </div>
    <p>${escapeHtml(task.summary)}</p>
  </div>`;
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
