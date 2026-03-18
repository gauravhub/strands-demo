# Tasks: AgentCore Evaluations

**Input**: Design documents from `/specs/015-agentcore-evaluations/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Create the custom evaluator config JSON and IAM permissions documentation — foundational artifacts needed by all other phases.

<!-- parallel-group: 1 (max 3 concurrent) -->
- [ ] T001 [P] Create custom evaluator config JSON at specs/015-agentcore-evaluations/tool-selection-evaluator.json with LLM-as-a-judge config: model ID `global.anthropic.claude-sonnet-4-5-20250929-v1:0`, 3-point rating scale (0.0 Incorrect, 0.5 Partial, 1.0 Correct), and evaluation instructions that assess whether the agent selected appropriate tools (browser tools for screenshots, AWS MCP for infrastructure, EKS MCP for cluster queries, Gateway for web search). Use `{context}` and `{assistant_turn}` placeholders per AgentCore evaluator format.
- [ ] T002 [P] Create IAM permissions reference document at specs/015-agentcore-evaluations/iam-permissions.md documenting: (1) the evaluation execution role is auto-created by the CLI as `AgentCoreEvalsSDK-{region}-{hash}`, (2) it is separate from the agent's `AgentExecutionRole` in infra/agentcore/template.yaml, (3) required permissions include CloudWatch Logs read, Bedrock model invoke for judging, and evaluation results write, (4) no changes to the existing CloudFormation template are needed.

**Checkpoint**: Evaluator config JSON and IAM documentation ready.

---

## Phase 2: User Story 3 — Custom Tool Selection Evaluator (Priority: P2)

**Goal**: Create and register the custom tool_selection_accuracy evaluator so it's available for both on-demand and online evaluation.

**Independent Test**: Run `agentcore eval evaluator list` and verify tool_selection_accuracy appears alongside built-in evaluators.

**Note**: This phase is ordered before US1/US2/US4 because the custom evaluator must exist before it can be referenced in on-demand runs or online configs.

<!-- sequential -->
- [ ] T003 [US3] Register the custom evaluator by running: `agentcore eval evaluator create --name "tool_selection_accuracy" --config specs/015-agentcore-evaluations/tool-selection-evaluator.json --level TRACE --description "Evaluates whether the agent selected the correct tools for the user request"`. Verify it appears in `agentcore eval evaluator list`.

**Checkpoint**: Custom evaluator registered and visible in evaluator list.

---

## Phase 3: User Story 4 — CLI Wrapper Script (Priority: P2)

**Goal**: Create the CLI wrapper script that all other user stories depend on for convenient execution.

**Independent Test**: Run `./scripts/eval-agent.sh` with no arguments and verify usage help is displayed.

**Note**: This phase is ordered before US1/US2 because the wrapper script provides the `setup` and `run` commands those stories test.

<!-- sequential -->
- [ ] T004 [US4] Create CLI wrapper script at scripts/eval-agent.sh with: (1) shebang and set -euo pipefail, (2) usage/help function showing all subcommands with examples, (3) `run` subcommand accepting session-id and optional --days flag — runs `agentcore eval run` with all 5 evaluators (Builtin.GoalSuccessRate, Builtin.Helpfulness, Builtin.Correctness, Builtin.Faithfulness, tool_selection_accuracy), (4) `setup` subcommand that runs `agentcore eval online create` with name strands_demo_eval, 100% sampling rate, all 5 evaluators, (5) `list` subcommand that runs `agentcore eval online list`, (6) `status` subcommand accepting config-id that runs `agentcore eval online get`, (7) `create-evaluator` subcommand that runs the evaluator create command from T003 using the JSON config, (8) `list-evaluators` subcommand that runs `agentcore eval evaluator list`, (9) case statement dispatching to subcommands with default showing help. Agent ID is auto-detected by agentcore CLI from .bedrock_agentcore.yaml — do not hardcode. Make the script executable (chmod +x).

**Checkpoint**: CLI wrapper script exists and shows help when run without arguments.

---

## Phase 4: User Story 1 — Continuous Quality Monitoring (Priority: P1)

**Goal**: Set up online (continuous) evaluation with all evaluators at 100% sampling rate.

**Independent Test**: Run `./scripts/eval-agent.sh setup` and verify the online evaluation config is created with status ACTIVE. Then run `./scripts/eval-agent.sh list` to confirm it appears.

<!-- sequential -->
- [ ] T005 [US1] Run `./scripts/eval-agent.sh setup` to create the online evaluation config (strands_demo_eval) with 100% sampling rate and all 5 evaluators. Verify config status transitions to ACTIVE. Save the returned config ID for future reference.

**Checkpoint**: Online evaluation config is ACTIVE and sampling 100% of sessions.

---

## Phase 5: User Story 2 — On-Demand Session Evaluation (Priority: P1)

**Goal**: Validate that on-demand evaluation works against a real agent session with all 5 evaluators.

**Independent Test**: Invoke the agent, wait for observability data, then run `./scripts/eval-agent.sh run <session-id>` and verify scores are returned for all evaluators.

<!-- sequential -->
- [ ] T006 [US2] Invoke the deployed agent via `agentcore invoke --input "What AWS services can you help me with?"` to generate a session with observability data. Note the session ID from the output or from `agentcore obs list`.
- [ ] T007 [US2] Wait 2-5 minutes for CloudWatch logs to populate, then run `./scripts/eval-agent.sh run <session-id>` using the session from T006. Verify scores and explanations are returned for all 5 evaluators (GoalSuccessRate, Helpfulness, Correctness, Faithfulness, tool_selection_accuracy). Optionally save results with `--output results.json`.

**Checkpoint**: On-demand evaluation returns scores from all 5 evaluators for a real session.

---

## Phase 6: User Story 5 — Evaluation IAM Permissions Validation (Priority: P1)

**Goal**: Verify that the auto-created evaluation execution role has correct permissions and document them.

**Independent Test**: Check that T005 (online config creation) and T007 (on-demand eval) both completed without IAM permission errors.

<!-- sequential -->
- [ ] T008 [US5] Verify the evaluation execution role was auto-created by running `aws iam list-roles --query "Roles[?contains(RoleName, 'AgentCoreEvalsSDK')]"`. Document the role name, ARN, and attached policies in specs/015-agentcore-evaluations/iam-permissions.md (update the file created in T002 with actual values from the deployed role).

**Checkpoint**: IAM permissions documented with actual role details from deployment.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — T001 and T002 can run in parallel
- **Phase 2 (US3)**: Depends on T001 (needs the JSON config file)
- **Phase 3 (US4)**: No hard dependency — can start after Phase 1 (references evaluator names, not the registered evaluator)
- **Phase 4 (US1)**: Depends on T003 (custom evaluator must be registered) and T004 (uses wrapper script)
- **Phase 5 (US2)**: Depends on T004 (uses wrapper script) and T003 (custom evaluator for full evaluation)
- **Phase 6 (US5)**: Depends on T005 (role is auto-created during online config setup)

### User Story Dependencies

- **US3 (Custom Evaluator)**: Can start after Phase 1 — independent of other stories
- **US4 (CLI Wrapper)**: Can start after Phase 1 — independent, but provides tooling for US1/US2
- **US1 (Continuous Monitoring)**: Depends on US3 + US4 being complete
- **US2 (On-Demand Eval)**: Depends on US3 + US4 being complete
- **US5 (IAM Permissions)**: Depends on US1 (role auto-created during setup)

### Parallel Opportunities

- T001 and T002 can run in parallel (different files, no dependencies)
- T003 and T004 could run in parallel (T003 registers the evaluator, T004 creates the script — no file conflicts), but T004's `create-evaluator` subcommand references the JSON from T001
- US1 and US2 can run in parallel once US3 and US4 are complete

---

## Implementation Strategy

### MVP First (US3 + US4 → US1)

1. Complete Phase 1: Setup (T001, T002 in parallel)
2. Complete Phase 2: Register custom evaluator (T003)
3. Complete Phase 3: Create CLI wrapper (T004)
4. Complete Phase 4: Set up continuous monitoring (T005)
5. **STOP and VALIDATE**: Verify online eval config is ACTIVE

### Full Delivery

6. Complete Phase 5: On-demand evaluation validation (T006, T007)
7. Complete Phase 6: IAM documentation (T008)

---

## Notes

- This is a tooling/infrastructure feature — no Python code changes, no tests to write
- All tasks use the `agentcore` CLI — no raw AWS API calls
- The agent code in `src/agentcore/app.py` is NOT modified (FR-006)
- Agent ID is auto-detected from `.bedrock_agentcore.yaml` — never hardcoded
- Total: 8 tasks across 6 phases
