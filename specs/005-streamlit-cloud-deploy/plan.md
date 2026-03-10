# Implementation Plan: Deploy Streamlit App to Streamlit Community Cloud

**Branch**: `005-streamlit-cloud-deploy` | **Date**: 2026-03-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-streamlit-cloud-deploy/spec.md`

## Summary

Deploy the existing Strands Demo Streamlit frontend to Streamlit Community Cloud (SCC) so users can access it from a stable public HTTPS URL. The AgentCore backend, Cognito User Pool, and all AWS infrastructure remain unchanged on AWS. The app is a stateless frontend — no infrastructure is moved. Changes are limited to: (1) generating a `requirements.txt` for SCC dependency resolution, (2) creating a public GitHub repository, (3) configuring SCC secrets, and (4) updating the Cognito App Client to allow the new redirect URI.

## Technical Context

**Language/Version**: Python 3.11 (match `.python-version`; set in SCC Advanced Settings)
**Primary Dependencies**: streamlit, strands-agents, boto3, authlib, python-dotenv, anthropic, bedrock-agentcore, requests (all from `pyproject.toml`)
**Storage**: N/A — stateless frontend, all state in `st.session_state`
**Testing**: pytest (existing), manual smoke test on deployed URL
**Target Platform**: Streamlit Community Cloud (free tier) + AWS (AgentCore, Cognito — unchanged)
**Project Type**: Web application (Streamlit frontend)
**Performance Goals**: Cold start < 15 seconds (SC-001), full login flow < 60 seconds (SC-002)
**Constraints**: SCC free tier: 1GB memory, public GitHub repo required
**Scale/Scope**: Demo workload — single concurrent user sufficient

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simplicity First | PASS | No new abstractions. Changes limited to `requirements.txt`, GitHub remote, SCC secrets config, Cognito URI update. Zero application logic changes. |
| II. Iterative & Independent Delivery | PASS | Feature is independently deliverable — app continues to work locally and on SCC. Vertical slice: deployment config only. |
| III. Python-Native Patterns | PASS | Dependencies declared in `requirements.txt` derived from `pyproject.toml`. No new runtimes. |
| IV. Security by Design | PASS | Cognito remains the IdP. Secrets never committed — supplied via SCC secrets manager. `.env` in `.gitignore`. |
| V. Observability & Debuggability | PASS | `LOG_LEVEL` configurable via SCC secret. FR-007 requires clear error on missing secrets (already implemented in `app.py`). |

**Post-Phase 1 Re-check**: All principles still satisfied. No design artifacts introduce new complexity.

## Project Structure

### Documentation (this feature)

```text
specs/005-streamlit-cloud-deploy/
├── plan.md              # This file
├── research.md          # Phase 0 output — technology decisions
├── quickstart.md        # Phase 1 output — deployment walkthrough
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
# Existing structure — no new directories. Only new file: requirements.txt
.
├── app.py                     # Streamlit entry point (unchanged)
├── requirements.txt           # NEW — generated from pyproject.toml for SCC
├── pyproject.toml             # Existing — unchanged
├── .gitignore                 # Existing — already excludes .env
├── src/
│   ├── agent/                 # Strands agent logic (unchanged)
│   ├── agentcore/             # AgentCore client (unchanged)
│   ├── auth/                  # Cognito OAuth (unchanged)
│   └── chat/                  # Chat UI (unchanged)
├── infra/                     # AWS infra templates (unchanged)
└── tests/                     # pytest tests (unchanged)
```

**Structure Decision**: No structural changes. The only new file at repo root is `requirements.txt`. All existing code, infra, and test directories remain untouched.

## Architecture

### Deployment Topology

```text
┌──────────────────────────┐     HTTPS     ┌────────────────────────────┐
│  Streamlit Community     │ ◄──────────── │  User Browser              │
│  Cloud (free tier)       │               │  https://*.streamlit.app   │
│                          │               └────────────────────────────┘
│  app.py                  │
│  src/                    │
│  requirements.txt        │
│  Secrets: st.secrets     │
│  (env vars auto-exposed) │
└──────────┬───────────────┘
           │ HTTPS + JWT Bearer
           ▼
┌──────────────────────────┐
│  AWS (unchanged)         │
│  ┌─────────────────────┐ │
│  │ AgentCore Runtime   │ │
│  │ (Cognito JWT auth)  │ │
│  └─────────────────────┘ │
│  ┌─────────────────────┐ │
│  │ Cognito User Pool   │ │
│  │ (hosted UI)         │ │
│  └─────────────────────┘ │
└──────────────────────────┘
```

### Secrets Configuration (SCC TOML format)

Root-level keys in SCC secrets manager become environment variables automatically:

```toml
# Streamlit Community Cloud → Settings → Secrets
COGNITO_USER_POOL_ID = "us-east-1_XXXXXXXXX"
COGNITO_CLIENT_ID = "xxxxxxxxxxxxxxxxxxxxxxxxxx"
COGNITO_CLIENT_SECRET = "xxxxxxxxxxxxxxxxxxxxxxxxxx"
COGNITO_DOMAIN = "https://strands-demo-dhamijag.auth.us-east-1.amazoncognito.com"
COGNITO_REDIRECT_URI = "https://<app-name>.streamlit.app"
ANTHROPIC_API_KEY = "sk-ant-..."
TAVILY_API_KEY = "tvly-..."
AGENTCORE_RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:829040135710:runtime/strands_demo_agent-..."
AWS_REGION = "us-east-1"
LOG_LEVEL = "INFO"
```

### Why No Code Changes

1. **Secrets**: `os.environ.get()` works because SCC auto-exposes root-level TOML secrets as env vars.
2. **`load_dotenv()`**: No-op when `.env` doesn't exist — harmless in SCC.
3. **Redirect URI**: Controlled by `COGNITO_REDIRECT_URI` env var — already configurable per environment (FR-008).
4. **Dependencies**: `requirements.txt` is a new file but doesn't change existing code.

## Tech Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| Frontend hosting | Streamlit Community Cloud (free tier) | Replaces `localhost:8501` for public access |
| Dependency manifest | `requirements.txt` (new file) | Generated from `pyproject.toml` |
| Secrets | SCC Secrets Manager (TOML) | Root-level keys → auto env vars |
| Source control | GitHub (public repo) | New remote — SCC pulls from here |
| Auth | AWS Cognito (unchanged) | Add SCC URL to allowed callbacks |
| Backend | AWS AgentCore Runtime (unchanged) | HTTPS + JWT from SCC frontend |

## Complexity Tracking

No constitution violations. No complexity justification needed.
