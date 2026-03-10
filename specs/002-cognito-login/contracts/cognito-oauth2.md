# Contract: Cognito OAuth2 Interface (002)

**Date**: 2026-03-09
**Branch**: `002-cognito-login`

This document defines the interface contracts between the Strands Demo application and the AWS Cognito Hosted UI (OAuth2 authorization server).

---

## 1. Authorization Request (App → Cognito)

The app redirects the user's browser to Cognito's authorization endpoint.

**Endpoint**: `GET {COGNITO_DOMAIN}/oauth2/authorize`

| Parameter | Required | Value |
|---|---|---|
| `response_type` | Yes | `code` |
| `client_id` | Yes | `{COGNITO_CLIENT_ID}` |
| `redirect_uri` | Yes | `{COGNITO_REDIRECT_URI}` (must match App Client configuration exactly) |
| `scope` | Yes | `openid email profile` |
| `state` | Yes | Random CSRF token (`secrets.token_urlsafe(32)`) |
| `code_challenge` | Yes | SHA-256 hash of `code_verifier`, base64url-encoded |
| `code_challenge_method` | Yes | `S256` |

**Pre-conditions**: `state` and `code_verifier` stored in `st.session_state["oauth_pending"]` before redirect.

---

## 2. Authorization Callback (Cognito → App)

Cognito redirects back to the app's callback URL after authentication.

**URL**: `{COGNITO_REDIRECT_URI}?code={auth_code}&state={state}`

| Query Parameter | Description |
|---|---|
| `code` | Single-use authorization code; valid for 10 minutes; MUST be exchanged immediately |
| `state` | Echoed verbatim from the authorization request; MUST match stored `state` |

**Error case**: `{COGNITO_REDIRECT_URI}?error={error_code}&error_description={description}`

| Error Code | Meaning |
|---|---|
| `access_denied` | User cancelled login on Hosted UI |
| `invalid_request` | Malformed authorization request |

**App obligations on callback**:
1. Validate `state` matches `st.session_state["oauth_pending"]["state"]` — reject and show error if mismatch.
2. Exchange `code` for tokens (see §3) within the same Streamlit re-render.
3. Clear `st.query_params` after successful exchange.
4. Delete `st.session_state["oauth_pending"]` after use (success or failure).

---

## 3. Token Exchange (App → Cognito)

The app exchanges the authorization code for tokens directly (server-side, not in browser).

**Endpoint**: `POST {COGNITO_DOMAIN}/oauth2/token`

**Request**:
- Content-Type: `application/x-www-form-urlencoded`

| Body Parameter | Value |
|---|---|
| `grant_type` | `authorization_code` |
| `client_id` | `{COGNITO_CLIENT_ID}` |
| `client_secret` | `{COGNITO_CLIENT_SECRET}` |
| `redirect_uri` | `{COGNITO_REDIRECT_URI}` |
| `code` | Authorization code from callback |
| `code_verifier` | Original PKCE verifier from `st.session_state["oauth_pending"]` |

**Success Response** (200 OK, JSON):

| Field | Type | Description |
|---|---|---|
| `access_token` | `str` | Short-lived access token |
| `id_token` | `str` | JWT with user identity claims |
| `refresh_token` | `str` | Long-lived token |
| `expires_in` | `int` | Seconds until access token expires |
| `token_type` | `str` | Always `"Bearer"` |

**Error Response** (400, JSON): `{"error": "...", "error_description": "..."}`

---

## 4. Logout (App → Cognito)

**Endpoint**: `GET {COGNITO_DOMAIN}/logout`

| Parameter | Value |
|---|---|
| `client_id` | `{COGNITO_CLIENT_ID}` |
| `logout_uri` | `{COGNITO_REDIRECT_URI}` (must be in allowed sign-out URLs list) |

The app also clears `st.session_state["user_session"]` locally before redirecting.

---

## 5. Callback URL Registration Requirement

The `COGNITO_REDIRECT_URI` value MUST be registered in the Cognito App Client's **Allowed callback URLs** list. The match is exact (including trailing slash). Mismatch causes Cognito to reject the authorization request with `invalid_request`.

For local development: `http://localhost:8501`
For deployed environments: the public HTTPS URL of the Streamlit app.
