<!--
SYNC IMPACT REPORT
==================
Version change: (unversioned template) → 1.0.0
Modified principles: N/A (initial adoption)
Added sections:
  - Core Principles (5 principles)
  - Technology Stack
  - Development Workflow
  - Governance
Removed sections: N/A (initial adoption)
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ Constitution Check section references updated principles
  - .specify/templates/spec-template.md ✅ Aligned with iterative delivery philosophy
  - .specify/templates/tasks-template.md ✅ Task categorization reflects incremental story delivery
Deferred TODOs:
  - None
-->

# Strands Demo Constitution

## Core Principles

### I. Simplicity First (NON-NEGOTIABLE)

Every feature MUST start as the simplest possible implementation that delivers value.
YAGNI (You Aren't Gonna Need It) is enforced: no speculative abstractions, no premature
generalization, no features built for hypothetical future requirements. Complexity MUST be
justified by a concrete, present need — not anticipated need. Each addition to the codebase
MUST answer: "Is this required right now?"

**Rationale**: This is a demo project intended to grow iteratively. Keeping scope tight at
each step ensures forward momentum without accumulating technical debt.

### II. Iterative & Independent Delivery

Every feature MUST be independently deliverable, testable, and demonstrable without
requiring other in-progress features to be complete. Features are delivered as vertical
slices — from Streamlit UI through Strands agent logic to AWS backend. Each iteration MUST
leave the application in a working, runnable state.

**Rationale**: Iterative delivery enables continuous validation, reduces integration risk,
and ensures each step produces a demonstrable artifact.

### III. Python-Native Patterns

All code MUST be written in Python and follow idiomatic Python conventions (PEP 8, type
hints where clarity is improved, virtual environments via `venv` or `uv`). Dependencies
MUST be declared in `requirements.txt` or `pyproject.toml`. No mixing of runtimes or
languages without explicit justification.

**Rationale**: A single-language, idiomatic codebase is easier to maintain, onboard, and
extend incrementally.

### IV. Security by Design

Authentication and authorization MUST use AWS Cognito as the Identity Provider — no
custom auth implementations. Secrets and credentials MUST never be hardcoded; use
environment variables or AWS Secrets Manager. All Streamlit endpoints that expose agent
functionality MUST be protected by Cognito authentication. IAM roles MUST follow the
principle of least privilege.

**Rationale**: Security cannot be retrofitted. Cognito integration from the start ensures
the demo reflects production-grade auth patterns and avoids credential sprawl.

### V. Observability & Debuggability

All Strands agent interactions MUST emit structured log output (at minimum: input, tool
calls, output, errors). Streamlit UI MUST surface agent responses and errors clearly to
the user. Log levels MUST be configurable via environment variable. Silent failures are
not permitted — every error MUST be caught, logged, and surfaced appropriately.

**Rationale**: Agent applications are difficult to debug without visibility into tool
invocations and LLM interactions. Observability is non-negotiable from day one.

## Technology Stack

- **Language**: Python 3.11+
- **Agent Framework**: AWS Strands Agents SDK
- **Frontend**: Streamlit
- **Identity Provider**: AWS Cognito (User Pools + App Client)
- **Cloud Provider**: AWS
- **Dependency Management**: `requirements.txt` or `pyproject.toml` with `uv`/`pip`
- **Testing**: `pytest` for unit and integration tests
- **Environment Config**: `.env` files (local dev) + environment variables (deployed)

New dependencies MUST be evaluated for necessity before being added. Prefer AWS-native
services over third-party equivalents where the complexity trade-off is neutral or
favorable.

## Development Workflow

- Features are developed one at a time, in priority order.
- Each feature MUST have a spec (`spec.md`) before implementation begins.
- Each feature MUST be runnable and demonstrable at completion before the next begins.
- Code changes MUST be committed at logical checkpoints (not in one large batch).
- No feature branch merges without a working Streamlit UI demonstrating the feature.
- Streamlit app MUST remain launchable (`streamlit run app.py`) at all times on `main`.
- AWS infrastructure changes (Cognito, IAM, etc.) MUST be documented alongside code
  changes in the relevant spec or plan artifact.

## Governance

This constitution supersedes all other development practices for this project. Amendments
require: (1) a written description of the change, (2) a version bump per semantic
versioning rules below, and (3) propagation to dependent templates.

**Versioning policy**:
- MAJOR: Removal or incompatible redefinition of an existing principle.
- MINOR: Addition of a new principle or material expansion of guidance.
- PATCH: Clarifications, wording refinements, typo fixes.

**Compliance**: Every spec, plan, and task list MUST reference and comply with the active
constitution version. The `/speckit.plan` Constitution Check gate enforces this before
implementation begins.

**Version**: 1.0.0 | **Ratified**: 2026-03-09 | **Last Amended**: 2026-03-09
