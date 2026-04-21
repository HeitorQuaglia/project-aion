# Project Aion

**A programmable QA/QC control plane for AI-powered software.**

Aion orchestrates the complete quality lifecycle of an AI solution — from isolating the execution environment to aggregating statistical results across hundreds of runs. It treats quality assurance not as a checklist of assertions, but as a continuous, measurable, and reproducible process.

> "You can't improve what you can't measure. With AI systems, you can't even measure without infrastructure."

---

## Two Modes

### Operator Control
An interactive web interface for developers and QA engineers working alongside the system they are building. Offers live execution feedback, manual inspection of individual runs, and per-run observation details (raw response, latency, token counts).

### CI Mode
A fully headless runtime driven by configuration files and CLI flags. Produces structured output and standard exit codes for integration with any CI/CD pipeline. Zero human interaction required.

Both modes share the same core engine, lifecycle model, and evaluation logic. The surface changes; the semantics do not.

---

## Key Capabilities

- **Lifecycle orchestration** — spec → execute → observe → evaluate → report
- **Two executor backends** — Agno-native (direct LLM calls) or HTTP (any agent that exposes an endpoint)
- **Deterministic and LLM-as-judge evaluation** — mix rule-based scorers with model-driven verdict logic
- **Vendor-neutral** — no lock-in to a specific model provider, framework, or cloud
- **Programmable** — every stage is extensible; bring your own evaluators and reporters

---

## Architecture

### Domain model

```
Suite ──▶ Scenario ──▶ Probe
            │
            ▼
           Run ──▶ Observation
```

| Concept | Description |
|---|---|
| **Suite** | Named collection of Scenarios |
| **Scenario** | Atomic test case: `input` string + `probes` list + `tags` metadata |
| **Probe** | Assertion on expected output; `deterministic` (rule-based) or `llm_judge` (model-as-evaluator) |
| **Run** | Immutable execution record; lifecycle: `PENDING → RUNNING → COMPLETE \| FAILED` |
| **Observation** | Execution metadata: raw response, wall time, token counts, error |

### Executor backends

Aion supports two executor backends, selected via `AionConfig`:

**Agno executor** — calls an LLM directly through the Agno SDK. Suitable when Aion owns the agent.

**HTTP executor** — POSTs to any HTTP endpoint. Suitable for testing an existing agent service without modifying it.

```
AionConfig
├── llm: ModelConfig          → ExecutorAgent (Agno SDK)
└── http_target: HttpTargetConfig → HttpExecutorAgent (HTTP POST)
```

#### HTTP executor protocol

Any agent can be tested by Aion if it exposes an endpoint that:

- **Accepts**: `POST <url>` with `Content-Type: application/json`
  ```json
  { "message": "<scenario input>", "<tag_key>": "<tag_value>", ... }
  ```
  Extra fields come from `scenario.tags` and are agent-specific (e.g. `aspect_type`, `destination`).

- **Returns**: JSON with a configurable string field (default `"message"`):
  ```json
  { "message": "<agent response>" }
  ```

The adapter that maps this protocol to the agent's internal interface lives in the **agent's own repo** — Aion has no knowledge of agent internals.

---

## REST API

The Aion server exposes a JSON API for managing suites and triggering runs.

### Suites

| Method | Path | Description |
|---|---|---|
| `GET` | `/suites` | List all registered suites |
| `GET` | `/suites/{id}` | Get a suite by ID |
| `POST` | `/suites` | Register a new suite |

### Runs

| Method | Path | Description |
|---|---|---|
| `POST` | `/suites/{suite_id}/runs` | Trigger an evaluation run (async) |
| `GET` | `/runs` | Query runs (`?suite_id=` or `?scenario_id=`) |
| `GET` | `/runs/{id}` | Get a single run with full observation |

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Server liveness check |

---

## Configuration

All settings are driven by environment variables (prefix `AION_`).

### Agno executor (default)

| Variable | Default | Description |
|---|---|---|
| `AION_EXECUTOR_TYPE` | `agno` | Executor backend: `agno` or `http` |
| `AION_LLM_PROVIDER` | `openai` | `openai` or `bedrock` |
| `AION_LLM_MODEL_ID` | `gpt-4o` | Model identifier |
| `AION_LLM_OPENAI_API_KEY` | — | API key (falls back to `OPENAI_API_KEY`) |
| `AION_LLM_OPENAI_BASE_URL` | — | Override endpoint for compatible services |
| `AION_LLM_BEDROCK_REGION` | `us-east-1` | AWS region |
| `AION_STORAGE_PATH` | `runs` | SQLite DB directory |

### HTTP executor

