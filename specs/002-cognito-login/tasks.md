# Tasks: Cognito Login

**Input**: Design documents from `/specs/002-cognito-login/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/cognito-oauth2.md ✅

**Organization**: Tasks grouped by user story to enable independent implementation and testing of each story.

> **MCP reminder** (applies throughout): Use the **AWS MCP server** for CloudFormation resource properties, Cognito API details, and IAM questions. Use the **Strands Agents MCP server** for any Strands SDK integration questions.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (no dependency on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — new directories, dependencies, and config skeleton

- [x] T001 Add `authlib>=1.3.2` to `[project].dependencies` in `pyproject.toml` and run `uv sync`
- [x] T002 [P] Create `infra/` directory (will hold CloudFormation templates)
- [x] T003 [P] Create `src/auth/__init__.py` (empty, marks auth package)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: All AWS infrastructure and shared auth primitives that MUST exist before any user story can be implemented or tested.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

> Use the **AWS MCP server** for T004 to look up `AWS::Cognito::UserPool`, `AWS::Cognito::UserPoolClient`, and `AWS::Cognito::UserPoolDomain` resource properties before authoring the template.

- [x] T004 Author `infra/cognito.yaml` CloudFormation template defining: `AWS::Cognito::UserPool` (username + email sign-in, password policy), `AWS::Cognito::UserPoolDomain` (Cognito-managed subdomain), `AWS::Cognito::UserPoolClient` (confidential client, authorization code grant, scopes: openid/email/profile, callback URL: `http://localhost:8501`); export Outputs: `UserPoolId`, `UserPoolClientId`, `UserPoolClientSecret`, `UserPoolDomain`
- [x] T005 Deploy CloudFormation stack: `aws cloudformation deploy --template-file infra/cognito.yaml --stack-name strands-demo-cognito --capabilities CAPABILITY_IAM --region us-east-1`
- [x] T006 Populate `.env` file from stack outputs (`aws cloudformation describe-stacks --stack-name strands-demo-cognito`): set `AWS_REGION`, `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID`, `COGNITO_CLIENT_SECRET`, `COGNITO_DOMAIN`, `COGNITO_REDIRECT_URI=http://localhost:8501`
- [x] T007 [P] Create `.env.example` at repo root listing all 6 required variable names with placeholder values and inline comments (no secrets)
- [x] T008 Create `scripts/provision_users.py`: reads from `.env` via `python-dotenv`; calls `admin_create_user(MessageAction='SUPPRESS')` then `admin_set_user_password(Permanent=True)` for `demo_user_1` and `demo_user_2`; idempotent (catches `UsernameExistsException`, re-sets password safely); prints credentials to console
- [x] T009 Run `uv run python scripts/provision_users.py` — verify both users created and in `CONFIRMED` state
- [x] T010 Implement `src/auth/config.py`: define `CognitoConfig` dataclass; `load_config()` reads all 6 env vars via `os.environ`; raises `EnvironmentError` with descriptive message listing missing variables if any are absent; called once at app startup

**Checkpoint**: AWS infra deployed, test users provisioned, config loader complete — user story implementation can now begin.

---

## Phase 3: User Story 1 - Successful Login (Priority: P1) 🎯 MVP

**Goal**: User clicks Login, is redirected to Cognito Hosted UI, authenticates, and returns to the main app with their username displayed.

**Independent Test**: `uv run streamlit run app.py` → click Login → complete auth on Cognito page → verify main app view shows username.

### Implementation for User Story 1

