# Data Model: AgentCore Evaluations

**Feature**: 015-agentcore-evaluations
**Date**: 2026-03-18

## Entities

### Custom Evaluator Definition (tool-selection-evaluator.json)

A JSON configuration file that defines the custom LLM-as-a-judge evaluator.

| Field | Type | Description |
|-------|------|-------------|
| llmAsAJudge.modelConfig.bedrockEvaluatorModelConfig.modelId | string | Bedrock model ID for the judge (Claude Sonnet) |
| llmAsAJudge.modelConfig.bedrockEvaluatorModelConfig.inferenceConfig.maxTokens | int | Max output tokens for judge response |
| llmAsAJudge.modelConfig.bedrockEvaluatorModelConfig.inferenceConfig.temperature | float | Sampling temperature for judge (1.0 = default) |
| llmAsAJudge.ratingScale.numerical[] | array | Rating scale entries with value, label, definition |
| llmAsAJudge.instructions | string | Evaluation prompt template with {context} and {assistant_turn} placeholders |

### Online Evaluation Config (managed by AgentCore service)

Created via CLI, not stored as a local file. Identified by a config ID returned on creation.

| Attribute | Description |
|-----------|-------------|
| Config Name | User-chosen name (underscores, no hyphens) |
| Config ID | Auto-generated: `{name}-{random}` |
| Agent ID | Auto-detected from `.bedrock_agentcore.yaml` |
| Sampling Rate | Percentage of sessions to evaluate (100.0) |
| Evaluators | List of evaluator IDs (built-in + custom) |
| Status | CREATING → ACTIVE (or DISABLED) |
| Execution Role | Auto-created: `AgentCoreEvalsSDK-{region}-{hash}` |
| Output Log Group | `/aws/bedrock-agentcore/evaluations/results/{config-id}` |

### Evaluation Result (CloudWatch output)

Results are written to the output log group. Each result contains:

| Field | Description |
|-------|-------------|
| Evaluator ID | Which evaluator produced this result |
| Score | Numerical score (0.0 - 1.0) |
| Label | Human-readable label (e.g., "Very Helpful", "Correct") |
| Explanation | LLM-generated reasoning for the score |
| Token Usage | Input/output/total tokens consumed by the judge |
| Session ID | Which session was evaluated |
| Trace ID | Which trace within the session (for TRACE-level evaluators) |

## Relationships

```
Online Evaluation Config
  ├── references → Agent Runtime (by agent ID)
  ├── uses → Built-in Evaluators (4x)
  ├── uses → Custom Evaluator (tool_selection_accuracy)
  └── writes → Evaluation Results (to CloudWatch log group)

Custom Evaluator
  ├── defined by → tool-selection-evaluator.json (local file)
  └── invokes → Bedrock Model (Claude Sonnet, for judging)

CLI Wrapper Script (scripts/eval-agent.sh)
  ├── reads → .bedrock_agentcore.yaml (agent ID)
  ├── invokes → agentcore eval CLI commands
  └── references → tool-selection-evaluator.json (for create-evaluator subcommand)
```

## File Artifacts

| File | Purpose | Created By |
|------|---------|------------|
| `specs/015-agentcore-evaluations/tool-selection-evaluator.json` | Custom evaluator config | Manual (version controlled) |
| `scripts/eval-agent.sh` | CLI wrapper script | Manual (version controlled) |
| `infra/agentcore/template.yaml` | CloudFormation — no changes needed (eval role is separate) | Existing |
