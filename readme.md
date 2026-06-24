# Email Triage App

## View The Demo Dashboard

The fastest way to review the working demo is the static evaluation dashboard:

```sh
python3 -m http.server 8080 --directory dashboard
```

Then open:

```text
http://localhost:8080/test-evaluation.html
```

The dashboard shows the methodology plus three eval email conversations with
request, structured output, checks, and trace/interim artifacts. It works
without the API running because the latest eval output is embedded in
`dashboard/assets/evals-data.js`.

To regenerate the static demo data before viewing:

```sh
make eval-static
```

Dockerised FastAPI service for receiving Outlook email payloads from Power
Automate, extracting structured prioritised tasks, and saving each request's
artifacts under `runs/` for review and evaluation.

The app runs locally in deterministic `LLM_PROVIDER=mock` mode by default so
the full demo/eval flow works without live Claude credentials. Set
`LLM_PROVIDER=anthropic` or `LLM_PROVIDER=foundry` when wiring production
credentials.

## Local Setup

Create a local env file and fill in the secrets you need:

```sh
cp .env.example .env
```

For first-party Anthropic, set `LLM_PROVIDER=anthropic` and
`ANTHROPIC_API_KEY`. For Azure AI Foundry, set `LLM_PROVIDER=foundry` plus the
`AZURE_FOUNDRY_*` values.

## Run

```sh
make up
```

The API listens on `http://localhost:8000`. Local run bundles are written to
`./runs` on the host via the compose mount.

If another service already owns host port `8000`, run with a different host
port:

```sh
PORT=8010 make up-detached
```

Useful commands:

```sh
make build
make up-detached
make health
make logs
make down
```

## Evaluate

Run all eval cases against the live local API:

```sh
make up-detached
make eval
```

For a non-default host port:

```sh
PORT=8010 make up-detached
EVAL_API_URL=http://localhost:8010 make eval
```

The runner posts every case in `evals/cases/`, reads matching run bundles from
`runs/`, and writes `dashboard/data/evals.json` for the static walkthrough
dashboard.

For a static pre-deployment eval that does not require a running API server:

```sh
make eval-static
```

That writes both `dashboard/data/evals.json` and
`dashboard/assets/evals-data.js`. `test-evaluation.html` loads the JS data
bundle directly, so the eval conversations are visible even after the app is
stopped.

Serve the dashboard with:

```sh
python3 -m http.server 8080 --directory dashboard
```

## Docker

The image uses a multi-stage uv build:

1. install dependencies with `uv sync --frozen --no-dev --no-install-project`;
2. copy the virtual environment into a slim Python runtime image;
3. run Uvicorn as a non-root user;
4. mount `/app/runs` for per-request artifacts.

Build manually with:

```sh
docker compose build
```

## Azure Deployment Notes

The v1 target is Azure Container Apps in Australia East:

1. build and push the Docker image to Azure Container Registry;
2. deploy a Container App with external HTTPS ingress to port `8000`;
3. configure `ANTHROPIC_API_KEY` or `AZURE_FOUNDRY_*`, `LOGFIRE_TOKEN`, and
   `TRIAGE_API_KEY` as Container Apps secrets;
4. mount persistent storage for `/app/runs` with Azure Files, or switch the app
   storage implementation to Azure Blob when that slice lands.
