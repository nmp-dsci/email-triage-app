# Eval Runner

This directory contains live API eval cases for the email triage service. Each
case is one Power Automate-style email payload.

## Layout

```text
evals/cases/<case-id>/
  request.json    # required: payload POSTed to /triage
  expected.json   # optional: lightweight checks for the API output
```

The starter cases are copied from `tests/data/`:

- `01-invoice-pdf`: PDF invoice plus a scheduling task.
- `02-expenses-xlsx`: spreadsheet attachment approval path.
- `03-body-only`: body-only task plus FYI content.

## Run

For a static pre-deployment evaluation that does not require a running API
server, run:

```bash
uv run --prerelease=allow python evals/run_evals.py --offline --fail-on-error
```

This runs the FastAPI app in-process, writes run bundles under `runs/`, writes
`dashboard/data/evals.json`, and writes `dashboard/assets/evals-data.js`. The
HTML loads the JS data bundle directly, so the dashboard remains reviewable
after the app/server is stopped.

To evaluate a live API instead, start the API, then run:

```bash
python evals/run_evals.py --api-url http://localhost:8000/triage
```

If the API requires the Power Automate shared secret, set it in the environment
or pass it explicitly:

```bash
TRIAGE_API_KEY=... python evals/run_evals.py
python evals/run_evals.py --api-key ...
```

The runner always discovers every directory in `evals/cases/` that contains a
`request.json`, posts them to the live API, evaluates any `expected.json`
checks, attempts to read the matching run bundle from `runs/`, and writes:

```text
dashboard/data/evals.json
dashboard/assets/evals-data.js
```

Open the dashboard with:

```bash
python -m http.server 8080 --directory dashboard
```

Then visit `http://localhost:8080/test-evaluation.html`.

You can also open `dashboard/test-evaluation.html` directly from disk after the
offline run because the eval data is embedded via `assets/evals-data.js`.

## Expected Checks

`expected.json` is intentionally small and dependency-free. Supported keys:

- `min_tasks`, `max_tasks`
- `overall_priority` or `overall_priority_in`
- `priorities_include`
- `categories_include`
- `summaries_include`
- `due_dates_include`
- `sources_include`
- `attachment_names_include`

String checks are case-insensitive and search the structured output as JSON, so
they work while the triage schema is still evolving.
