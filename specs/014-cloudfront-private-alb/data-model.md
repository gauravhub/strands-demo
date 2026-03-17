# Data Model: CloudFront + Private ALB

**Date**: 2026-03-17 | **Branch**: `014-cloudfront-private-alb`

## Infrastructure Resources

### Internal ALB (via Kubernetes Ingress)

| Attribute | Value |
|-----------|-------|
| Scheme | `internal` |
| Subnets | Private subnets (tagged `kubernetes.io/role/internal-elb=1`) |
| Target Type | `ip` (pod IPs) |
| Health Check | `/actuator/health/liveness` on port 8080 |
| Listener | HTTP port 80 |

### CloudFront VPC Origin

| Attribute | Value |
|-----------|-------|
| Origin Type | VPC origin |
| Target | Internal ALB ARN |
| VPC | `vpc-0def9b94fcbd9db8c` |
| Protocol | HTTP only |

### CloudFront Distribution

| Attribute | Value |
|-----------|-------|
| Origin | VPC origin (pointing to internal ALB) |
| Viewer Protocol Policy | Redirect HTTP to HTTPS |
| Origin Protocol Policy | HTTP only |
| Cache Policy | CachingDisabled (`4135ea2d-6df8-44a3-9df3-4b5a84be39ad`) |
| Default Root Object | (none — UI handles routing) |
| Domain | `dXXXXXXXXXX.cloudfront.net` (auto-assigned) |
| Certificate | Default CloudFront certificate |

### Kubernetes Resources

| Resource | Name | Namespace | Key Config |
|----------|------|-----------|------------|
| IngressClassParams | `alb` | (cluster-scoped) | `scheme: internal` |
| IngressClass | `alb` | (cluster-scoped) | `controller: eks.amazonaws.com/alb` |
| Ingress | `ui` | `ui` | `target-type: ip`, health check on 8080 |

## Resource Relationships

```
Internet User
  │
  ▼ (HTTPS)
CloudFront Distribution (*.cloudfront.net)
  │
  ▼ (HTTP, via VPC origin over AWS backbone)
Internal ALB (private subnets, scheme: internal)
  │
  ▼ (IP target, port 8080)
UI Pods (ClusterIP service, port 80 → container 8080)
```

## Configuration Updates

| Config | Old Value | New Value |
|--------|-----------|-----------|
| `RETAIL_STORE_URL` in `.env` | `http://k8s-ui-ui-...elb.amazonaws.com` | `https://dXXXXXXXXXX.cloudfront.net` |
| `RETAIL_STORE_URL` in `.env.example` | Same old ALB URL | Same CloudFront URL |
| AgentCore Runtime env var | Same old ALB URL | Same CloudFront URL |
