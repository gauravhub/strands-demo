# Infrastructure & Tooling Checklist: AgentCore Evaluations

**Purpose**: Validate requirements quality for CLI wrapper, custom evaluator config, IAM permissions, and operational readiness
**Created**: 2026-03-18
**Feature**: [spec.md](../spec.md)

## Requirement Completeness

- [ ] CHK001 - Are all CLI wrapper subcommands explicitly enumerated with their arguments and expected outputs? [Completeness, Spec §FR-005]
- [ ] CHK002 - Are error message requirements defined for each CLI wrapper subcommand when it fails? [Completeness, Gap]
- [ ] CHK003 - Is the naming convention for the online evaluation config specified (underscores required, no hyphens)? [Completeness, Gap]
- [ ] CHK004 - Are the exact fields of the custom evaluator JSON config (model ID, rating scale values, instruction template) all documented? [Completeness, Spec §FR-003, §FR-004]
- [ ] CHK005 - Is the prerequisite dependency on feature 006 (observability) explicitly stated as a hard prerequisite, not just an assumption? [Completeness, Spec §Assumptions]
- [ ] CHK006 - Are requirements defined for what the `setup` subcommand does when a config already exists (create vs update behavior)? [Completeness, Spec §US4 Scenario 2]

## Requirement Clarity

- [ ] CHK007 - Is "auto-detect the agent ID" (FR-011) clarified with the specific mechanism (`.bedrock_agentcore.yaml` parsing vs `agentcore status` command)? [Clarity, Spec §FR-007, §FR-011]
- [ ] CHK008 - Is the custom evaluator's `{context}` and `{assistant_turn}` instruction template placeholder behavior explicitly defined? [Clarity, Spec §FR-004]
- [ ] CHK009 - Is "configurable sampling rate" (FR-002) clarified — configurable at setup time only, or runtime-adjustable via the wrapper script? [Clarity, Spec §FR-002]
- [ ] CHK010 - Are the 3-point rating scale labels (Incorrect/Partial/Correct) defined with unambiguous criteria for each level? [Clarity, Plan §Custom Evaluator]

## Requirement Consistency

- [ ] CHK011 - Does the plan's list of CLI subcommands (6 subcommands including `status` and `list-evaluators`) align with FR-005's stated scope (3 subcommands: run, setup, list)? [Consistency, Spec §FR-005 vs Plan §CLI Wrapper]
- [ ] CHK012 - Is the IAM approach consistent between Spec §FR-010 ("add to existing CloudFormation template") and Plan §Research R2 ("document only, no CFN changes")? [Consistency, Spec §FR-010 vs Plan]
- [ ] CHK013 - Are the evaluator names consistent across spec, plan, and data model (e.g., "tool_selection_accuracy" vs any variations)? [Consistency]

## Acceptance Criteria Quality

- [ ] CHK014 - Is SC-003 ("80% of evaluated sessions") measurable without defining how many sessions constitute a valid sample? [Measurability, Spec §SC-003]
- [ ] CHK015 - Is SC-001 ("under 5 minutes") measurable given it depends on AWS API response times outside the feature's control? [Measurability, Spec §SC-001]
- [ ] CHK016 - Are success criteria defined for the custom evaluator creation step itself (not just its evaluation accuracy)? [Gap, Spec §SC]

## Scenario Coverage

- [ ] CHK017 - Are requirements defined for updating an existing custom evaluator (version/overwrite behavior)? [Coverage, Gap]
- [ ] CHK018 - Are requirements defined for deleting or disabling an online evaluation config? [Coverage, Gap]
- [ ] CHK019 - Are requirements defined for the CLI wrapper's behavior when the `agentcore` CLI is not installed? [Coverage, Gap]
- [ ] CHK020 - Are requirements defined for running the wrapper script from a directory other than the repo root? [Coverage, Gap]

## Edge Case Coverage

- [ ] CHK021 - Are requirements defined for what happens when the custom evaluator judge model (Claude Sonnet) is unavailable in the deployment region? [Edge Case, Gap]
- [ ] CHK022 - Are requirements defined for concurrent `setup` invocations (race condition on config creation)? [Edge Case, Gap]
- [ ] CHK023 - Is the 2-5 minute CloudWatch delay quantified with a recommended wait time or retry strategy in the wrapper script? [Edge Case, Spec §Edge Cases]

## Dependencies & Assumptions

- [ ] CHK024 - Is the assumption that the evaluation execution role is auto-created validated against the CLI documentation (what if auto-creation fails)? [Assumption, Spec §Assumptions]
- [ ] CHK025 - Is the dependency on the specific Claude Sonnet model ID (`global.anthropic.claude-sonnet-4-5-20250929-v1:0`) documented with a fallback if the model is deprecated? [Dependency, Spec §Assumptions]
- [ ] CHK026 - Is the assumption "no new Python packages needed" validated — does the `agentcore` CLI need to be a specific minimum version? [Assumption, Spec §Assumptions]

## Notes

- Focus areas: CLI contract completeness, evaluator config clarity, IAM/infrastructure, operational readiness
- Depth: Standard
- Audience: Reviewer (PR)
- Items CHK011 and CHK012 flag spec-plan inconsistencies that should be resolved before implementation
