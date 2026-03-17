# Research: EKS Retail Store Deployment

**Date**: 2026-03-17
**Feature**: 011-eks-retail-store-deploy

## Research Summary

No NEEDS CLARIFICATION items were identified in the Technical Context. All decisions are straightforward:

### Decision 1: Manifest Source

- **Decision**: Fetch files from GitHub API via MCP tools (owner: `aws-samples`, repo: `eks-workshop-v2`, path: `manifests/base-application/`)
- **Rationale**: Direct GitHub API access is available via the existing `mcp__github__get_file_contents` tool, avoiding the need for git clone or curl
- **Alternatives considered**: `git clone` (heavier, pulls entire repo), `curl` raw URLs (less reliable, no auth)

### Decision 2: Deployment Mechanism

- **Decision**: `kubectl apply -k manifests/retail-store/` (Kustomize)
- **Rationale**: Specified in requirements (FR-004); Kustomize is built into kubectl since v1.14+
- **Alternatives considered**: Helm (not applicable — upstream uses Kustomize), plain `kubectl apply -f` (doesn't support Kustomize overlays)

### Decision 3: Validation Approach

- **Decision**: kubectl commands to verify namespaces, deployments, pods, and services
- **Rationale**: Direct kubectl queries are the simplest way to validate cluster state; no additional tools needed
- **Alternatives considered**: Custom validation script (over-engineering for a one-time deployment)
