# Data Model: Cognito Login (002)

**Date**: 2026-03-09
**Branch**: `002-cognito-login`

---

## Entities

### UserSession

Represents an authenticated user's in-memory session within Streamlit. Created on successful OAuth2 token exchange; destroyed on logout or tab close.

| Field | Type | Description | Source |
|---|---|---|---|
| `access_token` | `str` | OAuth2 access token for authorized API calls | Cognito token endpoint |
| `id_token` | `str` | JWT containing user identity claims | Cognito token endpoint |
| `refresh_token` | `str` | Long-lived token to obtain new access tokens | Cognito token endpoint |
| `username` | `str` | Cognito username (from `cognito:username` claim in ID token) | Decoded from `id_token` |
| `email` | `str \| None` | User's email address (from `email` claim) | Decoded from `id_token` |
| `expires_at` | `int` | Unix timestamp when access token expires | Derived: `time.time() + expires_in` |

**Storage**: `st.session_state["user_session"]` (server-side, in-memory only)
**Lifecycle**: Created → active → expired (redirect to login) or destroyed (logout)
**Identity rule**: One session per Streamlit browser tab; identified by Streamlit's internal session ID.

---

### OAuthPendingState

Short-lived state held between the login redirect and the Cognito callback. Prevents CSRF and binds the PKCE code verifier to the flow.

| Field | Type | Description |
|---|---|---|
| `state` | `str` | Random CSRF token (`secrets.token_urlsafe(32)`) |
| `code_verifier` | `str` | PKCE code verifier (random 43-128 char URL-safe string) |

**Storage**: `st.session_state["oauth_pending"]` (cleared immediately after successful code exchange or on mismatch)
**Lifecycle**: Created just before authorization redirect → validated and destroyed on callback

---

### CognitoConfig

Application-level configuration loaded once at startup from `.env`. Not stored in session state.

| Field | Type | Source |
|---|---|---|
| `user_pool_id` | `str` | `COGNITO_USER_POOL_ID` env var |
| `client_id` | `str` | `COGNITO_CLIENT_ID` env var |
| `client_secret` | `str` | `COGNITO_CLIENT_SECRET` env var |
| `domain` | `str` | `COGNITO_DOMAIN` env var |
| `redirect_uri` | `str` | `COGNITO_REDIRECT_URI` env var |
| `region` | `str` | `AWS_REGION` env var |

**Validation**: All fields required; application MUST fail fast at startup with a descriptive error if any field is missing.

---

## State Transitions

```
[Unauthenticated]
      │
      │ user clicks Login
      ▼
[Pending OAuth] ── state mismatch ──► [Unauthenticated] (error shown)
      │
      │ Cognito redirects with valid code+state
      ▼
[Token Exchange]
      │ success              │ failure
      ▼                      ▼
[Authenticated]        [Unauthenticated] (error shown)
      │
      │ user clicks Logout
      │ OR access token expires
      ▼
[Unauthenticated]
```

---

## Relationships

- One `CognitoConfig` is shared across all sessions (loaded at app startup).
- One `OAuthPendingState` exists per tab during the login flow only.
- One `UserSession` exists per tab when authenticated.
- `UserSession` has no persistent representation — it lives entirely in memory and is not written to any database or file.
