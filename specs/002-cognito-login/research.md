# Research: Cognito Login (002)

**Date**: 2026-03-09
**Branch**: `002-cognito-login`

---

## 1. OAuth2 Authorization Code Flow in Streamlit

### Decision
Use a **manual OAuth2 implementation** with `authlib` for the token exchange and PKCE generation, reading all config from `.env` via `python-dotenv`.

### Rationale
- The user spec mandates credentials live in `.env`. Streamlit's native `st.login()` requires `secrets.toml`, creating a second config surface — rejected for simplicity.
- A manual implementation is ~50 lines of straightforward code: build authorization URL → redirect → detect `?code=` in `st.query_params` → POST to token endpoint → store tokens in `st.session_state`.
- `authlib` adds clean PKCE (`code_verifier` / `code_challenge`) generation without reinventing crypto primitives.
- `boto3` is NOT used for the OAuth2 token exchange; it only handles User Pool admin operations (user provisioning).

### Alternatives Considered
| Alternative | Rejected Because |
|---|---|
| Streamlit native `st.login()` | Requires `secrets.toml`; conflicts with `.env`-only spec requirement |
| `requests-oauthlib` | Superseded by `authlib`; less maintained |
| Raw `requests` POST only | No PKCE support without manual crypto; `authlib` is marginal cost for safety gain |

### Flow Detail
1. App detects unauthenticated user → renders Login button.
2. On click: generate `state` (random token, stored in `st.session_state`) and PKCE `code_verifier`/`code_challenge`; build Cognito authorization URL; redirect browser via `st.markdown` JavaScript redirect or `st.link_button`.
3. Cognito Hosted UI handles user authentication; redirects to `COGNITO_REDIRECT_URI?code=...&state=...`.
4. App (on re-render) reads `st.query_params`: if `code` present, validate `state`, POST to `{COGNITO_DOMAIN}/oauth2/token` with `code`, `code_verifier`, `client_id`, `client_secret`, `redirect_uri`.
5. Store `access_token`, `id_token`, `refresh_token`, `username` in `st.session_state`; clear query params; render main app.

### Session Persistence
`st.session_state` persists within a browser tab session (survives re-runs, not hard refresh). For this demo, this is acceptable — the user spec does not require persistence beyond tab session. Hard refresh triggers re-authentication via the same OAuth2 flow.

---

## 2. AWS Infrastructure Provisioning

### Decision
Use **CloudFormation** (`infra/cognito.yaml`) to provision all AWS infrastructure. A minimal post-deploy `scripts/provision_users.py` (boto3) handles test user creation only, since CloudFormation cannot set permanent passwords natively.

### CloudFormation Resources
| CFN Resource Type | Purpose |
|---|---|
| `AWS::Cognito::UserPool` | User Pool with email/username sign-in, password policy |
| `AWS::Cognito::UserPoolDomain` | Hosted UI domain (Cognito-managed subdomain) |
| `AWS::Cognito::UserPoolClient` | App client: confidential, authorization code grant, Hosted UI scopes |

Stack outputs to export (consumed by `.env`):
- `UserPoolId`, `UserPoolClientId`, `UserPoolClientSecret`, `UserPoolDomain`, `CognitoRegion`

> **MCP note**: Use the AWS MCP server to look up current `AWS::Cognito::UserPool` and `AWS::Cognito::UserPoolClient` property names and valid values before authoring the template.

### User Provisioning (post-deploy script)
`scripts/provision_users.py` uses boto3 `cognito-idp`:
1. `admin_create_user(UserPoolId, Username, TemporaryPassword, MessageAction='SUPPRESS')` — creates user, suppresses welcome email.
2. `admin_set_user_password(UserPoolId, Username, Password, Permanent=True)` — transitions user from `FORCE_CHANGE_PASSWORD` to `CONFIRMED`.

Script is **idempotent** — safe to re-run if the user already exists (catches `UsernameExistsException` and calls `admin_set_user_password` only).

### Why Not Pure CloudFormation for Users?
`AWS::Cognito::UserPoolUser` creates users but cannot set permanent passwords — users remain in `FORCE_CHANGE_PASSWORD`. Bypassing this natively requires a Lambda-backed Custom Resource, which violates Simplicity First for a 2-user demo. The boto3 script is the minimal viable solution.

### Alternatives Considered
| Alternative | Rejected Because |
|---|---|
| Console-based manual setup | Not reproducible, not version-controlled |
| Terraform / CDK | Adds non-Python toolchain without benefit for this scope |
| Pure CloudFormation for users (with Lambda custom resource) | Over-engineered for 2 demo users |

### Required App Client Settings (encoded in CFN template)
| Setting | Value |
|---|---|
| App type | Confidential client (has client secret) |
| Allowed OAuth flows | Authorization code grant only |
| Allowed scopes | `openid`, `email`, `profile` |
| Callback URL | `http://localhost:8501` (dev) |
| Sign-out URL | `http://localhost:8501` |
| Hosted UI | Enabled (Cognito domain required) |

---

## 3. Environment Configuration

### Decision
Use `python-dotenv` (already in `pyproject.toml`) to load from `.env` at startup.

### Required Variables
```
AWS_REGION                  # e.g. us-east-1
COGNITO_USER_POOL_ID        # e.g. us-east-1_XXXXXXXXX
COGNITO_CLIENT_ID           # App client ID
COGNITO_CLIENT_SECRET       # App client secret
COGNITO_DOMAIN              # e.g. https://my-app.auth.us-east-1.amazoncognito.com
COGNITO_REDIRECT_URI        # e.g. http://localhost:8501
```

### Rationale
`python-dotenv` is already declared as a dependency. No additional tooling required. A `.env.example` file will be committed (with placeholder values) so developers know exactly what to populate.

---

## 4. Security

### CSRF Protection
Generate `state = secrets.token_urlsafe(32)` before redirecting; store in `st.session_state["oauth_state"]`. On callback, reject if `st.query_params["state"] != st.session_state["oauth_state"]`.

### PKCE
Implement `S256` code challenge even though this is a confidential server-side client. Overhead is minimal; defense-in-depth aligns with project constitution (Security by Design). `authlib` generates both `code_verifier` and `code_challenge` with one call.

### Token Storage
Tokens stored only in `st.session_state` (server-side Streamlit memory). Not written to browser cookies, localStorage, or disk. Access tokens not logged.

### New Dependency Required
- `authlib>=1.3.2` — add to `pyproject.toml`
