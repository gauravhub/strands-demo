# Research: CloudFront + Private ALB for Retail Store UI

**Date**: 2026-03-17 | **Branch**: `014-cloudfront-private-alb`

## R1: CloudFront VPC Origins

**Decision**: Use CloudFront VPC origins to connect CloudFront to the internal ALB.

**Rationale**: CloudFront VPC origins (launched Nov 2024) allow CloudFront to reach ALBs, NLBs, and EC2 instances in private subnets without requiring them to be internet-facing. CloudFront traffic stays on the AWS backbone network, eliminating the need for public subnets, Internet Gateways, or NAT Gateways. The feature automatically manages security group rules to allow CloudFront traffic to reach the origin.

**How it works**:
1. Create the internal ALB via Kubernetes Ingress (EKS Auto Mode)
2. Create a VPC origin in CloudFront pointing to the ALB's ARN
3. Create a CloudFront distribution using the VPC origin
4. CloudFront automatically configures network connectivity through the VPC

**Alternatives considered**:
- CloudFront with custom header validation on public ALB — rejected; ALB still needs to be internet-facing, doesn't meet the security requirement.
- AWS Global Accelerator — rejected; doesn't provide HTTPS termination or caching, more expensive.
- API Gateway with VPC Link — rejected; adds complexity, not needed for a static web UI.

## R2: Internal ALB via EKS Auto Mode

**Decision**: Use `scheme: internal` in IngressClassParams to create an internal ALB.

**Rationale**: EKS Auto Mode with `elasticLoadBalancing: enabled` provisions ALBs based on IngressClassParams. Setting `scheme: internal` creates the ALB in private subnets (tagged with `kubernetes.io/role/internal-elb=1`). This is the same pattern as feature 012 but with `internal` instead of `internet-facing`.

**Key difference from feature 012**: The previous feature used `scheme: internet-facing` which required public subnets and was flagged as a security risk. This feature uses `scheme: internal` — no public subnets or Internet Gateway needed.

## R3: CloudFront Cache Policy for Dynamic Web App

**Decision**: Use AWS managed `CachingDisabled` policy (ID: `4135ea2d-6df8-44a3-9df3-4b5a84be39ad`).

**Rationale**: The retail store UI is a dynamic web application with session cookies and personalized content. Caching would cause stale content or cross-user data leaks. The `CachingDisabled` managed policy forwards all requests to the origin without caching, which is the correct behavior for this use case.

**Alternatives considered**:
- `CachingOptimized` — rejected; would cache dynamic content and cause stale pages.
- Custom cache policy with short TTL — rejected; adds complexity with minimal benefit for a demo app.

## R4: CloudFront Origin Protocol Policy

**Decision**: HTTP only for origin connections.

**Rationale**: The internal ALB doesn't have a TLS certificate. CloudFront terminates HTTPS at the edge and connects to the ALB over HTTP within the VPC. This is secure because the traffic between CloudFront and the ALB travels over the AWS backbone network within the VPC — it never traverses the public internet.

## R5: Security Group Management

**Decision**: CloudFront VPC origin automatically manages security group rules.

**Rationale**: When a VPC origin is created, CloudFront automatically adds inbound rules to the ALB's security group to allow traffic from CloudFront. This is a managed feature — no manual security group configuration is needed. The security group will only allow CloudFront VPC origin traffic, not `0.0.0.0/0`.

**Note**: After VPC origin creation, verify the security group rules to confirm no public access is allowed.

## R6: AgentCore Runtime Redeployment

**Decision**: Update `RETAIL_STORE_URL` env var and rebuild the runtime container.

**Rationale**: The `RETAIL_STORE_URL` currently points to the old (deleted) ALB URL. It needs to be updated to the new CloudFront HTTPS URL. This requires:
1. Upload new source zip to S3
2. Trigger CodeBuild to rebuild the container
3. Update the AgentCore Runtime with the new env var using the real Anthropic API key (not the masked CloudFormation value)

**Lesson learned from feature 013**: CloudFormation `NoEcho` parameters return `****` — always use the real key from `.env`.
