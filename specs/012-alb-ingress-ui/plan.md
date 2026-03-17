# Implementation Plan: ALB Ingress for EKS Retail Store UI

**Branch**: `012-alb-ingress-ui` | **Date**: 2026-03-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-alb-ingress-ui/spec.md`

## Summary

Expose the EKS retail store UI to the internet by: (1) creating VPC public networking infrastructure (Internet Gateway, two public subnets, public route table) via AWS CLI, and (2) creating a Kubernetes Ingress resource that provisions an internet-facing ALB routing to the UI service. EKS Auto Mode handles the AWS Load Balancer Controller automatically.

## Technical Context

**Language/Version**: N/A — no application code; AWS CLI commands + Kubernetes YAML manifests
**Primary Dependencies**: AWS CLI v2, kubectl (with built-in Kustomize)
**Storage**: N/A — infrastructure resources only
**Testing**: Manual validation via AWS CLI, kubectl, curl, and browser
**Target Platform**: AWS (us-east-1) — EKS cluster `casual-indie-mushroom`, VPC `vpc-0def9b94fcbd9db8c`
**Project Type**: Infrastructure / Kubernetes manifests
**Performance Goals**: ALB provisioned within 5 minutes of Ingress creation
**Constraints**: AWS CLI only (no CloudFormation/Terraform), do not modify existing private subnets/routes, do not install LB controller manually
**Scale/Scope**: 2 public subnets, 1 Internet Gateway, 1 route table, 1 Ingress resource

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simplicity First | PASS | Minimal infrastructure: only IGW, 2 subnets, 1 route table, 1 Ingress. No over-engineering. |
| II. Iterative & Independent Delivery | PASS | Self-contained feature — adds internet access to existing deployed UI without affecting other services. |
| III. Python-Native Patterns | N/A | No Python code in this feature — infrastructure manifests only. |
| IV. Security by Design | PASS | HTTP-only as explicitly scoped. ALB is internet-facing by design requirement. No credentials hardcoded — uses existing AWS CLI/kubectl auth. |
| V. Observability & Debuggability | PASS | ALB health checks provide observability. Validation steps confirm working state. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/012-alb-ingress-ui/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
manifests/retail-store/
├── kustomization.yaml           # Root kustomization (already exists)
├── ui/
│   ├── kustomization.yaml       # Updated to include ingress.yaml
│   ├── namespace.yaml           # Existing
│   ├── configMap.yaml           # Existing
│   ├── serviceAccount.yaml      # Existing
│   ├── service.yaml             # Existing
│   ├── deployment.yaml          # Existing
│   └── ingress.yaml             # NEW — ALB Ingress resource
└── [other services unchanged]
```

**Structure Decision**: Single new file (`ingress.yaml`) added to existing `manifests/retail-store/ui/` directory, integrated via the existing Kustomize structure. No new directories needed.
