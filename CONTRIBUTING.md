# Contributing to Project Aion

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) for dependency and environment management

## Setup

```bash
git clone <repo>
cd project-aion
uv sync --dev
```

## Running checks

```bash
uv run ruff check .          # lint
uv run ruff format .         # format
uv run mypy .                # type checking
uv run pytest                # tests + coverage
```

All four must pass before a PR is ready for review.

---

## Code style

### Formatter and linter

We use **Ruff** for both formatting and linting. Line length is 100. Do not configure your editor to use Black, isort, or any other formatter — Ruff handles everything.

The full rule set is defined in `pyproject.toml`. Key enforced rules: pyflakes, pyupgrade, bugbear, simplify, and pydocstyle (Google convention).

### Type annotations

**All** function signatures require type annotations — parameters and return types. No exceptions for public or private code. Mypy runs in `--strict` mode; the CI will fail on any type error.

```python
# correct
def score(output: str, rubric: Rubric) -> Verdict:
    ...

# wrong — missing annotations
def score(output, rubric):
    ...
```

### Docstrings

Public functions, classes, and methods require docstrings in **Google style**. Omit docstrings for `__init__`, module-level, and package-level (they add noise without value here).

```python
def provision(scenario: Scenario) -> Environment:
    """Isolate an execution environment for a scenario.

    Args:
        scenario: The scenario whose environment requirements will be applied.

    Returns:
        A ready-to-use Environment with all dependencies pinned.

    Raises:
        ProvisionError: If the environment cannot be created or isolated.
    """
```

A docstring should explain **why** or **what contract** the function holds — not restate the obvious from the name and types.

### Comments

Default to no inline comments. Add one only when the reason behind the code is non-obvious: a hidden constraint, a workaround for a specific bug, a subtle invariant. If removing the comment wouldn't confuse a future reader, don't write it.

### Pydantic models

Data structures that cross lifecycle stage boundaries are defined as `pydantic.BaseModel`. Do not use plain dataclasses or TypedDicts for domain objects — validation and serialization come for free.

---

## Testing

Tests live in `tests/`. Mirror the source structure: `aion/lifecycle/evaluate.py` → `tests/lifecycle/test_evaluate.py`.

Coverage threshold is **80%** globally. The CI will fail below this. Write tests that exercise behavior, not implementation details — test the contract, not the internals.

Use `pytest` fixtures for shared state. Do not put setup logic in test functions.

---

## Commits

We follow [Conventional Commits](https://www.conventionalcommits.org/).

```
<type>(<scope>): <short summary>

[optional body]
```

**Types:**

| Type | When to use |
|---|---|
| `feat` | A new capability visible to a user or consumer |
| `fix` | A bug fix |
| `refactor` | Code change that neither adds a feature nor fixes a bug |
| `test` | Adding or updating tests |
| `docs` | Documentation only |
| `chore` | Build, tooling, dependency updates |
| `perf` | Performance improvement |

**Scope** is the lifecycle stage or module affected: `lifecycle`, `evaluate`, `ci`, `report`, `provision`, etc.

```bash
# good
feat(evaluate): add LLM-as-judge evaluator with configurable model
fix(ci): return exit code 1 when any policy threshold is violated
docs: add glossary to concept.md

# bad
update stuff
fixed bug
WIP
```

Summary line: imperative mood, lowercase, no period, max 72 characters.

---

## Branches

```
main          # stable, always passing CI
feat/<name>   # new features
fix/<name>    # bug fixes
chore/<name>  # tooling, deps, non-functional
```

Merge via pull request. Squash if the branch history is noisy; preserve if the commits are clean and meaningful.

---

## What not to do

- Do not add optional parameters or fallbacks for scenarios that cannot happen.
- Do not introduce abstractions until the same pattern appears at least three times.
- Do not add error handling for framework or internal invariants — only validate at system boundaries.
- Do not skip type annotations with `# type: ignore` without a comment explaining why.
