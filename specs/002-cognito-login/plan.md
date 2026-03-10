# Implementation Plan: Cognito Login

**Branch**: `002-cognito-login` | **Date**: 2026-03-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-cognito-login/spec.md`

---

## Summary

Add user authentication to the Strands Demo Streamlit app using AWS Cognito Hosted UI (OAuth2 authorization code flow with PKCE). Unauthenticated users see a login page with a single "Login" button; clicking it redirects to Cognito's managed login UI. On successful authentication, users land on the main application. All AWS infrastructure (User Pool, App Client, Hosted UI domain) is provisioned via a CloudFormation template. A post-deploy script creates two test users. All credentials are read from a `.env` file populated from CloudFormation stack outputs.

---

## Developer Tools

When researching or implementing any part of this feature, prefer using MCP tools before falling back to general web search:

| Situation | MCP Tool to Use |
|---|---|
| Questions about Strands Agents SDK (agent loop, tool use, hooks) | Strands Agents MCP server |
| AWS service documentation (Cognito API, CloudFormation resource types, IAM) | AWS MCP server |
| Debugging CloudFormation template errors or Cognito config issues | AWS MCP server |
| Understanding Strands tool integration patterns | Strands Agents MCP server |

MCP tools provide authoritative, up-to-date documentation directly from the source and reduce the risk of acting on outdated community answers. Use them at the start of any implementation task that touches AWS services or Strands SDK internals.

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `streamlit>=1.35.0`, `boto3>=1.34.0`, `python-dotenv>=1.0.0`, `authlib>=1.3.2` (new)
**Storage**: None — session tokens held in `st.session_state` (in-memory, per tab)
**Testing**: `pytest>=8.0`
**Target Platform**: Local dev (localhost:8501); browser-based Streamlit app
**Project Type**: Web application (Streamlit)
**Performance Goals**: Login round-trip completes in under 5 seconds (SC-001)
**Constraints**: Credentials never hardcoded; `.env` as sole config source; session lost on hard refresh (acceptable for demo)
**Scale/Scope**: 2 pre-provisioned users; single-user demo scale

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Simplicity First | ✅ Pass | Manual OAuth2 flow (~50 LOC); no unnecessary abstractions; no premature generalization |
| II. Iterative & Independent Delivery | ✅ Pass | Login is a complete vertical slice; app remains runnable at every step; this feature doesn't depend on any incomplete feature |
| III. Python-Native Patterns | ✅ Pass | Python 3.11+, pyproject.toml/uv, PEP 8, type hints where helpful |
| IV. Security by Design | ✅ Pass | Cognito as IdP (no custom auth); no hardcoded secrets; CSRF state parameter; PKCE (S256); tokens in server-side session state only |
| V. Observability & Debuggability | ✅ Pass | Auth errors surfaced clearly to user; startup fails fast with descriptive message on missing config; note: no app-level auth event audit logging (by user's explicit decision — Cognito audit logs used instead) |

**Post-Design Re-check**: ✅ All gates pass. The manual OAuth2 approach, in-memory session storage, and boto3 provisioning script all align with constitution constraints.

---

## Project Structure

### Documentation (this feature)

```text
specs/002-cognito-login/
├── plan.md              # This file
├── research.md          # Phase 0: OAuth2 approach, provisioning, security decisions
├── data-model.md        # Phase 1: UserSession, OAuthPendingState, CognitoConfig entities
├── quickstart.md        # Phase 1: Dev setup and verification steps
├── contracts/
│   └── cognito-oauth2.md  # OAuth2 endpoint contracts (authorize, token, logout)
└── tasks.md             # Phase 2 output (/speckit.tasks — not created here)
```

### Source Code (repository root)

```text
app.py                          # Streamlit entry point — updated with auth gate

src/
└── auth/
    ├── __init__.py
    ├── config.py               # Load & validate CognitoConfig from .env
    ├── oauth.py                # Build auth URL, exchange code, PKCE, state validation
    └── session.py              # is_authenticated(), get_user(), clear_session()

infra/
└── cognito.yaml                # CloudFormation template: User Pool, App Client, Hosted UI domain

scripts/
└── provision_users.py          # Post-deploy script: create 2 test users with permanent passwords
                                # (CFN cannot set permanent passwords natively; script runs after stack deploy)

tests/
└── unit/
    └── auth/
        ├── test_config.py      # Config validation, missing var handling
        └── test_oauth.py       # URL construction, state validation, token parsing