| Variable | Default | Description |
|---|---|---|
| `AION_EXECUTOR_TYPE` | — | Set to `http` to enable |
| `AION_HTTP_TARGET_URL` | — | Full URL of the agent endpoint |
| `AION_HTTP_TARGET_HEADERS` | `{}` | JSON object of extra headers (e.g. auth) |
| `AION_HTTP_TARGET_PROVIDER_NAME` | `http` | Label stored on Run records |
| `AION_HTTP_TARGET_RESPONSE_FIELD` | `message` | JSON key to read from agent response |
| `AION_HTTP_TARGET_TIMEOUT_SECONDS` | `30.0` | Request timeout |

---

## CLI (CI mode)

The `aion` CLI runs a suite defined in a YAML file and exits with code `0` (all passed) or `1` (any failed).

```bash
uv run aion <config.yaml>
uv run aion <config.yaml> --output json
uv run aion <config.yaml> --storage-path /tmp/runs
```

### Config file format

```yaml
# aion.yaml
executor:
  type: openai          # openai | bedrock | http
  model_id: gpt-4o
  api_key: null         # falls back to OPENAI_API_KEY

storage_path: runs      # optional, default "runs"

suite:
  id: my-suite
  name: My Suite
  scenarios:
    - id: sc-1
      suite_id: my-suite
      input: "What is the return policy?"
      probes:
        - id: mentions-policy
          description: "Does the response describe a concrete return policy?"
          probe_type: llm_judge
```

#### Bedrock executor

```yaml
executor:
  type: bedrock
  model_id: anthropic.claude-3-5-sonnet-20241022-v2:0
  region: us-east-1
```

#### HTTP executor

```yaml
executor:
  type: http
  url: http://localhost:8001/api/v1/chat
  headers:
    Authorization: "Bearer <key>"
  provider_name: my-agent
  response_field: message   # JSON key to extract from agent response
  timeout_seconds: 30.0
```

### Output

**Text (default)**
```
[PASS] sc-1 — 843ms
[FAIL] sc-2 — 1204ms

1 passed, 1 failed
```

**JSON** (`--output json`) — one JSON line per run, followed by a summary line:
```jsonl
{"id": "...", "scenario_id": "sc-1", "status": "complete", ...}
{"id": "...", "scenario_id": "sc-2", "status": "failed", ...}
{"passed": 1, "failed": 1, "total": 2}
```

---

## Running

### Backend (API server)

```bash
uv run python -m uvicorn aion.api.app:create_app --factory --reload
```

### Development commands

```bash
uv run ruff check .      # lint
uv run ruff format .     # format
uv run mypy .            # type check (strict)
uv run pytest            # tests + coverage (80% floor)
```

---

## Integrating an existing agent

### Via CLI

Create a config YAML pointing at your agent's HTTP endpoint and run it directly in CI:

```yaml
executor:
  type: http
  url: http://localhost:8001/api/test/chat
  headers:
    Authorization: "Bearer <key>"
  provider_name: my-agent

suite:
  id: my-agent-v1
  name: My Agent Eval
  scenarios:
    - id: s1
      suite_id: my-agent-v1
      input: "What is the return policy?"
      tags:
        context: customer-support
      probes:
        - id: mentions-policy
          description: "Does the response describe a concrete return policy?"
          probe_type: llm_judge
```

```bash
uv run aion my-agent.yaml
```

### Via REST API

1. **Add an adapter endpoint** to the agent's service that accepts `{message, ...tags}` and returns `{message}` (or configure `AION_HTTP_TARGET_RESPONSE_FIELD` to match its existing response shape).

2. **Configure Aion** to target that endpoint:
   ```bash
   AION_EXECUTOR_TYPE=http
   AION_HTTP_TARGET_URL=http://localhost:8001/api/test/chat
   AION_HTTP_TARGET_HEADERS='{"Authorization": "Bearer <key>"}'
   AION_HTTP_TARGET_PROVIDER_NAME=my-agent
   ```

3. **Define a suite** and load it via `POST /suites`:
   ```json
   {
     "id": "my-agent-v1",
     "name": "My Agent Eval",
     "scenarios": [
       {
         "id": "s1",
         "suite_id": "my-agent-v1",
         "input": "What is the return policy?",
         "tags": { "context": "customer-support" },
         "probes": [
           {
             "id": "mentions-policy",
             "description": "Does the response describe a concrete return policy?",
             "probe_type": "llm_judge"
           }
         ]
       }
     ]
   }
   ```

4. **Trigger and inspect**:
   ```bash
   curl -X POST http://localhost:8000/suites/my-agent-v1/runs
   curl http://localhost:8000/runs?suite_id=my-agent-v1
   ```
