# Infrastructure Requirements Quality Checklist: ALB Ingress for EKS Retail Store UI

**Purpose**: Validate completeness, clarity, and consistency of VPC networking and Kubernetes Ingress requirements
**Created**: 2026-03-17
**Feature**: [spec.md](../spec.md)

## Requirement Completeness

- [ ] CHK001 Are all VPC resources (IGW, subnets, route table, routes, associations) individually specified with creation parameters? [Completeness, Spec §FR-001 through §FR-003]
- [ ] CHK002 Are Name tags specified for all new AWS resources (IGW, subnets, route table) to enable identification? [Completeness, Gap]
- [ ] CHK003 Are all required Kubernetes Ingress annotations explicitly listed in the requirements? [Completeness, Spec §FR-006]
- [ ] CHK004 Is the `MapPublicIpOnLaunch` attribute specified for public subnets? [Completeness, Gap]
- [ ] CHK005 Are the exact CIDR blocks documented for both public subnets with non-overlap validation against existing ranges? [Completeness, Spec §FR-002]
- [ ] CHK006 Is the health check port explicitly specified alongside the health check path? [Completeness, Spec §FR-008]

## Requirement Clarity

- [ ] CHK007 Is "internet-facing" unambiguously defined as an ALB scheme annotation value rather than a general description? [Clarity, Spec §FR-006]
- [ ] CHK008 Is the Ingress path type (Prefix vs Exact) specified for the `/` routing rule? [Clarity, Gap]
- [ ] CHK009 Are the required tag key-value pairs for ALB auto-discovery listed with exact values (not just described)? [Clarity, Spec §FR-004]
- [ ] CHK010 Is it clear whether private subnet tagging (FR-005) is conditional ("if not already tagged") or unconditional? [Clarity, Spec §FR-005]
- [ ] CHK011 Is the ALB provisioning timeout expectation (5 minutes) specified as a success criterion rather than just an assumption? [Clarity, Spec §SC-002]

## Requirement Consistency

- [ ] CHK012 Are health check requirements consistent between the Ingress annotations (FR-008) and the validation criteria (US3 acceptance scenarios)? [Consistency, Spec §FR-008 + US3]
- [ ] CHK013 Is the service port (80) vs container port (8080) distinction consistently referenced across all requirements? [Consistency, Spec §FR-006 + §FR-008]
- [ ] CHK014 Are the constraint about not modifying private subnets (FR-010) and the requirement to tag them (FR-005) reconciled? [Consistency, Spec §FR-005 + §FR-010]
- [ ] CHK015 Is the cluster name (`casual-indie-mushroom`) consistently used across all tag requirements? [Consistency, Spec §FR-004]

## Acceptance Criteria Quality

- [ ] CHK016 Can SC-001 ("accessible from any internet-connected browser") be objectively measured without ambiguity? [Measurability, Spec §SC-001]
- [ ] CHK017 Is SC-005 ("existing cluster workloads remain unaffected") measurable — are specific verification checks defined? [Measurability, Spec §SC-005]
- [ ] CHK018 Are acceptance scenarios for US2 specific enough to validate each VPC resource independently? [Measurability, Spec §US2]

## Edge Case & Failure Scenario Coverage

- [ ] CHK019 Are requirements defined for what happens if CIDR blocks are already in use in the VPC? [Edge Case, Gap]
- [ ] CHK020 Are requirements defined for ALB provisioning failure (e.g., Ingress stuck without ADDRESS beyond timeout)? [Edge Case, Gap]
- [ ] CHK021 Is behavior specified when the EKS Auto Mode load balancer controller is not functioning? [Edge Case, Gap]
- [ ] CHK022 Are requirements defined for partial infrastructure failure (e.g., one subnet created but second fails)? [Edge Case, Gap]
- [ ] CHK023 Is the expected behavior documented if the UI service is down when the Ingress is first applied? [Edge Case, Spec §Edge Cases]

## Non-Functional Requirements

- [ ] CHK024 Are security requirements for the ALB defined (e.g., security group rules, open ports)? [Security, Gap]
- [ ] CHK025 Is the lack of HTTPS/TLS explicitly documented as an accepted limitation with scope for future work? [Security, Spec §Assumptions]
- [ ] CHK026 Are cost implications of the ALB and public subnets acknowledged in requirements or assumptions? [Non-Functional, Gap]

## Dependencies & Assumptions

- [ ] CHK027 Is the assumption that VPC CIDR has space for additional /20 subnets validated against the actual VPC CIDR? [Assumption, Spec §Assumptions]
- [ ] CHK028 Is the dependency on EKS Auto Mode's `elasticLoadBalancing: enabled` documented as a prerequisite to verify? [Dependency, Spec §Assumptions]
- [ ] CHK029 Are AWS IAM permission requirements for VPC resource creation documented? [Dependency, Spec §Assumptions]
- [ ] CHK030 Is the dependency on the UI service's liveness probe endpoint being operational documented as a prerequisite? [Dependency, Spec §Assumptions]

## Notes

- Check items off as completed: `[x]`
- Items reference spec sections using `[Spec §X]` notation
- `[Gap]` markers indicate requirements that may be missing from the spec
- Focus: infrastructure resource creation, Kubernetes manifest correctness, operational readiness
