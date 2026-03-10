# Tasks: Deploy Streamlit App to Streamlit Community Cloud

**Input**: Design documents from `/specs/005-streamlit-cloud-deploy/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, quickstart.md

**Tests**: Not requested — no test tasks generated.

**Organization**: Tasks grouped by user story. Zero application code changes required — this feature is deployment configuration only.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Generate dependency manifest and prepare repository for SCC deployment

<!-- parallel-group: 1 (max 3 concurrent) -->
- [x] T001 [P] Generate requirements.txt at repository root from pyproject.toml dependencies — list all runtime dependencies from `[project.dependencies]` section, pin versions to match uv.lock, exclude dev dependencies
- [x] T002 [P] Verify .gitignore excludes .env, .env.*, .streamlit/secrets.toml and includes !.env.example — update /home/dhamijag/playground/strands-demo/.gitignore if needed
- [x] T003 [P] Create .streamlit/secrets.toml.example template file at /home/dhamijag/playground/strands-demo/.streamlit/secrets.toml.example with TOML-format placeholders for all required secrets (COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET, COGNITO_DOMAIN, COGNITO_REDIRECT_URI, ANTHROPIC_API_KEY, TAVILY_API_KEY, AGENTCORE_RUNTIME_ARN, AWS_REGION, LOG_LEVEL)

---

## Phase 2: Foundational (GitHub Remote)

**Purpose**: Create public GitHub repository and push code — BLOCKS all SCC deployment tasks

**⚠️ CRITICAL**: SCC cannot deploy without a GitHub remote

<!-- sequential -->
- [x] T004 Create a public GitHub repository named `strands-demo` using `gh repo create` CLI and add it as the `origin` remote
- [x] T005 Push all branches (main and feature branches) to the GitHub remote with `git push -u origin --all`

**Checkpoint**: GitHub remote is live — SCC can now connect to the repository

---

## Phase 3: User Story 1 — App Accessible on Public URL (Priority: P1) 🎯 MVP

**Goal**: Deploy the Streamlit app to SCC so users can access it from a stable public HTTPS URL

**Independent Test**: Visit the public `*.streamlit.app` URL in a browser and verify the landing page loads with the Login button visible

### Implementation for User Story 1

<!-- sequential -->
- [ ] T006 [US1] Deploy the app on Streamlit Community Cloud: go to share.streamlit.io, connect the `strands-demo` GitHub repo, set branch to `main`, set main file path to `app.py`, set Python version to 3.11 in Advanced Settings, and click Deploy
- [ ] T007 [US1] Record the assigned `*.streamlit.app` public URL in specs/005-streamlit-cloud-deploy/quickstart.md and verify the landing page loads (may show config errors until secrets are configured in US2)

**Checkpoint**: App is deployed on SCC — landing page accessible (secrets not yet configured)

---

## Phase 4: User Story 2 — Secrets Securely Configured in Cloud (Priority: P2)

**Goal**: Configure all required secrets in SCC secrets manager so the app runs identically to local setup

**Independent Test**: After configuring secrets, reboot the SCC app and confirm it loads without error; all integrations (Cognito redirect, AgentCore invocation) work end to end

### Implementation for User Story 2

<!-- sequential -->
- [ ] T008 [US2] Configure secrets in SCC dashboard (Settings → Secrets): paste TOML-format secrets with all 10 required keys from .env.example values — COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET, COGNITO_DOMAIN, COGNITO_REDIRECT_URI (set to the *.streamlit.app URL from T007), ANTHROPIC_API_KEY, TAVILY_API_KEY, AGENTCORE_RUNTIME_ARN, AWS_REGION, LOG_LEVEL
- [ ] T009 [US2] Reboot the SCC app and verify it starts without missing environment variable errors — landing page should render with Login button visible and no error banners

**Checkpoint**: SCC app is running with all secrets configured — ready for auth flow testing

---

## Phase 5: User Story 3 — Cognito Redirect URI Updated for Cloud URL (Priority: P3)

**Goal**: Register the SCC public URL as an allowed callback and logout URI in the Cognito App Client so OAuth2 login works on the deployed URL

**Independent Test**: Complete a full login flow on the SCC URL — click Login, authenticate in Cognito hosted UI, verify redirect back to the SCC app with an active session

### Implementation for User Story 3

<!-- sequential -->
- [ ] T010 [US3] Update the Cognito App Client to add the SCC public URL as an allowed callback URI and logout URI using `aws cognito-idp update-user-pool-client` — keep existing `http://localhost:8501` URIs alongside the new SCC URL
- [ ] T011 [US3] Update COGNITO_REDIRECT_URI in SCC secrets to match the exact SCC public URL (including https:// prefix, no trailing slash) and reboot the app
- [ ] T012 [US3] Perform end-to-end smoke test on the SCC URL: visit landing page → click Login → authenticate in Cognito hosted UI → verify redirect back to SCC → verify chatbot interface loads with username displayed → send a test message → verify AgentCore response streams back

**Checkpoint**: Full authentication flow works on the deployed SCC URL

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and validation

<!-- parallel-group: 2 (max 3 concurrent) -->
- [ ] T013 [P] Update specs/005-streamlit-cloud-deploy/quickstart.md with the actual SCC URL, GitHub repo URL, and any deployment notes discovered during implementation
- [ ] T014 [P] Update /home/dhamijag/playground/strands-demo/.env.example with a comment documenting the SCC secrets TOML format and a reference to .streamlit/secrets.toml.example

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately. All 3 tasks are parallel.
- **Foundational (Phase 2)**: Depends on Phase 1 (requirements.txt must exist before push). T004 → T005 sequential.
- **User Story 1 (Phase 3)**: Depends on Phase 2 (GitHub remote must exist for SCC). T006 → T007 sequential.
- **User Story 2 (Phase 4)**: Depends on Phase 3 (app must be deployed on SCC). T008 → T009 sequential.
- **User Story 3 (Phase 5)**: Depends on Phase 4 (secrets must be configured). T010 → T011 → T012 sequential.
- **Polish (Phase 6)**: Depends on Phase 5 completion. T013 and T014 are parallel.

### User Story Dependencies

- **US1 (P1)**: Depends on GitHub remote (Phase 2) — delivers deployed app with visible landing page
- **US2 (P2)**: Depends on US1 — configures secrets so app functions fully
- **US3 (P3)**: Depends on US2 — updates Cognito to enable login flow on SCC URL

**Note**: Unlike typical features, these user stories are strictly sequential because each builds on the previous deployment state.

### Parallel Opportunities

- Phase 1: All 3 setup tasks (T001, T002, T003) can run in parallel
- Phase 6: Documentation tasks (T013, T014) can run in parallel
- All other phases are sequential (deployment steps depend on previous state)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (generate requirements.txt, verify .gitignore, create secrets template)
2. Complete Phase 2: Foundational (create GitHub repo, push code)
3. Complete Phase 3: User Story 1 (deploy on SCC, verify landing page)
4. **STOP and VALIDATE**: Landing page accessible at public URL
5. Proceed to US2 (secrets) and US3 (Cognito redirect) for full functionality

### Incremental Delivery

1. Setup + Foundational → GitHub repo live
2. User Story 1 → App deployed, landing page visible (MVP!)
3. User Story 2 → Secrets configured, app starts without errors
4. User Story 3 → Full login flow works on SCC URL
5. Polish → Documentation updated with actual URLs and notes

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Zero application code changes — this feature is purely deployment configuration
- Manual SCC dashboard steps (T006, T008) require human interaction
- Commit after Phase 1 completes (new files: requirements.txt, .streamlit/secrets.toml.example)
