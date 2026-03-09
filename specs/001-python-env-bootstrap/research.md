# Research: Python Environment Bootstrap

**Feature**: `001-python-env-bootstrap`
**Date**: 2026-03-09

---

## Decision 1: Strands Agents SDK Package

**Decision**: Use `strands-agents` from PyPI. Add companion `strands-agents-tools` as a
runtime dependency for pre-built tool support.

**Rationale**: `strands-agents` is the official PyPI package name for the AWS Strands
Agents SDK (launched May 2025). The top-level Python import namespace is `strands`
(e.g., `from strands import Agent`). Bedrock support is built into the core package via
`boto3` — no separate provider package required for the default use case.

**Alternatives considered**:
- `aws-strands-sdk` — does not exist
- `amazon-strands` — does not exist

**Companion packages**:
- `strands-agents-tools` — pre-built tool library (file ops, shell, HTTP). Include as
  runtime dep since the demo will use tools.
- Optional extras (`strands-agents[anthropic]`, `strands-agents[openai]`) — not needed;
  project uses Bedrock.

**Version note**: Launched at `0.1.x`. Pin with `>=0.1.0` and verify current patch on
PyPI at setup time.

---

## Decision 2: uv Project Structure & Commands

**Decision**: Use `uv init --app` to initialize. Declare runtime deps in
`[project].dependencies`, dev deps in `[dependency-groups].dev` (PEP 735). Commit
`uv.lock`.

**Rationale**: `uv` is the fastest Python package manager and has native `pyproject.toml`
support. The `--app` flag (no `[build-system]` block) is correct for a non-published
application. `[dependency-groups]` is the PEP 735 standard for dev-only deps, natively
supported by uv v0.4+.

**Key commands**:

| Action | Command |
|--------|---------|
| Initialize project | `uv init --app strands-demo` (or `uv init` in existing dir) |
| Sync all deps | `uv sync` |
| Add runtime dep | `uv add <package>` |
| Add dev dep | `uv add --dev <package>` |
| Run in venv | `uv run <command>` |

**Lock file**: `uv.lock` — MUST be committed. Cross-platform, pins all transitive deps.

**Python version files**:
- `requires-python = ">=3.11"` in `pyproject.toml` — enforced constraint
- `.python-version` — created by uv, pins local dev Python version, commit it

**Alternatives considered**:
- `pip` + `requirements.txt` — rejected; no lock file, no dev/runtime separation
- `poetry` — rejected; uv is faster and is the project's chosen toolchain per constitution
- `pipenv` — rejected; same reasons as poetry

---

## Decision 3: Environment Variables & Secrets Template

**Decision**: Commit `.env.example` with all placeholder keys. Load via `python-dotenv`
at runtime. Add `python-dotenv` as a runtime dependency.

**Rationale**: boto3 reads `AWS_*` variables automatically from `os.environ`. Cognito
variables must be read explicitly by application code. Establishing the full set of
expected variables in `.env.example` now prevents ad-hoc secret management later.

**AWS Core variables** (read automatically by boto3):

| Variable | Purpose |
|----------|---------|
| `AWS_ACCESS_KEY_ID` | IAM user/role access key |
| `AWS_SECRET_ACCESS_KEY` | IAM secret key |
| `AWS_SESSION_TOKEN` | Temporary session token (STS/SSO) |
| `AWS_REGION` | Target AWS region (e.g., `us-east-1`) |

**Cognito variables** (read explicitly by app code):

| Variable | Purpose |
|----------|---------|
| `COGNITO_USER_POOL_ID` | User Pool ID (e.g., `us-east-1_AbCdEfGhI`) |
| `COGNITO_APP_CLIENT_ID` | App Client ID for auth flows |
| `COGNITO_APP_CLIENT_SECRET` | App Client Secret (if confidential client) |
| `COGNITO_DOMAIN` | Hosted UI domain for OAuth 2.0 flows |
| `COGNITO_REDIRECT_URI` | OAuth 2.0 callback URL |
| `COGNITO_REGION` | Region of User Pool (often same as AWS_REGION) |

**`.gitignore` additions required**: `.env`, `.env.*` (already present in project
`.gitignore`). `.env.example` is explicitly safe to commit (no real values).