.env.example                    # Template with all required variable names (no secrets)
```

**Structure Decision**: Single project layout extending the existing `src/` and `tests/` directories. `infra/` holds all CloudFormation templates (one per feature as needed). `scripts/` holds post-deploy operational tooling that cannot be expressed in CloudFormation (e.g., permanent password setting).

**CloudFormation / Script split rationale**: `AWS::Cognito::UserPoolUser` can create users but cannot set permanent passwords — users land in `FORCE_CHANGE_PASSWORD` state. A Lambda custom resource could solve this but violates Simplicity First for a 2-user demo. The pragmatic split: CFN owns all infrastructure; a minimal `scripts/provision_users.py` handles the permanent-password-only step that CFN cannot perform natively.

---

## Phase 0: Research (Complete)

See [research.md](research.md) for full findings. Key decisions:

| Decision | Choice | Reference |
|---|---|---|
| OAuth2 implementation | Manual flow with `authlib` (PKCE + state) | research.md §1 |
| Streamlit session detection | `st.query_params` (reads `?code=` from callback URL) | research.md §1 |
| Session storage | `st.session_state` (server-side in-memory) | research.md §1 |
| AWS infrastructure provisioning | CloudFormation (`infra/cognito.yaml`) for User Pool, App Client, Domain | research.md §2 |
| User provisioning | Post-deploy `scripts/provision_users.py` with `admin_set_user_password(Permanent=True)` | research.md §2 |
| Config loading | `python-dotenv` from `.env` | research.md §3 |
| CSRF protection | `secrets.token_urlsafe(32)` state parameter | research.md §4 |
| PKCE | S256 (even for confidential client) | research.md §4 |
| New dependency | `authlib>=1.3.2` | research.md §4 |

---

## Phase 1: Design (Complete)

### Data Model
See [data-model.md](data-model.md). Three entities:
- `UserSession` — in-memory authenticated session (stored in `st.session_state`)
- `OAuthPendingState` — short-lived CSRF + PKCE state during login flow
- `CognitoConfig` — app-level config loaded from `.env` at startup

### Interface Contracts
See [contracts/cognito-oauth2.md](contracts/cognito-oauth2.md). Covers:
- Authorization request parameters (app → Cognito)
- Callback handling obligations (Cognito → app)
- Token exchange request/response format
- Logout endpoint
- Callback URL registration requirement

### Quickstart
See [quickstart.md](quickstart.md). Covers AWS setup, `.env` configuration, provisioning script, app launch, and troubleshooting.

---

## Implementation Notes for Tasks Phase

The following implementation sequence is recommended (for `/speckit.tasks`):

> **MCP reminder**: Use the AWS MCP server when authoring the CloudFormation template (resource types, property names, Cognito-specific constraints). Use the Strands Agents MCP server for any Strands SDK integration questions.

**Group A — Infrastructure (CloudFormation)**
1. **Author `infra/cognito.yaml`** — CloudFormation template defining: `AWS::Cognito::UserPool`, `AWS::Cognito::UserPoolDomain`, `AWS::Cognito::UserPoolClient` (Hosted UI + authorization code grant); export stack outputs (User Pool ID, Client ID, Client Secret, Domain)
2. **Deploy CloudFormation stack** — `aws cloudformation deploy --template-file infra/cognito.yaml --stack-name strands-demo-cognito`
3. **Populate `.env`** — copy stack outputs into `.env` (User Pool ID, Client ID, Client Secret, Domain, Region)

**Group B — User Provisioning**
4. **Create `scripts/provision_users.py`** — reads from `.env`; calls `admin_create_user` + `admin_set_user_password(Permanent=True)` for `demo_user_1` and `demo_user_2`; idempotent (safe to re-run)
5. **Run provisioning script** — `uv run python scripts/provision_users.py`

**Group C — Application Code**
6. **Add `authlib` dependency** to `pyproject.toml` + `uv sync`
7. **Create `.env.example`** — committed to repo with placeholder variable names (no secrets)
8. **Implement `src/auth/config.py`** — load and validate all env vars at startup; fail fast with clear error
9. **Implement `src/auth/oauth.py`** — build authorization URL with state + PKCE; exchange code for tokens; parse ID token claims
10. **Implement `src/auth/session.py`** — thin helpers: `is_authenticated()`, `get_user()`, `clear_session()`
11. **Update `app.py`** — auth gate: if not authenticated, show login landing; if callback detected, run code exchange; if authenticated, show main app with logout button

**Group D — Tests & Verification**
12. **Write unit tests** — `test_config.py` (missing var errors), `test_oauth.py` (URL construction, state validation)
13. **Smoke test** end-to-end with both test users (`demo_user_1`, `demo_user_2`)
