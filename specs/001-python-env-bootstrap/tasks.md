---

description: "Task list for Python Environment Bootstrap"
---

# Tasks: Python Environment Bootstrap

**Input**: Design documents from `/specs/001-python-env-bootstrap/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, quickstart.md ✅

**Tests**: Not requested — no test tasks generated.

**Organization**: Tasks are grouped by user story to enable independent implementation
and validation of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in all descriptions

## Path Conventions

All deliverables are at the repository root (no `src/` — config/metadata only feature).

---

## Phase 1: Setup

**Purpose**: Initialize uv project structure in the existing repository root.

- [x] T001 Initialize uv project in repo root: run `uv init --app .` to generate `pyproject.toml` and `.python-version` scaffolds — then inspect and delete any uv-generated sample file (e.g., `hello.py`, `main.py`) that is not part of the planned deliverables

---

## Phase 2: User Story 1 - Developer Can Run the Project Locally (Priority: P1) 🎯 MVP

**Goal**: A developer clones the repo, runs two commands, and can import all core packages
without errors.

**Independent Test**: Run `uv sync` on a clean clone, then execute
`uv run python -c "import strands; import streamlit; import boto3; print('OK')"` —
output must be `OK` with no errors.

### Implementation for User Story 1

- [x] T002 [US1] Configure project metadata in `pyproject.toml`: set `name = "strands-demo"`, `version = "0.1.0"`, `description`, `readme = "README.md"`, `requires-python = ">=3.11"`, and `authors = [{name = "<your name>", email = "<your email>"}]`
- [x] T003 [P] [US1] Declare runtime dependencies in `pyproject.toml` under `[project].dependencies`: `strands-agents>=0.1.0`, `strands-agents-tools>=0.1.0`, `streamlit>=1.35.0`, `boto3>=1.34.0`, `python-dotenv>=1.0.0`
- [x] T004 [P] [US1] Declare dev dependency group in `pyproject.toml` under `[dependency-groups].dev`: `pytest>=8.0`, `pytest-cov>=5.0`
- [x] T005 [US1] Run `uv sync` to resolve dependencies, generate `uv.lock`, and create `.venv` — verify exit code 0 and all packages importable
- [x] T006 [US1] Create `.env.example` at repo root with all required placeholder variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_REGION`, `COGNITO_USER_POOL_ID`, `COGNITO_APP_CLIENT_ID`, `COGNITO_APP_CLIENT_SECRET`, `COGNITO_DOMAIN`, `COGNITO_REDIRECT_URI`, `COGNITO_REGION` — each with inline comment describing its purpose
- [x] T007 [US1] Create `README.md` at repo root with: project overview, prerequisites section (uv install link), setup commands (`git clone` → `uv sync` → `cp .env.example .env`), and import verification command

**Checkpoint**: At this point, User Story 1 is fully functional. A developer can clone
and have a working environment in under 5 minutes.

---

## Phase 3: User Story 2 - Developer Can Add and Track New Dependencies (Priority: P2)

**Goal**: Document and validate the workflow for adding new packages so that all
developers get consistent environments going forward.

**Independent Test**: Run `uv add <package>`, then verify `pyproject.toml` and `uv.lock`
both contain the new package. On a second machine, `uv sync` installs the same version.

### Implementation for User Story 2

- [x] T008 [US2] Add "Managing Dependencies" section to `README.md` documenting: `uv add <package>` for runtime deps, `uv add --dev <package>` for dev deps, and the note that `uv.lock` must be committed after adding
- [x] T009 [US2] Validate dependency tracking: run `uv add requests`, verify `requests` appears in `pyproject.toml` under `[project].dependencies` and in `uv.lock`, then run `uv remove requests` to clean up — confirm both files revert

**Checkpoint**: User Story 2 complete. Adding a dependency updates both `pyproject.toml`
and `uv.lock` automatically.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and commit of all generated artifacts.

- [x] T010 [P] Verify idempotency: run `uv sync` a second time on the configured environment — must complete without errors (SC-004)
- [x] T011 [P] Verify `.gitignore` excludes `.venv/` and `.env` but does NOT exclude `.env.example` or `uv.lock`
- [x] T012 Create minimal `app.py` stub at repo root containing a single Streamlit placeholder page (title + "Coming soon" message) so that `streamlit run app.py` is launchable — satisfies constitution Development Workflow requirement
- [x] T013 Run full quickstart validation per `specs/001-python-env-bootstrap/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **User Story 1 (Phase 2)**: Depends on Phase 1 (uv init must create pyproject.toml first)
- **User Story 2 (Phase 3)**: Depends on Phase 2 completion (needs working pyproject.toml + uv.lock)
- **Polish (Phase 4)**: Depends on both user stories complete

### Within User Story 1

- T002 MUST complete before T003/T004 (metadata before deps)
- T003 and T004 CAN run in parallel (different sections of same file — coordinate carefully)
- T005 MUST follow T003 and T004 (sync requires complete dep declarations)
- T006 and T007 CAN run in parallel after T005 (independent files)

### Within User Story 2

- T008 and T009 CAN run in parallel (different concerns, same README target — coordinate)

### Parallel Opportunities

```bash
# After T002, launch T003 and T004 together:
Task: "T003 — Declare runtime deps in pyproject.toml"
Task: "T004 — Declare dev deps in pyproject.toml"

# After T005, launch T006 and T007 together:
Task: "T006 — Create .env.example"
Task: "T007 — Create README.md"

# In Polish phase, T010 and T011 can run together:
Task: "T010 — Verify idempotency"
Task: "T011 — Verify .gitignore"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: User Story 1 (T002–T007)
3. **STOP and VALIDATE**: Run quickstart import check
4. All core dependencies installed, secrets template in place, README ready

### Incremental Delivery

1. Complete Setup + User Story 1 → working environment (MVP)
2. Add User Story 2 → dependency management documented and validated
3. Polish → idempotency verified, app.py stub created, everything committed

---

## Notes

- [P] tasks operate on different files or independent concerns — coordinate on `pyproject.toml`
  edits (T003/T004) by editing separate sections sequentially if running alone
- T001 (`uv init --app .`) is safe to run in an existing git repo with no `pyproject.toml`
- `uv.lock` and `.python-version` are auto-generated by uv — do not hand-edit
- Commit order after completion: `pyproject.toml`, `.python-version`, `uv.lock`,
  `.env.example`, `README.md`
