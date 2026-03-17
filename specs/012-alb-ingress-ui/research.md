# Research: ALB Ingress for EKS Retail Store UI

**Date**: 2026-03-17 | **Branch**: `012-alb-ingress-ui`

## R1: EKS Auto Mode ALB Provisioning

**Decision**: Use the `alb` IngressClass provided by EKS Auto Mode — no manual controller installation.

**Rationale**: EKS Auto Mode with `elasticLoadBalancing: enabled` automatically manages the AWS Load Balancer Controller. Creating a Kubernetes Ingress with `ingressClassName: alb` triggers automatic ALB provisioning. This is the simplest path with zero controller management overhead.

**Alternatives considered**:
- Manual AWS Load Balancer Controller installation via Helm — rejected per constraint (EKS Auto Mode manages it).
- NLB via Service type LoadBalancer — rejected; ALB provides HTTP-level routing and health checks needed for the UI.

## R2: Public Subnet CIDR Selection

**Decision**: Use `10.0.0.0/20` (us-east-1a) and `10.0.16.0/20` (us-east-1b) for public subnets.

**Rationale**: These CIDR blocks are in the lower range of the VPC address space and do not overlap with existing private subnets (10.0.128.0/20, 10.0.144.0/20, 10.0.160.0/20 which are all in the upper range). Each /20 provides 4,091 usable IPs — more than sufficient for ALB ENIs.

**Alternatives considered**:
- Smaller /24 subnets — viable but /20 matches existing subnet sizing for consistency.
- Three public subnets (one per AZ) — unnecessary; ALB requires minimum 2 AZs, and 2 subnets is simpler.

## R3: ALB Subnet Auto-Discovery Tags

**Decision**: Tag public subnets with `kubernetes.io/role/elb=1` and `kubernetes.io/cluster/casual-indie-mushroom=shared`. Tag private subnets with `kubernetes.io/role/internal-elb=1`.

**Rationale**: The AWS Load Balancer Controller uses these tags to discover which subnets to place ALB ENIs in. `kubernetes.io/role/elb=1` marks subnets for internet-facing ALBs. The cluster tag with value `shared` indicates the subnet is shared (not exclusively owned by the cluster). Private subnet tags are best practice even though not needed for this feature.

**Alternatives considered**:
- Explicit subnet annotation on Ingress (`alb.ingress.kubernetes.io/subnets`) — works but tags are the standard auto-discovery mechanism and more maintainable.

## R4: ALB Health Check Configuration

**Decision**: Use `/actuator/health/liveness` on port 8080 as the ALB health check path, matching the UI deployment's liveness probe.

**Rationale**: The UI application exposes a Spring Boot Actuator liveness endpoint. Using the same path as the Kubernetes liveness probe ensures consistency — if the pod is healthy for Kubernetes, it's healthy for the ALB. Port 8080 is the container port the application listens on.

**Alternatives considered**:
- Root path `/` — would work but is heavier (renders full UI page) and doesn't specifically test application health.
- Readiness probe path — liveness is more appropriate for ALB since we want to know if the app process is alive.

## R5: Target Type Selection

**Decision**: Use `ip` target type for ALB targets.

**Rationale**: IP target type routes directly to pod IPs via the VPC CNI, bypassing kube-proxy. This is the recommended approach for EKS with the AWS Load Balancer Controller and provides better performance and more accurate load distribution across pods.

**Alternatives considered**:
- `instance` target type — routes to NodePort, adding an extra hop and less granular distribution. Not optimal for EKS Auto Mode.
