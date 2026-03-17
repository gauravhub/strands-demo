# Tasks: EKS Retail Store Deployment

**Input**: Design documents from `/specs/011-eks-retail-store-deploy/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Tests**: No automated tests — validation is performed via kubectl commands against the live cluster.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Create the local directory structure for manifests

<!-- sequential -->
- [x] T000 Pre-flight check: verify kubectl context is configured and cluster is reachable by running `kubectl cluster-info` and `kubectl get namespaces` to confirm connectivity; check for pre-existing conflicting namespaces (ui, catalog, carts, checkout, orders, other) — **Resolved: reconfigured kubeconfig for cluster casual-indie-mushroom in us-east-1**
- [x] T001 Create directory structure: `manifests/retail-store/`, `manifests/retail-store/carts/`, `manifests/retail-store/catalog/`, `manifests/retail-store/checkout/`, `manifests/retail-store/orders/`, `manifests/retail-store/ui/`, `manifests/retail-store/other/`

---

## Phase 2: User Story 1 - Copy Upstream Manifests into Repository (Priority: P1) MVP

**Goal**: Fetch all 37 manifest files from `aws-samples/eks-workshop-v2` (path `manifests/base-application/`) and write them into `manifests/retail-store/` preserving exact content and directory structure.

**Independent Test**: Run `kubectl kustomize manifests/retail-store/` and verify valid YAML is rendered with all 6 components.

### Root Kustomization

<!-- sequential -->
- [x] T002 [US1] Fetch and write root `manifests/retail-store/kustomization.yaml` from GitHub (owner: aws-samples, repo: eks-workshop-v2, path: manifests/base-application/kustomization.yaml)

### Service Manifests (Parallel Groups)

<!-- parallel-group: 1 (max 3 concurrent) -->
- [x] T003 [P] [US1] Fetch and write all 8 files in `manifests/retail-store/carts/` from GitHub path `manifests/base-application/carts/` (namespace.yaml, serviceAccount.yaml, configMap.yaml, deployment.yaml, deployment-db.yaml, service.yaml, service-db.yaml, kustomization.yaml)
- [x] T004 [P] [US1] Fetch and write all 9 files in `manifests/retail-store/catalog/` from GitHub path `manifests/base-application/catalog/` (namespace.yaml, serviceAccount.yaml, configMap.yaml, secrets.yaml, deployment.yaml, statefulset-mysql.yaml, service.yaml, service-mysql.yaml, kustomization.yaml)
- [x] T005 [P] [US1] Fetch and write all 8 files in `manifests/retail-store/checkout/` from GitHub path `manifests/base-application/checkout/` (namespace.yaml, serviceAccount.yaml, configMap.yaml, deployment.yaml, deployment-redis.yaml, service.yaml, service-redis.yaml, kustomization.yaml)

<!-- parallel-group: 2 (max 3 concurrent) -->
- [x] T006 [P] [US1] Fetch and write all 9 files in `manifests/retail-store/orders/` from GitHub path `manifests/base-application/orders/` (namespace.yaml, serviceAccount.yaml, configMap.yaml, secrets.yaml, deployment.yaml, deployment-postgresql.yaml, service.yaml, service-postgresql.yaml, kustomization.yaml)
- [x] T007 [P] [US1] Fetch and write all 6 files in `manifests/retail-store/ui/` from GitHub path `manifests/base-application/ui/` (namespace.yaml, serviceAccount.yaml, configMap.yaml, deployment.yaml, service.yaml, kustomization.yaml)
- [x] T008 [P] [US1] Fetch and write all 3 files in `manifests/retail-store/other/` from GitHub path `manifests/base-application/other/` (namespace.yaml, configMap.yaml, kustomization.yaml)

### Validation

<!-- sequential -->
- [x] T009 [US1] Validate all manifest files exist in `manifests/retail-store/` by running `find manifests/retail-store/ -type f | wc -l` and confirming the count matches expected total, then run `kubectl kustomize manifests/retail-store/` to verify valid YAML renders for all 6 components — **Result: 44 files, 37 Kubernetes resources rendered successfully**

**Checkpoint**: All 37 manifest files are present locally and Kustomize renders valid YAML. User Story 1 is complete.

---

## Phase 3: User Story 2 - Deploy Application to EKS Cluster (Priority: P1)

**Goal**: Deploy the retail store application to the EKS cluster using Kustomize and wait for all deployments to roll out.

**Independent Test**: All 6 namespaces exist, all 9 deployments have available replicas, all pods are Running.

**Depends on**: User Story 1 (manifests must exist locally)

### Deployment

<!-- sequential -->
- [x] T010 [US2] Run `kubectl apply -k manifests/retail-store/` to deploy all resources to the EKS cluster
- [x] T011 [US2] Wait for all 9 deployments to roll out by running `kubectl rollout status` for each: deployment/ui -n ui, deployment/catalog -n catalog, statefulset/catalog-mysql -n catalog, deployment/carts -n carts, deployment/carts-dynamodb -n carts, deployment/checkout -n checkout, deployment/checkout-redis -n checkout, deployment/orders -n orders, deployment/orders-postgresql -n orders

**Checkpoint**: All resources applied and all deployments report ready replicas. User Story 2 is complete.

---

## Phase 4: User Story 3 - Validate Deployment Health (Priority: P2)

**Goal**: Verify that all namespaces, deployments, pods, and services are healthy and interconnected.

**Independent Test**: kubectl commands confirm all 6 namespaces active, all deployments available, all pods Running, all services resolvable.

**Depends on**: User Story 2 (application must be deployed)

### Validation

<!-- sequential -->
- [x] T012 [US3] Verify all 6 namespaces exist and are Active: `kubectl get namespaces` and confirm ui, catalog, carts, checkout, orders, other are present
- [x] T013 [US3] Verify all deployments and statefulsets show available replicas: run `kubectl get deployments -A` filtered for namespaces ui, catalog, carts, checkout, orders — confirm READY matches DESIRED for all 8 deployments; also run `kubectl get statefulsets -n catalog` to confirm catalog-mysql StatefulSet has READY replicas
- [x] T014 [US3] Verify all pods are Running: `kubectl get pods -A` filtered for namespaces ui, catalog, carts, checkout, orders — confirm all pods show STATUS=Running and READY containers
- [x] T015 [US3] Verify all services exist: `kubectl get services -A` filtered for namespaces ui, catalog, carts, checkout, orders — confirm services: ui, catalog, catalog-mysql, carts, carts-dynamodb, checkout, checkout-redis, orders, orders-postgresql

**Checkpoint**: All validation checks pass. Full deployment is confirmed healthy. User Story 3 is complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **User Story 1 (Phase 2)**: Depends on Setup — fetch and write all manifest files
- **User Story 2 (Phase 3)**: Depends on User Story 1 — manifests must exist to deploy
- **User Story 3 (Phase 4)**: Depends on User Story 2 — application must be deployed to validate

### User Story Dependencies

- **User Story 1 (P1)**: Independent after Setup. Root kustomization must be written before validation (T009), but all service directories (T003-T008) are independent of each other.
- **User Story 2 (P1)**: Strictly sequential — apply then wait for rollout.
- **User Story 3 (P2)**: Strictly sequential — validate namespaces, then deployments, then pods, then services.

### Parallel Opportunities

- **Phase 2 (US1)**: T003-T005 can run in parallel (parallel-group 1). T006-T008 can run in parallel (parallel-group 2). All 6 service directories are independent.
- **Phase 3 (US2)**: No parallelism — kubectl apply must complete before rollout status checks.
- **Phase 4 (US3)**: No parallelism — validation checks are sequential for clear reporting.

---

## Parallel Example: User Story 1

```bash
# Group 1 (3 concurrent):
Task: "Fetch and write all 8 files in manifests/retail-store/carts/"
Task: "Fetch and write all 9 files in manifests/retail-store/catalog/"
Task: "Fetch and write all 8 files in manifests/retail-store/checkout/"

# Group 2 (3 concurrent):
Task: "Fetch and write all 9 files in manifests/retail-store/orders/"
Task: "Fetch and write all 6 files in manifests/retail-store/ui/"
Task: "Fetch and write all 3 files in manifests/retail-store/other/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (create directories)
2. Complete Phase 2: User Story 1 (fetch all 37 manifest files)
3. **STOP and VALIDATE**: Run `kubectl kustomize manifests/retail-store/` to confirm valid YAML
4. Manifests are in repo and under version control

### Full Delivery

1. Complete Setup → directories ready
2. Complete User Story 1 → manifests in repo (MVP)
3. Complete User Story 2 → application deployed to EKS
4. Complete User Story 3 → deployment validated healthy
5. Feature complete

---

## Notes

- [P] tasks = different files/directories, no dependencies
- [Story] label maps task to specific user story for traceability
- All manifest content MUST be fetched from GitHub and written as-is — no modifications
- GitHub source: owner=aws-samples, repo=eks-workshop-v2, path=manifests/base-application/
- kubectl context is pre-configured for the target EKS cluster
- Total files: 37 across 7 directories (1 root + 6 service subdirectories)
- Total tasks: 16 (T000-T015)
