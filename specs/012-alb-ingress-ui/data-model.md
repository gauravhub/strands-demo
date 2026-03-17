# Data Model: ALB Ingress for EKS Retail Store UI

**Date**: 2026-03-17 | **Branch**: `012-alb-ingress-ui`

## Infrastructure Resources

### Internet Gateway

| Attribute | Value |
|-----------|-------|
| VPC | `vpc-0def9b94fcbd9db8c` |
| Name Tag | `casual-indie-mushroom-igw` |
| State | Attached |

### Public Subnets

| Attribute | Subnet 1 | Subnet 2 |
|-----------|----------|----------|
| CIDR | `10.0.0.0/20` | `10.0.16.0/20` |
| AZ | `us-east-1a` | `us-east-1b` |
| VPC | `vpc-0def9b94fcbd9db8c` | `vpc-0def9b94fcbd9db8c` |
| MapPublicIpOnLaunch | true | true |
| Tags | `kubernetes.io/role/elb=1`, `kubernetes.io/cluster/casual-indie-mushroom=shared` | Same |
| Name Tag | `casual-indie-mushroom-public-1a` | `casual-indie-mushroom-public-1b` |

### Public Route Table

| Attribute | Value |
|-----------|-------|
| VPC | `vpc-0def9b94fcbd9db8c` |
| Name Tag | `casual-indie-mushroom-public-rt` |
| Routes | `0.0.0.0/0` → Internet Gateway |
| Associations | Both public subnets |

### Existing Private Subnets (tag additions only)

| Subnet ID | AZ | Additional Tag |
|-----------|----|----------------|
| `subnet-0d4fd966d44fc9c0c` | us-east-1a | `kubernetes.io/role/internal-elb=1` |
| `subnet-04fee54afd4f1c444` | us-east-1b | `kubernetes.io/role/internal-elb=1` |
| `subnet-04bfcab1b517df4fe` | us-east-1c | `kubernetes.io/role/internal-elb=1` |

## Kubernetes Resources

### Ingress

| Attribute | Value |
|-----------|-------|
| Name | `ui` |
| Namespace | `ui` |
| IngressClass | `alb` |
| Scheme | `internet-facing` |
| Target Type | `ip` |
| Listen Ports | `[{"HTTP": 80}]` |
| Health Check Path | `/actuator/health/liveness` |
| Health Check Port | `8080` |
| Backend Service | `ui` (port 80) |
| Path | `/` (Prefix) |

## Resource Relationships

```
Internet
  │
  ▼
Internet Gateway (attached to VPC)
  │
  ▼
Public Subnets (2 AZs) ──── Public Route Table (0.0.0.0/0 → IGW)
  │
  ▼
ALB (provisioned by Ingress via EKS Auto Mode)
  │
  ▼
Pod IPs (IP target type, port 8080)
  │
  ▼
UI Service (ClusterIP, port 80 → container 8080)
```