- [x] T011 [P] [US1] Implement `src/auth/session.py`: `store_session(tokens: dict, user_info: dict)` stores `UserSession` fields in `st.session_state["user_session"]`; `is_authenticated() -> bool`; `get_user() -> dict`; `clear_session()` deletes `st.session_state["user_session"]` and `st.session_state["oauth_pending"]`
- [x] T012 [P] [US1] Implement `src/auth/oauth.py` — Part A (outbound): `generate_auth_request() -> dict` generates `state` via `secrets.token_urlsafe(32)` and PKCE `code_verifier`/`code_challenge` (S256) via `authlib.integrations.requests_client`; stores both in `st.session_state["oauth_pending"]`; returns authorization URL with params: `response_type=code`, `client_id`, `redirect_uri`, `scope=openid email profile`, `state`, `code_challenge`, `code_challenge_method=S256`
- [x] T013 [US1] Implement `src/auth/oauth.py` — Part B (inbound): `exchange_code(code: str, state: str) -> dict` validates `state` against `st.session_state["oauth_pending"]["state"]` (raises `ValueError` on mismatch — log via `logging.error("CSRF state mismatch detected")`); POSTs to `{COGNITO_DOMAIN}/oauth2/token` with `grant_type=authorization_code`, `code`, `code_verifier`, `client_id`, `client_secret`, `redirect_uri`; on non-200 response log via `logging.error("Token exchange failed: %s", response.text)` and raise; returns parsed token response; `parse_id_token(id_token: str) -> dict` decodes JWT claims without verification (demo only) to extract `cognito:username` and `email`
- [x] T014 [US1] Update `app.py`: on startup call `load_config()` (fail fast if env vars missing); if `is_authenticated()`: show main app view (see T016); elif `?code=` in `st.query_params`: run token exchange flow (see T015); else: show landing page with Login button that triggers auth redirect (see T015)
- [x] T015 [US1] Update `app.py` — landing page + redirect + callback handling: render landing page with app title and Login button; on Login click store pending state and redirect browser to Cognito authorization URL; on callback (`?code=` detected): call `exchange_code()`, call `parse_id_token()`, call `store_session()`, call `st.query_params.clear()`, call `st.rerun()`; on any exception from `exchange_code()` log via `logging.error("Auth callback failed: %s", exc)` and display friendly error to user
- [x] T016 [US1] Update `app.py` — main app view: display authenticated user's username from `get_user()`; show placeholder content ("Welcome to Strands Demo"); include Logout button (wired in US3 / T022)
- [x] T017 [P] [US1] Write `tests/unit/auth/test_config.py`: test `load_config()` raises `EnvironmentError` when each required env var is missing; test successful load when all vars present (use `monkeypatch.setenv`)
- [x] T018 [P] [US1] Write `tests/unit/auth/test_oauth.py`: test `generate_auth_request()` returns URL with required params (`state`, `code_challenge`, `code_challenge_method=S256`); test `exchange_code()` raises `ValueError` on state mismatch; test `parse_id_token()` extracts username and email from a synthetic JWT payload

**Checkpoint**: User Story 1 fully functional — user can log in and see main app with username. Run `pytest tests/unit/auth/` and smoke test login end-to-end.

---

## Phase 4: User Story 2 - Failed Login Attempt (Priority: P2)

**Goal**: When a user cancels or fails on the Cognito Hosted UI, the app shows a clear error message on the landing page and does not grant access.

**Independent Test**: Click Login → on Cognito Hosted UI, cancel or close → verify app shows error message on landing page, no main app content visible.

### Implementation for User Story 2

- [x] T019 [US2] Update `app.py` callback handling: detect `?error=` in `st.query_params` (e.g., `error=access_denied`); display a user-friendly error message on the landing page ("Login was cancelled or failed. Please try again."); clear `st.session_state["oauth_pending"]` and `st.query_params` after displaying the error; Login button remains available for retry
- [x] T020 [US2] Smoke test: click Login → cancel on Cognito Hosted UI → verify `?error=access_denied` is handled → friendly error message shown → Login button visible → no main app content shown

**Checkpoint**: User Story 2 functional — failed/cancelled logins surface a friendly error and allow retry.

---

## Phase 5: User Story 3 - Logout (Priority: P3)

**Goal**: Logged-in user can end their session; returning to the app shows the landing page again.

**Independent Test**: Log in as demo_user_2 → click Logout → verify landing page shown → attempt to access main app without logging in → verify redirect to landing page.

### Implementation for User Story 3

