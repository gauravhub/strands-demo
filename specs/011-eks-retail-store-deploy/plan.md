# Implementation Plan: EKS Retail Store Deployment

**Branch**: `011-eks-retail-store-deploy` | **Date**: 2026-03-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-eks-retail-store-deploy/spec.md`

## Summary

Copy 37 Kustomize manifest files from the EKS Workshop sample repository (`aws-samples/eks-workshop-v2`) into `manifests/retail-store/` in this repo, deploy the retail store microservices application to an EKS cluster using `kubectl apply -k`, and validate that all 6 namespaces, 9 deployments, and associated services are healthy.

This is an infrastructure-only feature — no application code is written. The implementation consists of fetching upstream YAML files, writing them locally, executing kubectl commands, and verifying cluster state.

## Technical Context

**Language/Version**: N/A — no application code; Kubernetes YAML manifests only
**Primary Dependencies**: kubectl (with built-in Kustomize), GitHub API (for fetching upstream files)
**Storage**: N/A — manifests stored as files in repo; application data in-cluster (DynamoDB-local, MySQL, PostgreSQL, Redis)
**Testing**: kubectl-based validation (namespace existence, deployment readiness, pod health, service resolution)
**Target Platform**: Amazon EKS cluster (pre-provisioned)
**Project Type**: Infrastructure deployment (Kubernetes manifests + operational commands)
**Performance Goals**: All deployments healthy within 5 minutes of apply
**Constraints**: Manifests must be copied as-is with zero modifications; deploy via Kustomize only
**Scale/Scope**: 37 files across 7 directories; 9 deployments across 6 namespaces

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simplicity First | PASS | No abstractions or code — just copy files, deploy, validate |
| II. Iterative & Independent Delivery | PASS | Self-contained infrastructure feature; does not modify existing app; `streamlit run app.py` unaffected. **Constitution exemption**: This feature deploys Kubernetes manifests only — no Streamlit UI component is applicable. The "working Streamlit UI demonstrating the feature" requirement applies to features that touch the application; infrastructure-only features are exempt as they are demonstrated via kubectl validation instead. |
| III. Python-Native Patterns | N/A | No Python code in this feature — Kubernetes YAML manifests only |
| IV. Security by Design | PASS | Using upstream secrets (base64-encoded demo credentials in manifests); no new credentials introduced; cluster access via existing kubectl context |
| V. Observability & Debuggability | PASS | Validation step checks pod health, deployment readiness, and service resolution; failures surface via kubectl output |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/011-eks-retail-store-deploy/
├── plan.md              # This file
├── research.md          # Phase 0 output (minimal — no unknowns)
├── data-model.md        # Phase 1 output (Kubernetes resource inventory)
├── tasks.md             # Phase 2 output (created by /speckit.tasks)
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
manifests/retail-store/
├── kustomization.yaml           # Root Kustomize config (references all subdirs)
├── carts/
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── serviceAccount.yaml
│   ├── configMap.yaml
│   ├── deployment.yaml
│   ├── deployment-db.yaml
│   ├── service.yaml
│   └── service-db.yaml
├── catalog/
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── serviceAccount.yaml
│   ├── configMap.yaml
│   ├── secrets.yaml
│   ├── deployment.yaml
│   ├── statefulset-mysql.yaml
│   ├── service.yaml
│   └── service-mysql.yaml
├── checkout/
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── serviceAccount.yaml
│   ├── configMap.yaml
│   ├── deployment.yaml
│   ├── deployment-redis.yaml
│   ├── service.yaml
│   └── service-redis.yaml
├── orders/
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── serviceAccount.yaml
│   ├── configMap.yaml
│   ├── secrets.yaml
│   ├── deployment.yaml
│   ├── deployment-postgresql.yaml
│   ├── service.yaml
│   └── service-postgresql.yaml
├── ui/
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── serviceAccount.yaml
│   ├── configMap.yaml
│   ├── deployment.yaml
│   └── service.yaml
└── other/
    ├── kustomization.yaml
    ├── namespace.yaml
    └── configMap.yaml
```

**Structure Decision**: Flat Kustomize layout under `manifests/retail-store/` matching the upstream structure exactly. No additional wrapper scripts or Helm charts — Kustomize is the deployment mechanism as specified.

## Architecture

### Approach

This feature has three sequential phases with no code development:

1. **Fetch & Write**: Use GitHub API (via MCP tools) to fetch each manifest file from `aws-samples/eks-workshop-v2` at path `manifests/base-application/{subdir}/{file}` and write it to `manifests/retail-store/{subdir}/{file}`. Each of the 6 service subdirectories can be fetched in parallel since they are independent.

2. **Deploy**: Execute `kubectl apply -k manifests/retail-store/` which Kustomize will expand into all resources across all namespaces. This is a single atomic operation.

3. **Validate**: Run kubectl commands to verify:
   - 6 namespaces exist and are Active
   - 9 deployments have available replicas (rollout complete)
   - All pods are Running
   - All services exist

### Component Map

| Component | Namespace | App Image | Data Store | Data Store Image |
|-----------|-----------|-----------|------------|-----------------|
| ui | ui | retail-store-sample-ui:1.2.1 | None | — |
| catalog | catalog | retail-store-sample-catalog:1.2.1 | MySQL (StatefulSet) | mysql:8.0 |
| carts | carts | retail-store-sample-cart:1.2.1 | DynamoDB-local (Deployment) | amazon/dynamodb-local |
| checkout | checkout | retail-store-sample-checkout:1.2.1 | Redis (Deployment) | redis:6-alpine |
| orders | orders | retail-store-sample-orders:1.2.1 | PostgreSQL (Deployment) | postgresql |

### Inter-Service Communication

```
UI → catalog.catalog.svc:80    (product browsing)
UI → carts.carts.svc:80        (shopping cart)
UI → orders.orders.svc:80      (order history)
UI → checkout.checkout.svc:80  (checkout flow)
checkout → orders.orders.svc:80 (place order)
```

All communication is via ClusterIP Services on port 80, targeting container port 8080.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Cluster lacks resources for 9 deployments | Low | High | Check node capacity before deploying; pods will show Pending with events |
| Image pull failures (ECR public) | Low | Medium | Cluster must have internet egress; check pod events for ImagePullBackOff |
| Namespace conflicts from prior deployment | Low | Low | `kubectl apply` is idempotent; existing resources updated in-place |
| Upstream manifest changes after copy | Low | Low | Manifests pinned to version 1.2.1 images; copy is a point-in-time snapshot |

## Complexity Tracking

No constitution violations — table not needed.
