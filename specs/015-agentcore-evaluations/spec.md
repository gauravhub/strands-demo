# Feature Specification: AgentCore Evaluations

**Feature Branch**: `015-agentcore-evaluations`
**Created**: 2026-03-18
**Status**: Draft
**Input**: User description: "Enable AgentCore Evaluations for the strands-demo agent with built-in and custom evaluators, CLI wrapper script, and IAM permissions"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Continuous Quality Monitoring (Priority: P1)

A developer deploys the strands-demo agent and wants ongoing quality monitoring without manual intervention. They configure online evaluation so that a percentage of live agent sessions are automatically evaluated for helpfulness, correctness, faithfulness, and goal completion. The developer views evaluation results in CloudWatch to track quality trends over time.

**Why this priority**: Continuous monitoring is the primary value proposition — it catches quality regressions in production before users report them. Without it, evaluation is reactive rather than proactive.

**Independent Test**: Can be fully tested by creating an online evaluation config, invoking the agent a few times, waiting 5 minutes for CloudWatch data, and checking that evaluation results appear in the output log group.

**Acceptance Scenarios**:

1. **Given** the agent is deployed with observability enabled, **When** a developer creates an online evaluation config with 4 built-in evaluators, **Then** the config is created successfully with status ACTIVE and a 100% sampling rate.
2. **Given** an online evaluation config is active, **When** live agent sessions are sampled, **Then** evaluation results appear in the CloudWatch output log group within 10 minutes.
3. **Given** the online evaluation config exists, **When** the developer updates the sampling rate or evaluator list, **Then** the changes take effect without recreating the config.

---

### User Story 2 - On-Demand Session Evaluation (Priority: P1)

A developer wants to evaluate a specific agent session after a user reports an issue or after testing a new prompt. They run a single CLI command that evaluates the session against all configured evaluators (built-in and custom) and see scores, labels, and explanations for each evaluator.

**Why this priority**: On-demand evaluation is essential for debugging and validating fixes. It complements continuous monitoring by allowing targeted investigation of specific sessions.

**Independent Test**: Can be tested by invoking the agent once, waiting for observability data to populate, and running the on-demand evaluation command against that session.

**Acceptance Scenarios**:

1. **Given** an agent session with observability data exists, **When** the developer runs an on-demand evaluation with all evaluators, **Then** they see scores and explanations for each evaluator (Helpfulness, Correctness, Faithfulness, GoalSuccessRate, and the custom tool_selection_accuracy evaluator).
2. **Given** the developer specifies a session older than 7 days, **When** they run on-demand evaluation with an extended lookback period, **Then** the evaluation still finds and evaluates the session data.
3. **Given** no observability data exists for a session, **When** the developer runs on-demand evaluation, **Then** they receive a clear error message explaining the issue and suggesting next steps.

---

### User Story 3 - Custom Tool Selection Evaluator (Priority: P2)

A developer wants to assess whether the agent picks the right tool for each user request — for example, using browser tools for screenshot requests, AWS MCP for infrastructure queries, and Gateway for web search. They create a custom LLM-as-a-judge evaluator that scores tool selection accuracy, and this evaluator runs alongside the built-in ones in both on-demand and online modes.

**Why this priority**: Tool selection quality is a domain-specific concern unique to this multi-tool agent. Built-in evaluators cover general quality; this custom evaluator covers the agent's tool routing logic, which is a core differentiator.

**Independent Test**: Can be tested by creating the custom evaluator, invoking the agent with tool-heavy requests (e.g., "take a screenshot of the retail store", "list my EKS clusters"), and evaluating the session to see the tool_selection_accuracy score.

**Acceptance Scenarios**:

1. **Given** a custom evaluator config JSON exists, **When** the developer creates the evaluator via CLI, **Then** it appears in the evaluator list alongside built-in evaluators.
2. **Given** the custom evaluator is created, **When** it evaluates a session where the agent used browser tools for a screenshot request, **Then** it scores the tool selection as high (Correct).
3. **Given** the custom evaluator is created, **When** it evaluates a session where the agent used the wrong tool (e.g., web search instead of browser for a screenshot), **Then** it scores the tool selection as low (Incorrect) with an explanation.

---

### User Story 4 - CLI Wrapper for Evaluation Operations (Priority: P2)

A developer wants a convenient shell script that wraps common evaluation operations so they don't need to remember long CLI commands or flags. The script provides subcommands for running evaluations, managing online configs, and listing results.

**Why this priority**: Convenience tooling reduces friction for repeated evaluation tasks. While the underlying CLI works without it, a wrapper script makes evaluation a natural part of the development workflow.

**Independent Test**: Can be tested by running each subcommand of the wrapper script and verifying the expected output matches the equivalent raw CLI command.

**Acceptance Scenarios**:

1. **Given** the wrapper script exists at `scripts/eval-agent.sh`, **When** the developer runs `./scripts/eval-agent.sh run <session-id>`, **Then** the script runs on-demand evaluation against the session with all evaluators.
2. **Given** the wrapper script exists, **When** the developer runs `./scripts/eval-agent.sh setup`, **Then** the script creates or updates the online evaluation config with all evaluators and 100% sampling rate.
3. **Given** the wrapper script exists, **When** the developer runs `./scripts/eval-agent.sh list`, **Then** the script lists all online evaluation configs and their status.
4. **Given** the wrapper script exists, **When** the developer runs it without arguments, **Then** it displays usage help with examples.