- [x] T021 [US3] Verify `clear_session()` in `src/auth/session.py` (from T011) clears both `st.session_state["user_session"]` and `st.session_state["oauth_pending"]` — add any missing cleanup
- [x] T022 [US3] Update `app.py` — Logout button behaviour: wire Logout button (rendered in T016) to call `clear_session()` then redirect browser to `{COGNITO_DOMAIN}/logout?client_id={CLIENT_ID}&logout_uri={REDIRECT_URI}` to invalidate the Cognito session; after redirect completes, user lands back on landing page
- [x] T023 [US3] Smoke test: login as `demo_user_2` → click Logout → verify landing page shown → manually navigate to app root → verify no session restored (landing page still shown, not main app)

**Checkpoint**: All 3 user stories functional. Full login → view app → logout cycle works for both test users.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation completeness

- [x] T024 [P] Review `.env.example`: confirm all 6 env vars are listed with descriptive inline comments; commit to repo
- [x] T025 [P] Review `infra/cognito.yaml`: confirm all resource properties are correct; add inline comments explaining Hosted UI settings, callback URL, and OAuth2 scopes
- [x] T026 Run full quickstart.md validation: follow every step in `specs/002-cognito-login/quickstart.md` on a clean terminal to confirm it works end-to-end; update any steps that are wrong or missing
- [x] T027 Full end-to-end smoke test with both users: `demo_user_1` login → view app → logout; `demo_user_2` login → view app → logout; verify SC-001 through SC-005 from spec.md; for SC-001 manually time the Login button click → Cognito redirect → callback → main app sequence and confirm it completes in under 5 seconds

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories; T005 depends on T004; T006 depends on T005; T009 depends on T008; T010 can run after T006
- **User Story 1 (Phase 3)**: Depends on Phase 2 complete (especially T010); T013 depends on T012; T014-T016 depend on T011, T012, T013; T017/T018 can run in parallel once T012/T013 are drafted
- **User Story 2 (Phase 4)**: Depends on Phase 3 complete (app.py structure must exist from T014/T015)
- **User Story 3 (Phase 5)**: Depends on Phase 3 complete (T016 Logout button, T011 clear_session)
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational — no dependency on US2 or US3
- **US2 (P2)**: Requires US1's app.py callback structure (T014/T015) to exist first
- **US3 (P3)**: Requires US1's main app view (T016) and session.py (T011) to exist first

### Parallel Opportunities

- T002 and T003 can run together (Phase 1)
- T007 (`.env.example`) can run alongside T004–T006
- T011 and T012 can run in parallel (different files, no dependency)
- T017 and T018 can run in parallel once their respective source files are drafted
- T024 and T025 can run in parallel (Phase 6)

---

## Parallel Example: User Story 1

```
# These two can run simultaneously (different files):
T011: Implement src/auth/session.py
T012: Implement src/auth/oauth.py — Part A

# Then sequentially:
T013: Implement src/auth/oauth.py — Part B (depends on T012)
T014/T015/T016: Update app.py (depends on T011, T013)

# These can run in parallel once source is drafted:
T017: Write tests/unit/auth/test_config.py
T018: Write tests/unit/auth/test_oauth.py
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (deploy CFN stack, provision users, implement config.py)
3. Complete Phase 3: User Story 1 (oauth.py, session.py, app.py)
4. **STOP and VALIDATE**: Smoke test login end-to-end with demo_user_1
5. Demo: working Cognito login on localhost

### Incremental Delivery

1. Phase 1 + 2 → Infrastructure ready
2. Phase 3 → Login works (MVP demo-able)
3. Phase 4 → Error handling polished
4. Phase 5 → Logout complete
5. Phase 6 → Fully validated and documented

---

## Notes

- [P] tasks = different files, no inter-dependencies — safe to run in parallel
- [Story] label maps each task to its user story for traceability
- No test tasks are TDD-mandatory for this feature (tests in Phase 3 are post-implementation unit tests)
- Commit after each logical group (e.g., after T010, after T016, after T023)
- Stop at each **Checkpoint** to verify the story works independently before proceeding
