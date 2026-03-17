# Feature Specification: CloudFront + Private ALB for Retail Store UI

**Feature Branch**: `014-cloudfront-private-alb`
**Created**: 2026-03-17
**Status**: Draft
**Input**: Create a secure, private ALB + CloudFront architecture to expose the EKS retail store UI service to the internet without making the ALB directly internet-facing.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Access Retail Store UI Securely via HTTPS (Priority: P1)

As an end user, I want to access the retail store web UI via a secure HTTPS URL so that I can browse the store from any browser on the internet without the backend load balancer being directly exposed.

**Why this priority**: This is the core deliverable — users need a secure, public-facing URL to access the store. The internal ALB + CloudFront architecture ensures the load balancer is never directly reachable from the internet.

**Independent Test**: Navigate to the CloudFront HTTPS URL in a browser and confirm the retail store UI loads with a valid TLS certificate.

**Acceptance Scenarios**:

1. **Given** the CloudFront distribution is deployed, **When** a user navigates to the CloudFront HTTPS URL in a browser, **Then** the retail store UI homepage loads successfully with a valid TLS certificate.
2. **Given** the CloudFront distribution is deployed, **When** a user accesses the HTTP version of the CloudFront URL, **Then** the request is automatically redirected to HTTPS.
3. **Given** the CloudFront distribution is deployed, **When** a user clicks through product pages on the UI, **Then** all pages render correctly and navigation works end-to-end.

---

### User Story 2 - Internal ALB Not Directly Accessible from the Internet (Priority: P1)

As a platform operator, I want the load balancer to be internal (private) so that it cannot be accessed directly from the internet, reducing the attack surface.

**Why this priority**: This is the security requirement that motivated the entire feature — the previous internet-facing ALB was flagged as a security risk. The ALB must only be reachable via CloudFront.

**Independent Test**: Attempt to resolve and connect to the ALB's DNS name from the internet — it should be unreachable (private DNS, no public IP).

**Acceptance Scenarios**:

1. **Given** the internal ALB is provisioned, **When** attempting to access the ALB DNS name directly from the internet, **Then** the connection fails (DNS does not resolve publicly or connection times out).
2. **Given** the internal ALB is provisioned, **When** inspecting its configuration, **Then** it is in the private subnets with scheme `internal`.
3. **Given** the ALB security group is configured, **When** inspecting inbound rules, **Then** only CloudFront VPC origin traffic is allowed — no `0.0.0.0/0` rules exist.

---

### User Story 3 - Update Demo App Configuration (Priority: P2)

As a platform operator, I want the demo application's configuration updated to use the new CloudFront URL so that all references to the retail store point to the secure endpoint.

**Why this priority**: After the infrastructure is in place, the application configuration must be updated so the agent knows the correct URL for browser automation and user references.

**Independent Test**: Verify the `RETAIL_STORE_URL` environment variable in both local config and AgentCore Runtime points to the CloudFront HTTPS URL.

**Acceptance Scenarios**:

1. **Given** the CloudFront URL is available, **When** the AgentCore Runtime is redeployed with the new URL, **Then** the agent uses the CloudFront URL as the default retail store target.
2. **Given** the local `.env` file is updated, **When** running the Streamlit app locally, **Then** it uses the CloudFront URL for the retail store.

---

### Edge Cases

- What happens if CloudFront cannot reach the internal ALB? CloudFront returns a 502/503 error — the operator should check ALB health, security group rules, and VPC origin configuration.
- What happens if the ALB target pods are unhealthy? CloudFront passes through the ALB's 503 response — the operator should check pod health and liveness probe status.
- What happens during CloudFront distribution deployment? Deployment takes 5-15 minutes — the URL is not accessible until the distribution status changes to "Deployed".
- What happens if someone discovers the internal ALB DNS name? The DNS only resolves within the VPC — it is not reachable from the public internet.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: An internal (private) load balancer MUST be provisioned within the VPC's private subnets to route traffic to the retail store UI service.
- **FR-002**: The load balancer scheme MUST be `internal` — it MUST NOT be internet-facing.
- **FR-003**: The load balancer MUST use IP-based targeting to route directly to pod IPs.
- **FR-004**: The load balancer health check MUST use the application's liveness probe endpoint (`/actuator/health/liveness` on port 8080).
- **FR-005**: A content delivery network distribution MUST be created with the internal load balancer as its origin, using VPC origin connectivity.
- **FR-006**: The CDN MUST enforce HTTPS on the edge, automatically redirecting HTTP requests to HTTPS.
- **FR-007**: The CDN-to-origin connection MUST use HTTP (within the VPC) since the internal load balancer does not have a TLS certificate.
- **FR-008**: The CDN caching policy MUST be configured for a dynamic web application (minimal or no caching).
- **FR-009**: The load balancer's security group MUST restrict inbound traffic to only the CDN's VPC origin — no public internet access allowed.
- **FR-010**: The load balancer manifests MUST be integrated into the existing Kustomize structure alongside other retail store manifests.
- **FR-011**: The `RETAIL_STORE_URL` environment variable MUST be updated to the CDN's HTTPS URL in both local configuration and the AgentCore Runtime deployment.
- **FR-012**: Existing private subnets and their route tables MUST NOT be modified.

### Key Entities

- **Internal Load Balancer**: A private load balancer within the VPC that routes traffic to the UI service pods. Not directly accessible from the internet.
- **VPC Origin**: A connectivity mechanism that allows the CDN to reach the internal load balancer through the VPC's private network, without requiring the load balancer to be public.
- **CDN Distribution**: An edge network distribution that serves as the public-facing entry point, providing HTTPS termination, caching, and global edge delivery.
- **Security Group**: A network access control that restricts which traffic sources can reach the internal load balancer.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The retail store UI is accessible from any internet-connected browser via the CDN's HTTPS URL with a valid TLS certificate.
- **SC-002**: HTTP requests to the CDN URL are automatically redirected to HTTPS.
- **SC-003**: The internal load balancer is NOT accessible from the public internet — direct access attempts fail.
- **SC-004**: The load balancer's security group has zero inbound rules allowing `0.0.0.0/0` — only CDN VPC origin traffic is permitted.
- **SC-005**: All load balancer target group members report healthy status.
- **SC-006**: Existing cluster workloads and private networking remain unaffected.
- **SC-007**: The demo application's configuration references the CDN HTTPS URL as the retail store endpoint.

## Assumptions

- The EKS cluster's Auto Mode `elasticLoadBalancing` feature is enabled and functional.
- The VPC private subnets are properly tagged for internal load balancer auto-discovery (`kubernetes.io/role/internal-elb=1`).
- The UI service in the `ui` namespace is running and healthy.
- AWS CLI credentials are configured with sufficient permissions for load balancer, CDN, and VPC origin operations.
- kubectl is configured with access to the EKS cluster.
- No custom domain or custom TLS certificate is needed — the default CDN domain and certificate are sufficient.
- The CDN VPC origin feature is available in `us-east-1`.

## Constraints

- The load balancer MUST be internal — never internet-facing.
- No public subnets or Internet Gateway are needed for this architecture.
- Existing private subnets and their route tables must remain untouched.
- The EKS-managed load balancer controller must NOT be installed manually.
- All CDN and VPC origin operations must use AWS CLI (not CloudFormation or Terraform).
- The AgentCore Runtime must be redeployed with the updated `RETAIL_STORE_URL`.
