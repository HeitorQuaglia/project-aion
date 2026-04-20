# Aion — Concept & Design Model

## 1. Motivation

Generic test frameworks were designed for deterministic software. An assertion either passes or fails. The same input reliably produces the same output. Side effects are predictable.

AI-powered systems break every one of these assumptions:

- **Non-determinism** — the same prompt can produce meaningfully different outputs across runs, even at temperature zero.
- **Latency variance** — response times fluctuate with model load, token count, and infrastructure conditions.
- **Model drift** — a model updated by a provider may silently change behavior on your workload.
- **Multi-turn context** — correctness in a conversation depends on the entire preceding state, not a single input.
- **Cost as a quality dimension** — a solution that spends 10× more tokens to answer the same question is not equivalent, even if the answer is correct.

None of these dimensions are first-class citizens in `pytest`, `jest`, or their equivalents. Aion is built around them.

---

## 2. Core Model

Aion is a **control plane**. It does not contain your AI application. It does not replace your framework. It orchestrates the lifecycle of quality measurement *around* your system.

The mental model: Aion is to AI quality what Kubernetes is to deployment — it manages state, enforces policy, coordinates components, and surfaces health — but it doesn't run your code directly.

Three principles follow from this:

1. **Aion owns the lifecycle, not the implementation.** Your evaluators, your target system, and your reporters are plugged in. Aion drives the sequence.
2. **Aion is the source of truth for run metadata.** Every execution is recorded with its inputs, environment snapshot, outputs, scores, and cost. Nothing is ephemeral.
3. **Aion speaks in policies, not scripts.** A CI pipeline doesn't call a test function — it declares a policy (`fail if p50 latency > 2s`) and Aion enforces it.

---

## 3. Lifecycle Stages

Every quality run in Aion passes through the following canonical stages. Each stage is a well-defined contract between Aion's engine and the components it orchestrates.

### `spec`
Declare what behavior is expected. A spec is a named collection of **scenarios** — each scenario pairs an input (a prompt, a conversation history, a document) with one or more **probes** (questions about the expected output). Specs are version-controlled artifacts, not imperative scripts.

### `provision`
Isolate the execution environment. Before any run begins, Aion ensures the target system is in a known state: correct model version pinned, dependencies locked, external services mocked or live as declared. Isolation is not optional — it is the precondition for reproducibility.

### `execute`
Run the target system under controlled conditions. Aion submits inputs to the system, captures the raw response, and records execution metadata (wall time, token usage, HTTP status, error traces). The system under test is a black box at this stage.

### `observe`
Enrich the raw execution record. Structured fields are extracted from responses (tool calls, citations, JSON blobs). Traces are attached if the system emits them. Cost is normalized to a common unit. The observation layer turns raw output into structured data.

### `evaluate`
Score the observed output against the spec's probes. Aion supports two evaluator classes:

- **Deterministic** — regex match, JSON schema validation, substring presence, latency threshold. Binary or scored.
- **LLM-as-judge** — a separate model evaluates the output against a rubric. Returns a verdict with reasoning. Configurable model and prompt.

Multiple evaluators can run in parallel on the same observation. Each produces a named **verdict**.

### `analyze`
Aggregate verdicts across runs to compute statistical measures: pass rate, score distributions, p50/p95/p99 latency, cost per scenario, regression delta vs. a baseline run. This is where single-run signals become trends.

### `report`
Surface results to the right consumer. In Operator Control mode, results feed a live UI with drill-down into individual runs. In CI mode, a structured artifact (JSON, SARIF, or a custom reporter) is written to stdout or a file, and an exit code signals overall policy compliance.

---

## 4. Two Modes

### Operator Control

The Operator Control mode is designed for the developer or QA engineer working alongside the AI system during development. It is interactive, visual, and built for iteration speed.

Key characteristics:
- Live feedback as each scenario executes
- Manual inspection of any run: input, raw output, observation record, each verdict and its reasoning
- Replay: re-run a specific scenario with a modified input without re-running the full suite
- Diff view: compare two runs side by side (useful when testing a prompt change)
- Policy editor: define and tweak pass/fail thresholds interactively

The Operator is a participant. Aion augments their judgment, it does not replace it.

### CI Mode

The CI mode is designed for automated pipelines where no human is present. It is headless, scriptable, and deterministic in its interface contract.

Key characteristics:
- Driven entirely by configuration files (suite definitions, environment declarations, policy thresholds) and CLI flags
- Emits structured output on stdout (default: JSON lines; optionally SARIF for toolchain integration)
- Exit code reflects policy outcome: `0` = all policies pass, non-zero = one or more policies violated
- No interactive prompts, no UI dependencies, no state outside the declared config and the run artifact

A CI run is fully reproducible given the same config, the same model version, and the same input fixtures.

---

## 5. Design Principles

**Programmability over convention.**
Every stage of the lifecycle exposes an extension point. You bring your own evaluators, provisioners, and reporters. Aion provides the orchestration harness and the data model; it does not mandate the scoring logic.

**Isolation by default.**
Reproducibility requires controlled environments. Aion makes isolation the default, not an opt-in. Runs that share state across scenarios are explicitly declared, not accidentally inherited.

**Statistical validity.**
A single run is anecdotal. Aion is designed around repeated measurement, distribution tracking, and regression detection. Quality thresholds are expressed as statistical policies, not boolean flags.

**Vendor-neutral.**
Aion does not assume a specific model provider, inference framework, agent SDK, or cloud. The target system is an interface, not a dependency. Evaluators that use LLM-as-judge are configurable to any model via a standard adapter.

**Separation of concerns.**
The spec (what to test), the execution (how to run it), the evaluation (how to score it), and the policy (what constitutes pass/fail) are four distinct, independently versioned artifacts. Mixing them produces fragile test suites.

---

## 6. Glossary

| Term | Definition |
|---|---|
| **Suite** | A named, versioned collection of scenarios that represent a coherent quality concern (e.g., "RAG retrieval accuracy", "tool call reliability"). |
| **Scenario** | A single test case: one input (or conversation history) paired with one or more probes. The atomic unit of execution. |
| **Probe** | A question about an expected output property. A scenario may have multiple probes (e.g., "does the answer mention the source?" AND "is the tone neutral?"). |
| **Run** | A single execution of a scenario by the target system, including all observation data and verdicts. |
| **Verdict** | The output of a single evaluator applied to a single run: a score (numeric or categorical) and optional reasoning. |
| **Policy** | A threshold or rule applied to aggregated verdicts across runs (e.g., "pass rate must exceed 95%", "p95 latency must be under 3s"). Policies are evaluated at the `report` stage. |
| **Policy Outcome** | The binary result of evaluating all policies for a suite run: pass or fail. This is what CI pipelines consume. |
| **Baseline** | A stored run artifact used as a reference point for regression detection in subsequent runs. |
