# Research: AgentCore Evaluations

**Feature**: 015-agentcore-evaluations
**Date**: 2026-03-18

## R1: AgentCore Evaluation Architecture

**Decision**: Use the `agentcore eval` CLI from the `bedrock-agentcore-starter-toolkit` package for all evaluation operations (on-demand and online).

**Rationale**: The CLI wraps the AgentCore Evaluations API and handles role creation, session discovery, and result formatting. It reads agent ID from `.bedrock_agentcore.yaml` automatically. Using the CLI aligns with the project's existing deployment workflow (agentcore configure/deploy/status).

**Alternatives considered**:
- Raw boto3 API calls: More flexible but verbose, requires manual role management, violates FR-008.
- AWS Console: Not scriptable, doesn't support CI/CD integration.

## R2: Evaluation Execution Role (IAM)

**Decision**: Let the `agentcore eval online create` CLI auto-create the evaluation execution role (`AgentCoreEvalsSDK-{region}-{hash}`). Document the role's permissions in the spec directory for reference rather than adding to the existing CloudFormation template.

**Rationale**: The evaluation execution role is a **separate role** from the agent's runtime execution role (`AgentExecutionRole` in `infra/agentcore/template.yaml`). The CLI auto-creates it with the correct trust policy and permissions. Adding it to CloudFormation would create a naming conflict since the CLI uses its own naming convention. The existing CFN template's `AgentExecutionRole` already has `AdministratorAccess` (line 99), so no additional runtime permissions are needed.

**Alternatives considered**:
- Add to CloudFormation: Would conflict with CLI auto-creation naming. The eval role has different trust policies (bedrock-agentcore evaluations service) than the runtime role.
- Manual role creation: Unnecessary complexity when CLI handles it.

## R3: Custom Evaluator Configuration

**Decision**: Create a custom evaluator using the `agentcore eval evaluator create` CLI command with a JSON config file stored at `specs/015-agentcore-evaluations/tool-selection-evaluator.json`.

**Rationale**: The JSON config defines the LLM-as-a-judge setup including model ID, rating scale, and evaluation instructions. Storing it in the spec directory provides version control and makes it reproducible. The evaluator operates at TRACE level (evaluates individual tool call decisions within a response).

**Key config elements**:
- Model: `global.anthropic.claude-sonnet-4-5-20250929-v1:0`
- Rating scale: 3-point numerical (0.0 Incorrect, 0.5 Partial, 1.0 Correct)
- Instructions: Evaluate tool selection considering available tools (browser, AWS MCP, EKS MCP, Gateway/web search)

**Alternatives considered**:
- SESSION level evaluation: Would evaluate overall tool usage across a conversation rather than per-turn decisions. TRACE level is more granular and actionable.
- Binary rating (0/1): Too coarse — "Partial" captures cases where the right tool category was selected but with suboptimal parameters.

## R4: CLI Wrapper Script Design

**Decision**: Create `scripts/eval-agent.sh` as a Bash wrapper with subcommands: `run`, `setup`, `list`, `status`, `create-evaluator`.

**Rationale**: A wrapper script reduces the command complexity for common operations. The `agentcore eval` CLI requires multiple flags and the evaluator names must be specified individually. The wrapper script encodes these defaults so developers can run evaluations with minimal typing.

**Alternatives considered**:
- Makefile targets: Less portable, doesn't support subcommand-style interface.
- Python script: Adds a runtime dependency for what is essentially CLI orchestration.
- Just running raw CLI commands: Works but violates FR-005 and is error-prone for repeated use.

## R5: Online Evaluation Sampling Rate

**Decision**: 100% sampling rate (evaluate every session).

**Rationale**: This is a demo project with low traffic volume. Evaluating every session provides complete quality coverage without significant cost impact. The sampling rate is configurable via the CLI wrapper's `setup` subcommand if it needs to be adjusted later.

**Alternatives considered**:
- 5% sampling: Standard for production workloads, but would miss most sessions in a low-traffic demo.
- 50%: A middle ground, but no reason not to evaluate everything when traffic is low.
