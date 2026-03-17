# Feature Specification: ALB Ingress for EKS Retail Store UI

**Feature Branch**: `012-alb-ingress-ui`
**Created**: 2026-03-17
**Status**: Draft
**Input**: Expose the EKS retail store UI service through an internet-facing AWS Application Load Balancer (ALB) by creating the required VPC networking infrastructure and a Kubernetes Ingress resource.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Access Retail Store UI from the Internet (Priority: P1)

As an end user, I want to access the retail store web UI from any browser on the internet so that I can browse products and interact with the application without needing cluster-level access.

**Why this priority**: This is the core deliverable — without internet-facing access, the UI is only reachable from within the cluster, making it unusable for external users or demos.

**Independent Test**: Navigate to the ALB's public DNS name in a browser and confirm the retail store UI loads and is interactive.

**Acceptance Scenarios**:

1. **Given** the ALB is provisioned and healthy, **When** a user navigates to the ALB DNS name via HTTP in a browser, **Then** the retail store UI homepage loads successfully.
2. **Given** the ALB is provisioned, **When** a user clicks through product pages on the UI, **Then** all pages render correctly and navigation works end-to-end.
3. **Given** the ALB is provisioned, **When** a user accesses the ALB URL from a different network (e.g., mobile hotspot, VPN off), **Then** the UI is still accessible, confirming true internet-facing availability.

---

### User Story 2 - VPC Public Networking Infrastructure (Priority: P1)

As a platform operator, I want public subnets with an Internet Gateway added to the existing VPC so that internet-facing load balancers can be provisioned by the EKS cluster.

**Why this priority**: This is a prerequisite for the ALB — without public subnets and an Internet Gateway, no internet-facing load balancer can be created.

**Independent Test**: Verify the Internet Gateway is attached, public subnets exist in two AZs, and the public route table has a default route to the Internet Gateway.

**Acceptance Scenarios**:

1. **Given** the VPC has only private subnets, **When** the networking setup is complete, **Then** two public subnets exist in different availability zones with non-overlapping CIDR blocks.
2. **Given** the public subnets are created, **When** inspecting their route table, **Then** there is a route `0.0.0.0/0` pointing to the attached Internet Gateway.
3. **Given** the public subnets are created, **When** inspecting their tags, **Then** they have `kubernetes.io/role/elb=1` and `kubernetes.io/cluster/casual-indie-mushroom=shared` tags for ALB auto-discovery.

---

### User Story 3 - ALB Health Checks Validate UI Availability (Priority: P2)

As a platform operator, I want the ALB to use the application's liveness probe endpoint for health checks so that traffic is only routed to healthy UI pods.

**Why this priority**: Health checks ensure reliability but are secondary to basic connectivity — the UI must be reachable first, then we ensure it stays reliably reachable.

**Independent Test**: Check ALB target group health in the AWS console or CLI; confirm targets are marked healthy using the liveness probe path.

**Acceptance Scenarios**:

1. **Given** the ALB is provisioned with health check configuration, **When** the UI pods are running normally, **Then** all targets in the ALB target group show as "healthy".
2. **Given** a UI pod becomes unhealthy, **When** the ALB performs its next health check, **Then** that target is marked unhealthy and removed from the rotation.

---

### Edge Cases

- What happens if the ALB cannot find subnets with the required tags? The Ingress resource will remain in a pending state without an ADDRESS — the operator must verify subnet tags.
- What happens if the UI pods are temporarily unavailable during deployment? The ALB health checks will mark targets unhealthy and return 503 until pods recover.
- What happens if the public subnet CIDR blocks conflict with existing ranges? Subnet creation will fail — CIDRs must be validated against existing allocations before creation.
- What happens if the Internet Gateway is detached or deleted? The ALB will lose internet connectivity and become unreachable from outside the VPC.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The VPC MUST have an Internet Gateway attached to enable internet-facing load balancing.
- **FR-002**: Two public subnets MUST be created in different availability zones with CIDR blocks that do not overlap with existing subnets (10.0.128.0/20, 10.0.144.0/20, 10.0.160.0/20).
- **FR-003**: A public route table MUST exist with a default route (0.0.0.0/0) pointing to the Internet Gateway, and both public subnets MUST be associated with it.
- **FR-004**: Public subnets MUST be tagged with `kubernetes.io/role/elb=1` and `kubernetes.io/cluster/casual-indie-mushroom=shared` for ALB auto-discovery.
- **FR-005**: Existing private subnets MUST be tagged with `kubernetes.io/role/internal-elb=1` (if not already tagged).
- **FR-006**: A Kubernetes Ingress resource MUST be created that provisions an internet-facing ALB routing HTTP traffic on port 80 to the UI service.
- **FR-007**: The ALB MUST use IP-based target type to route directly to pod IPs.
- **FR-008**: The ALB health check MUST use the application's liveness probe endpoint (`/actuator/health/liveness` on port 8080).
- **FR-009**: The Ingress manifest MUST be integrated into the existing Kustomize structure so it is applied alongside other retail store manifests.
- **FR-010**: Existing private subnet CIDR configurations and their route tables MUST NOT be modified (tagging is permitted per FR-005).

### Key Entities

- **Internet Gateway**: The gateway enabling internet connectivity for resources in public subnets within the VPC.
- **Public Subnet**: A subnet with a route to the Internet Gateway, used to host the ALB's network interfaces.
- **Ingress Resource**: A Kubernetes object that defines how external HTTP traffic is routed to internal services, triggering ALB provisioning via the EKS-managed load balancer controller.
- **ALB Target Group**: The set of pod IPs that the ALB forwards traffic to, with health checks ensuring only healthy pods receive requests.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The retail store UI is accessible from any internet-connected browser via the ALB's public DNS name over HTTP.
- **SC-002**: The ALB provisions successfully within 5 minutes of applying the Ingress resource, with a routable DNS address assigned.
- **SC-003**: All ALB target group members report healthy status using the application's liveness endpoint.
- **SC-004**: An HTTP request to the ALB URL returns a successful response (HTTP 200) with the retail store UI content.
- **SC-005**: Existing cluster workloads and private networking remain unaffected — no disruption to services running on private subnets.

## Assumptions

- The EKS cluster's Auto Mode `elasticLoadBalancing` feature is enabled and functional, managing the AWS Load Balancer Controller automatically.
- The VPC CIDR has sufficient address space for two additional /20 public subnets (e.g., 10.0.0.0/20 and 10.0.16.0/20 are available).
- The UI service in the `ui` namespace is running and healthy, with the liveness probe at `/actuator/health/liveness` on port 8080.
- AWS CLI credentials are configured with sufficient permissions to create VPC resources (Internet Gateway, subnets, route tables, tags).
- kubectl is configured with access to the `casual-indie-mushroom` EKS cluster.
- HTTP-only access is acceptable (no HTTPS/TLS termination required for this feature).

## Constraints

- All VPC networking operations must use AWS CLI commands (not CloudFormation or Terraform).
- The AWS Load Balancer Controller must NOT be installed manually — EKS Auto Mode manages it.
- Existing private subnets and their route tables must remain untouched.
- Only the ALB sits in public subnets — no NAT Gateway is needed.
