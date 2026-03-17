# Implementation Plan: CloudFront + Private ALB for Retail Store UI

**Branch**: `014-cloudfront-private-alb` | **Date**: 2026-03-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/014-cloudfront-private-alb/spec.md`

## Summary

Deploy an internal ALB via Kubernetes Ingress (EKS Auto Mode) in private subnets, then create a CloudFront distribution with VPC origin to provide secure HTTPS access to the retail store UI. The ALB is never internet-facing — CloudFront is the sole entry point. Update demo app configuration to use the CloudFront URL.

## Technical Context

**Language/Version**: N/A — AWS CLI commands + Kubernetes YAML manifests
**Primary Dependencies**: AWS CLI v2, kubectl (with Kustomize)
**Storage**: N/A — infrastructure resources only
**Testing**: Manual validation via AWS CLI, kubectl, curl, browser
**Target Platform**: AWS (us-east-1) — EKS cluster `casual-indie-mushroom`, VPC `vpc-0def9b94fcbd9db8c`
**Project Type**: Infrastructure — Kubernetes manifests + AWS CDN configuration
**Performance Goals**: CloudFront distribution deployed within 15 minutes
**Constraints**: Internal ALB only, AWS CLI for CloudFront/VPC origin ops, no custom domain/ACM cert
**Scale/Scope**: 3 K8s manifests, 1 CloudFront distribution, 1 VPC origin, AgentCore Runtime redeploy

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simplicity First | PASS | Minimal resources: internal ALB + CloudFront VPC origin. No WAF, custom domain, or certificate complexity. |
| II. Iterative & Independent Delivery | PASS | Self-contained feature — adds secure internet access without affecting other services. |
| III. Python-Native Patterns | N/A | No Python code — infrastructure only (plus config update). |
| IV. Security by Design | PASS | ALB is internal, security group locked to CloudFront VPC origin only, HTTPS enforced at edge. Addresses the security concern that caused the previous internet-facing ALB to be deleted. |
| V. Observability & Debuggability | PASS | CloudFront access logs available, ALB health checks provide observability. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/014-cloudfront-private-alb/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
manifests/retail-store/
├── kustomization.yaml           # Root kustomization (existing)
├── ui/
│   ├── kustomization.yaml       # MODIFIED — add ingress manifests
│   ├── ingressclassparams.yaml  # NEW — scheme: internal
│   ├── ingressclass.yaml        # NEW — eks.amazonaws.com/alb controller
│   ├── ingress.yaml             # NEW — internal ALB Ingress
│   └── [existing files unchanged]

.env.example                     # MODIFIED — update RETAIL_STORE_URL
```

**Structure Decision**: 3 new Kubernetes manifests in existing `manifests/retail-store/ui/` directory. CloudFront and VPC origin created via AWS CLI (no manifest files). AgentCore Runtime updated via CLI.
