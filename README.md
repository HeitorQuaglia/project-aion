# Project Aion

**A programmable QA/QC control plane for AI-powered software.**

Aion orchestrates the complete quality lifecycle of an AI solution — from isolating the execution environment to aggregating statistical results across hundreds of runs. It treats quality assurance not as a checklist of assertions, but as a continuous, measurable, and reproducible process.

> "You can't improve what you can't measure. With AI systems, you can't even measure without infrastructure."

---

## Two Modes

### Operator Control
An interactive desktop interface for developers and QA engineers working alongside the system they are building. Offers live execution feedback, manual inspection of individual runs, replay of past scenarios, and side-by-side output diffs. The operator stays in the loop.

### CI Mode
A fully headless runtime driven by configuration files and CLI flags. Produces structured output (JSON, SARIF) and standard exit codes for integration with any CI/CD pipeline. Zero human interaction required.

Both modes share the same core engine, lifecycle model, and evaluation logic. The surface changes; the semantics do not.

---

## Key Capabilities

- **Lifecycle orchestration** — spec → provision → execute → observe → evaluate → analyze → report
- **Execution isolation** — each run is sandboxed; environment drift does not contaminate results
- **Deterministic and LLM-as-judge evaluation** — mix rule-based scorers with model-driven verdict logic
- **Statistical analysis** — track pass rates, latency distributions, cost trends, and regressions across runs
- **Programmable** — every stage is extensible; bring your own evaluators, reporters, and provisioners
- **Vendor-neutral** — no lock-in to a specific model provider, framework, or cloud
