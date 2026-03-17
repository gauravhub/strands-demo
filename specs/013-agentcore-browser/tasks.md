# Tasks: AgentCore Browser Integration

**Input**: Design documents from `/specs/013-agentcore-browser/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: No test tasks — not explicitly requested. Validation is manual via Streamlit chat.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Dependencies & Configuration)

**Purpose**: Install dependencies and configure environment

- [x] T001 Install `playwright` and `nest-asyncio` dependencies and update `pyproject.toml` with these new dependencies
- [x] T002 [P] Add `RETAIL_STORE_URL` environment variable to `.env.example` with default value `http://k8s-ui-ui-6353f3da9d-613966318.us-east-1.elb.amazonaws.com`
- [x] T003 [P] Add `RETAIL_STORE_URL` to `.env` with the ALB URL value
- [x] T004 Verify `strands_tools.browser.AgentCoreBrowser` imports successfully (`python3 -c "from strands_tools.browser import AgentCoreBrowser; print('OK')"`)

---

## Phase 2: Foundational (Browser Tool Loading)

**Purpose**: Add browser tool loader following existing patterns — MUST complete before user stories

- [x] T005 Add `load_browser_tools()` function in `src/agent/mcp_tools.py` that creates `AgentCoreBrowser(region=os.environ.get("AWS_REGION", "us-east-1"))` and returns `[browser_tool.browser]`, with try/except returning `[]` on failure (matching existing graceful degradation pattern)
- [x] T006 Update `create_agent()` in `src/agent/chatbot.py` to call `load_browser_tools()`, merge browser tools into the agent's tool list (`tools = [*gateway_tools, *eks_tools, *aws_api_tools, *browser_tools]`), and update the log message to include browser tool count
- [x] T007 Add a `system_prompt` parameter to the `Agent()` constructor call in `src/agent/chatbot.py` that mentions browser capabilities, includes `RETAIL_STORE_URL` as the default browsing target, and instructs the agent to always stop browser sessions after use

**Checkpoint**: Agent loads with browser tools available. Other tools still work. If browser import fails, agent loads without browser tools.

---

## Phase 3: User Story 1 - Take a Screenshot of a Website (Priority: P1) 🎯 MVP

**Goal**: User asks for a screenshot and sees it displayed inline in the chat with a description

**Independent Test**: Type "take a screenshot of the retail store" — screenshot appears inline, agent describes the page

**Depends on**: Phase 2 (browser tool must be loaded)

### Implementation for User Story 1

- [x] T008 [US1] Update `src/chat/ui.py` to detect base64 image data in tool results and render with `st.image()` — check if tool result contains base64 PNG data (e.g., starts with `data:image/` or contains PNG header pattern) and render as image instead of markdown text, within the existing "🛠 Tools Used" expander
- [x] T009 [US1] Deploy and test: run `streamlit run app.py`, type "take a screenshot of the retail store" in chat, verify screenshot displays inline and agent describes page content
- [x] T010 [US1] Verify browser session cleanup: after the screenshot interaction, confirm no orphaned sessions exist (`aws bedrock-agentcore list-browser-sessions` or check AgentCore console)

**Checkpoint**: Screenshots display inline in chat, agent describes page content, sessions cleaned up

---

## Phase 4: User Story 2 - Browse and Describe a Web Page (Priority: P2)

**Goal**: User asks the agent to browse a page and get a text-only description

**Independent Test**: Type "browse the retail store and tell me what products are available" — agent returns text summary

**Depends on**: Phase 2 (browser tool loaded — no dependency on US1)

### Implementation for User Story 2

- [x] T011 [US2] Test text-only browsing: type "what's on the retail store homepage?" in chat, verify agent navigates and returns a text summary of page content (headings, navigation, products) without a screenshot
- [x] T012 [US2] Test with arbitrary URL: type "browse https://example.com and describe what you see" to verify the agent works with any public URL

**Checkpoint**: Agent can browse any URL and return text descriptions

---

## Phase 5: User Story 3 - Graceful Degradation (Priority: P3)

**Goal**: Verify agent works normally when browser tools are unavailable

**Independent Test**: Misconfigure browser, verify non-browser queries still work

**Depends on**: Phase 2

### Implementation for User Story 3

- [x] T013 [US3] Verify existing tools unaffected: with browser tools loaded, type a non-browser query (e.g., "search for Python tutorials" or "list my EKS clusters") and confirm the agent responds normally using Tavily/EKS/AWS API tools
- [x] T014 [US3] Test browser error handling: type "take a screenshot of https://nonexistent.invalid" and verify the agent reports the error gracefully without crashing

**Checkpoint**: Existing capabilities work alongside browser tools, errors handled gracefully

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [x] T015 Verify `streamlit run app.py` works with all tools (browser + Tavily + EKS + AWS API) loading successfully — check logs for tool counts
- [x] T016 [P] Verify `.env.example` documents `RETAIL_STORE_URL` for new deployments

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (dependencies must be installed first)
- **User Story 1 (Phase 3)**: Depends on Phase 2 (browser tool must be loaded)
- **User Story 2 (Phase 4)**: Depends on Phase 2 (can run in parallel with US1 if desired)
- **User Story 3 (Phase 5)**: Depends on Phase 2
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1 — Screenshot)**: Requires Phase 2 + UI changes in T008
- **US2 (P2 — Browse/Describe)**: Requires Phase 2 only — no UI changes needed (text output works with existing rendering)
- **US3 (P3 — Graceful Degradation)**: Requires Phase 2 — validation-only tasks

### Parallel Opportunities

- T002 and T003 can run in parallel (different files)
- T005 and T007 could be parallel but T006 depends on T005
- US1 and US2 can run in parallel after Phase 2
- T015 and T016 can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Phase 1: Install dependencies, set env vars
2. Complete Phase 2: Add browser tool loading + system prompt
3. Complete Phase 3: Screenshot rendering in UI
4. **STOP and VALIDATE**: Screenshot appears in chat with description

### Incremental Delivery

1. Setup + Foundational → Browser tool loads
2. US1 → Screenshots display inline (MVP!)
3. US2 → Text-only browsing works
4. US3 → Graceful degradation confirmed
5. Polish → Final validation

---

## Notes

- The `AgentCoreBrowser` from `strands-agents-tools` handles all browser lifecycle (start, navigate, screenshot, stop) automatically
- No custom tool wrappers needed — the pre-built tool is a single object added to the agent's tool list
- Screenshot detection in UI is the main new code — everything else is wiring existing components
- The agent's system prompt is the key to good user experience — it tells the agent about the retail store URL and browser capabilities