---

### User Story 5 - Evaluation IAM Permissions (Priority: P1)

The evaluation execution role needs specific IAM permissions to read observability data and invoke the judge model. These permissions are documented and, where possible, added to the existing CloudFormation template so that the infrastructure is self-contained.

**Why this priority**: Without the correct IAM permissions, evaluations fail silently or with cryptic errors. This is a prerequisite for all other stories.

**Independent Test**: Can be tested by verifying the evaluation execution role can be assumed and has the necessary permissions (by running `agentcore eval run` successfully without IAM errors).

**Acceptance Scenarios**:

1. **Given** the CloudFormation template includes evaluation-related permissions, **When** the stack is updated, **Then** the execution role has permissions to read CloudWatch logs, invoke Bedrock models for judging, and write evaluation results.
2. **Given** the evaluation execution role is auto-created by the CLI, **When** the developer checks the role's policies, **Then** the required permissions are documented in the spec directory for reference.

---

### Edge Cases

- What happens when the agent has no observability data (observability disabled or no sessions yet)? The evaluation commands should return clear error messages directing the user to enable observability first.
- What happens when the custom evaluator config JSON has invalid syntax? The CLI should validate the JSON and return a descriptive error before attempting to create the evaluator.
- What happens when the sampling rate is set to 0%? No sessions should be evaluated, and the config should reflect this as effectively disabled.
- What happens when the online evaluation config is created but the agent has no traffic? The config remains ACTIVE but produces no evaluation results until sessions are sampled.
- What happens when CloudWatch logs haven't populated yet (2-5 minute delay)? On-demand evaluation should surface the "no spans found" error with guidance to wait and retry.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create an online evaluation configuration with the following built-in evaluators: Builtin.GoalSuccessRate (SESSION), Builtin.Helpfulness (TRACE), Builtin.Correctness (TRACE), Builtin.Faithfulness (TRACE).
- **FR-002**: System MUST support a configurable sampling rate for online evaluation, starting at 100% (evaluate every session).
- **FR-003**: System MUST create a custom evaluator named "tool_selection_accuracy" using LLM-as-a-judge with Claude Sonnet as the judge model.
- **FR-004**: The custom evaluator MUST evaluate whether the agent selected the correct tools for the user's request, considering browser tools, AWS MCP, EKS MCP, and Gateway web search tools.
- **FR-005**: System MUST provide a CLI wrapper script (`scripts/eval-agent.sh`) with subcommands for: on-demand evaluation, online config management, and result listing.
- **FR-006**: System MUST NOT modify the agent code in `src/agentcore/app.py` — evaluations are external to the agent.
- **FR-007**: System MUST use the agent ID from the existing deployment configuration (`.bedrock_agentcore.yaml` or agentcore CLI auto-detection).
- **FR-008**: System MUST use `agentcore eval` CLI commands — not raw AWS API calls.
- **FR-009**: System MUST store the custom evaluator config JSON file in `specs/015-agentcore-evaluations/` for version control and reference.
- **FR-010**: System MUST document any IAM permissions required for the evaluation execution role, and where possible, add them to the existing CloudFormation template (`infra/agentcore/template.yaml`).
- **FR-011**: The CLI wrapper script MUST auto-detect the agent ID from the deployment config rather than requiring it as a hardcoded argument.
- **FR-012**: On-demand evaluation MUST support evaluating a specific session with all evaluators in a single command.

### Key Entities

- **Online Evaluation Config**: A named configuration that defines which evaluators to run, at what sampling rate, against which agent endpoint. Identified by a config ID.
- **Custom Evaluator**: An LLM-as-a-judge evaluator definition with a rating scale, judge model, and evaluation instructions. Identified by a name/ID.
- **Evaluation Result**: The output of running evaluators against a session — includes scores, labels, explanations, and token usage per evaluator.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can set up continuous evaluation monitoring in under 5 minutes using the CLI wrapper script.
- **SC-002**: On-demand evaluation of a single session completes in under 2 minutes and returns scores from all 5 evaluators.
- **SC-003**: The custom tool_selection_accuracy evaluator correctly distinguishes between appropriate and inappropriate tool selection in at least 80% of evaluated sessions.
- **SC-004**: All evaluation operations (create, run, list, update) work without IAM permission errors after the CloudFormation stack is updated.
- **SC-005**: Evaluation results are accessible via CloudWatch within 10 minutes of the evaluated session completing.

## Clarifications

### Session 2026-03-18

- No critical ambiguities detected. All functional requirements, evaluator definitions, constraints, and edge cases are sufficiently specified for planning.
- Q: What sampling rate for online evaluation? → A: 100% (evaluate every session, since this is a demo with low traffic).

## Assumptions

- The agent is already deployed to AgentCore Runtime with a valid agent ID.
- Observability (OpenTelemetry tracing to CloudWatch) is already enabled via feature 006.
- The `bedrock-agentcore-starter-toolkit` CLI (`agentcore` command) is already installed in the development environment.
- The evaluation execution role is auto-created by the CLI if it doesn't exist (as documented in AgentCore Evaluations quickstart).
- No new Python packages need to be added to the agent's dependencies — this is purely a tooling/infrastructure feature.
- The custom evaluator uses the Claude Sonnet model available in the deployment region (global.anthropic.claude-sonnet-4-5-20250929-v1:0).
