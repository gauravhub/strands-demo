# Tasks: ALB Ingress for EKS Retail Store UI

**Input**: Design documents from `/specs/012-alb-ingress-ui/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: No test tasks — not explicitly requested in the feature specification. Validation is manual (AWS CLI, kubectl, curl, browser).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths or commands in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify prerequisites and current state before making any changes

- [x] T001 Verify AWS CLI credentials and region configuration for us-east-1 (`aws sts get-caller-identity`)
- [x] T002 [P] Verify kubectl access to EKS cluster `casual-indie-mushroom` (`kubectl get nodes`)
- [x] T003 [P] Verify VPC exists, confirm VPC CIDR covers 10.0.0.0/20 and 10.0.16.0/20 (`aws ec2 describe-vpcs --vpc-ids vpc-0def9b94fcbd9db8c`), and inspect current subnets for CIDR non-overlap (`aws ec2 describe-subnets --filters Name=vpc-id,Values=vpc-0def9b94fcbd9db8c`) — **FINDING: Public subnets (10.0.0.0/20, 10.0.16.0/20, 10.0.32.0/20), IGW (igw-0b8382236331d8dc2), and public route table already exist from agentcore setup. Will reuse instead of creating new resources.**
- [x] T004 [P] Verify UI service is running in the `ui` namespace (`kubectl get svc -n ui` and `kubectl get pods -n ui`)

---

## Phase 2: User Story 2 - VPC Public Networking Infrastructure (Priority: P1)

**Goal**: Create public subnets with an Internet Gateway so internet-facing load balancers can be provisioned

**Independent Test**: Verify IGW is attached, 2 public subnets exist in different AZs, public route table has 0.0.0.0/0 → IGW route, and subnets are properly tagged

### Implementation for User Story 2

- [x] T005 [US2] ~~Create Internet Gateway~~ SKIPPED — IGW `igw-0b8382236331d8dc2` already exists and is attached to VPC
- [x] T006 [P] [US2] ~~Create public subnet in us-east-1a~~ SKIPPED — `subnet-0c60d18c4f0bf327b` (10.0.0.0/20) already exists
- [x] T007 [P] [US2] ~~Create public subnet in us-east-1b~~ SKIPPED — `subnet-0e1e4c828d6c90e45` (10.0.16.0/20) already exists
- [x] T008 [US2] Enable `MapPublicIpOnLaunch` on both public subnets (`aws ec2 modify-subnet-attribute --map-public-ip-on-launch`)
- [x] T009 [US2] ~~Create public route table~~ SKIPPED — `rtb-0999ed95894aa8050` already exists with IGW route
- [x] T010 [US2] ~~Add default route~~ SKIPPED — route 0.0.0.0/0 → igw-0b8382236331d8dc2 already exists
- [x] T011 [US2] ~~Associate subnets with route table~~ SKIPPED — associations already exist
- [x] T012 [P] [US2] Tag both public subnets with `kubernetes.io/role/elb=1` and `kubernetes.io/cluster/casual-indie-mushroom=shared` (`aws ec2 create-tags`)
- [x] T013 [P] [US2] Tag existing private subnets (subnet-0d4fd966d44fc9c0c, subnet-04fee54afd4f1c444, subnet-04bfcab1b517df4fe) with `kubernetes.io/role/internal-elb=1` (`aws ec2 create-tags`)
- [x] T014 [US2] Validate VPC networking: confirm IGW attached, subnets in correct AZs, route table has IGW route, all tags present

**Checkpoint**: VPC public networking is complete — public subnets with IGW are ready for ALB provisioning

---

## Phase 3: User Story 1 - Access Retail Store UI from the Internet (Priority: P1) 🎯 MVP

**Goal**: Create Kubernetes Ingress to provision an internet-facing ALB that routes to the UI service

**Independent Test**: Navigate to the ALB DNS name in a browser and confirm the retail store UI loads

**Depends on**: Phase 2 (public subnets must exist for ALB placement)

### Implementation for User Story 1

- [x] T015 [P] [US1] Create Ingress manifest at `manifests/retail-store/ui/ingress.yaml` + `ingressclassparams.yaml` + `ingressclass.yaml` (EKS Auto Mode requires explicit IngressClass with controller `eks.amazonaws.com/alb`)
- [x] T016 [P] [US1] Update `manifests/retail-store/ui/kustomization.yaml` to include `ingressclassparams.yaml`, `ingressclass.yaml`, and `ingress.yaml`
- [x] T017 [US1] Apply updated manifests with `kubectl apply -k manifests/retail-store/`
- [x] T018 [US1] Wait for ALB provisioning — ADDRESS: `k8s-ui-ui-6353f3da9d-613966318.us-east-1.elb.amazonaws.com`
- [x] T019 [US1] Validate ALB is accessible: curl returns HTTP 200 with Demo Store HTML (19,973 bytes)
- [x] T020 [US1] Validate retail store UI loads — confirmed via curl (cloud browser blocks HTTP; user can verify at http://k8s-ui-ui-6353f3da9d-613966318.us-east-1.elb.amazonaws.com)

**Checkpoint**: Retail store UI is accessible from the internet via ALB — MVP complete

---

## Phase 4: User Story 3 - ALB Health Checks Validate UI Availability (Priority: P2)

**Goal**: Confirm ALB health checks are using the liveness probe endpoint and targets are healthy

**Independent Test**: Check ALB target group health status in AWS CLI; confirm targets marked healthy

**Depends on**: Phase 3 (ALB must be provisioned)

### Implementation for User Story 3

- [x] T021 [US3] Verify ALB target group health check is configured for `/actuator/health/liveness` on port 8080 — confirmed
- [x] T022 [US3] Confirm all targets healthy — 10.0.158.75:8080 = healthy

**Checkpoint**: ALB health checks validated — traffic is only routed to healthy UI pods

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation

- [x] T023 Verify existing cluster workloads are unaffected — 11 pods running, no non-running pods
- [x] T024 [P] Verify private subnet route tables were not modified — confirmed unchanged
- [x] T025 Record the ALB DNS URL and resource IDs — see summary below

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **User Story 2 (Phase 2)**: Depends on Setup — VPC networking must be created first (BLOCKS User Story 1)
- **User Story 1 (Phase 3)**: Depends on User Story 2 — ALB needs public subnets
- **User Story 3 (Phase 4)**: Depends on User Story 1 — health checks need a provisioned ALB
- **Polish (Phase 5)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 2 (P1 — VPC Networking)**: Foundation — no other story dependencies, but blocks US1
- **User Story 1 (P1 — Internet Access)**: Depends on US2 (public subnets required for ALB)
- **User Story 3 (P2 — Health Checks)**: Depends on US1 (ALB must exist to verify health checks)

### Within Each User Story

- AWS resources must be created before tagging/validation
- Ingress manifest must be created before applying
- ALB must be provisioned before validation
- Commit after each logical group

### Parallel Opportunities

- T002, T003, T004 can run in parallel (independent verification checks)
- T006 and T007 can run in parallel (different subnets in different AZs)
- T012 and T013 can run in parallel (tagging different subnet groups)
- T023 and T024 can run in parallel (independent verification checks)

---

## Parallel Example: Phase 1 Setup

```bash
# Launch verification checks in parallel:
Task: "Verify kubectl access to EKS cluster (T002)"
Task: "Verify VPC and inspect subnets (T003)"
Task: "Verify UI service running in ui namespace (T004)"
```

## Parallel Example: Phase 2 Subnet Creation

```bash
# After IGW is created (T005), create both subnets in parallel:
Task: "Create public subnet in us-east-1a (T006)"
Task: "Create public subnet in us-east-1b (T007)"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup verification
2. Complete Phase 2: VPC public networking (US2) — CRITICAL prerequisite
3. Complete Phase 3: Ingress + ALB provisioning (US1)
4. **STOP and VALIDATE**: Access retail store UI via ALB URL in browser
5. Complete Phase 4: Health check validation (US3)

### Sequential Execution (Single Operator)

1. Setup → VPC Networking → Ingress → Health Checks → Polish
2. Each phase builds on the previous — strict sequential ordering required
3. Total: 25 tasks in 5 phases

---

## Notes

- [P] tasks = different resources, no dependencies
- [Story] label maps task to specific user story for traceability
- All AWS CLI commands must target `--region us-east-1`
- ALB provisioning takes 2-3 minutes — T018 should retry with wait
- Resource IDs from AWS CLI output must be captured and reused in subsequent commands (use shell variables)
- Commit manifest changes (T015, T016) before applying (T017)
