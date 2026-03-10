# Feature Specification: Cognito Login

**Feature Branch**: `002-cognito-login`
**Created**: 2026-03-09
**Status**: Draft
**Input**: User description: "Add a login functionality using Amazon Cognito. You can assume that credentials are available in .env file to interact with AWS account. Also, create two users in cognito that can login into the application with simple passwords."

## Clarifications

### Session 2026-03-09

- Q: Should users log in via a custom form embedded in the app, or be redirected to a provider-hosted login page? → A: Redirect to identity provider's hosted login page (OAuth2 redirect flow).
- Q: Are the two pre-provisioned users the same type, or do they represent different roles? → A: Same role — both are identical regular users with equal access, provisioned to verify multi-user login works.
- Q: Should authentication events be logged by the application for audit/debugging purposes? → A: No application-level logging required; rely on the identity provider's own audit logs.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Successful Login (Priority: P1)

A registered user visits the application and is presented with a "Login" button. Clicking it redirects them to the identity provider's hosted login page. They enter their credentials there, and upon successful authentication are redirected back to the main application with their session established.

**Why this priority**: Login is the gateway to the entire application. Without it, no other feature can be accessed. This is the core value of the feature.

**Independent Test**: Can be fully tested by clicking the login button with one of the two pre-created users, completing authentication on the hosted login page, and verifying the main application screen is shown.

**Acceptance Scenarios**:

1. **Given** an unauthenticated user on the application, **When** they click the Login button, **Then** they are redirected to the identity provider's hosted login page.
2. **Given** a user who has completed authentication on the hosted login page, **When** they are redirected back to the application, **Then** they land on the main application view with their identity visible (e.g., username displayed).
3. **Given** a logged-in user, **When** they navigate to the application root, **Then** they are shown the main application directly (no re-login required).

---

### User Story 2 - Failed Login Attempt (Priority: P2)

A user attempts to log in but cancels or abandons the process on the identity provider's hosted login page. When they are returned to the application, the system shows a clear error message on the landing page and does not grant access. The Login button remains available for a retry.

Note: Incorrect password and empty-field validation are handled entirely by the identity provider's hosted login page — the application is not responsible for those behaviors and cannot test them directly.

**Why this priority**: Clear feedback on failure is essential for usability and prevents user frustration. Without it the P1 story is incomplete from a user experience perspective.

**Independent Test**: Can be fully tested by clicking Login, cancelling on the identity provider's hosted login page, and verifying the app shows a friendly error message with the Login button still visible and no main app content shown.

**Acceptance Scenarios**:

1. **Given** a user who cancelled or aborted on the hosted login page, **When** the identity provider redirects them back to the application with an error code, **Then** a user-friendly error message is shown on the landing page (e.g., "Login was cancelled or failed. Please try again.") and no main application content is accessible.
2. **Given** an error has been shown after a failed login attempt, **When** the user clicks the Login button again, **Then** a new authentication attempt begins (fresh redirect to the hosted login page).

---

### User Story 3 - Logout (Priority: P3)

A logged-in user can explicitly end their session. After logout, they are returned to the login page and cannot access protected areas without logging in again.

**Why this priority**: Session termination is a basic security requirement. It is lower priority than login itself but needed for a complete, secure feature.

**Independent Test**: Can be fully tested by logging in, clicking logout, and confirming the login page is shown and the protected area is no longer accessible.

**Acceptance Scenarios**:

1. **Given** a logged-in user, **When** they click the logout button, **Then** their session is ended and they are redirected to the login page.
2. **Given** a user who has logged out, **When** they attempt to access a protected page directly, **Then** they are redirected to the login page.

---

### Edge Cases

- What happens when the identity provider is temporarily unavailable? The user sees a friendly error message and is not granted access.
- What happens after multiple consecutive failed login attempts? The account may be locked by the identity provider; the user should see an informative message.
- What happens if the user's session token expires mid-session? Session expiry detection is deferred to a future feature; for this demo, users may encounter unexpected behavior after the token TTL and can re-login by refreshing the page.
- Input validation (whitespace, empty fields, username format) is handled by the identity provider's hosted login page; the application has no responsibility for these cases.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The application MUST display a landing page for unauthenticated users with a clearly visible "Login" button.
- **FR-002**: Clicking the Login button MUST redirect the user to the identity provider's hosted login page (OAuth2 authorization code flow); the application does NOT render its own username/password form.
- **FR-003**: After the user authenticates on the hosted login page, the identity provider MUST redirect back to a configured callback URL within the application, and the application MUST exchange the returned authorization code for a valid session.
- **FR-004**: Upon successful authentication, the system MUST redirect the user to the main application view.
- **FR-005**: Upon failed authentication, the system MUST display a user-friendly error message without exposing internal error details or confirming whether a username exists.
- **FR-006**: The system MUST maintain an authenticated session so the user does not need to re-login on page navigation within the same browser tab session (hard refresh may require re-authentication; this is acceptable for a demo).
- **FR-007**: The application MUST provide a logout mechanism that terminates the user's session and redirects to the login page.
- **FR-008**: The system MUST protect all non-login pages from unauthenticated access by redirecting to the login page.
- **FR-009**: Two user accounts MUST be provisioned in the identity provider with simple passwords to enable immediate testing and demonstration of the login feature. Both accounts are regular users with identical access — no role differentiation is required.
- **FR-010**: User credentials (identity provider configuration, secrets) MUST be read from environment configuration and never hardcoded in source code.

### Key Entities

- **User Account**: A registered identity with a username and password, existing within the identity provider. Has attributes: username, email (optional), status (active/inactive).
- **Session**: A time-bounded authenticated context for a user. Created on successful login, destroyed on logout or expiry.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user with valid credentials can complete the login process and reach the main application in under 5 seconds under normal conditions.
- **SC-002**: 100% of login attempts with invalid credentials are rejected and result in an error message — no unauthorized access is ever granted.
- **SC-003**: Both pre-provisioned test users can log in successfully on the first attempt with their assigned credentials.
- **SC-004**: 100% of protected application routes redirect unauthenticated users to the login page.
- **SC-005**: After logout, re-accessing a protected route without logging in fails 100% of the time.

## Assumptions

- Authentication uses the OAuth2 authorization code flow via the identity provider's Hosted UI; the app client must be configured with an allowed callback URL.
- Credentials for connecting to the identity provider (region, user pool ID, app client ID, app client secret, hosted UI domain, callback URL, etc.) are stored in a `.env` file in the project root and loaded at application startup.
- The two pre-provisioned users will use simple passwords (e.g., 8+ characters with mixed case) that satisfy the identity provider's minimum password policy.
- User registration (sign-up) is out of scope; the application only supports login for pre-existing accounts.
- Password reset / forgot-password flow is out of scope for this feature.
- Multi-factor authentication (MFA) is not required for this feature.
- The application is a single-page web application accessed via a browser; mobile app support is out of scope.
- Session duration follows the identity provider's default token expiry settings.
- The application does not emit its own audit logs for authentication events; audit trails are managed entirely by the identity provider.
