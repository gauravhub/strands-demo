# Feature Specification: EKS Retail Store Deployment

**Feature Branch**: `011-eks-retail-store-deploy`
**Created**: 2026-03-17
**Status**: Draft
**Input**: Deploy the EKS Workshop retail store sample application to my EKS cluster and copy all manifests into this repo for reference.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Copy Upstream Manifests into Repository (Priority: P1)

As a developer, I want all Kubernetes manifests from the EKS Workshop retail store sample application copied into `manifests/retail-store/` in my repository so that I have a local reference of the deployment configuration under version control.

**Why this priority**: Without the manifests in the repo, no deployment can occur. This is the foundational prerequisite for all subsequent stories.

**Independent Test**: Can be fully tested by verifying that the `manifests/retail-store/` directory exists with the correct file structure matching the upstream source, and that `kubectl kustomize manifests/retail-store/` renders valid YAML without errors.

**Acceptance Scenarios**:

1. **Given** the upstream manifests exist at `github.com/aws-samples/eks-workshop-v2/tree/main/manifests/base-application`, **When** the copy task completes, **Then** the directory `manifests/retail-store/` contains all files matching the upstream structure with identical content.
2. **Given** the manifests have been copied, **When** running `kubectl kustomize manifests/retail-store/`, **Then** valid Kubernetes YAML is rendered with all 6 components (ui, catalog, carts, checkout, orders, other).
3. **Given** the manifests have been copied, **When** comparing any local file to its upstream counterpart, **Then** the content is byte-for-byte identical (no modifications).

---

### User Story 2 - Deploy Application to EKS Cluster (Priority: P1)

As a developer, I want to deploy the retail store sample application to my EKS cluster using the local manifests so that the application is running and accessible within the cluster.

**Why this priority**: Deployment is the core goal of this feature. It depends on Story 1 (manifests present) and is required before validation can occur.

**Independent Test**: Can be fully tested by running `kubectl apply -k manifests/retail-store/` and verifying that all namespaces, deployments, and services are created in the cluster.

**Acceptance Scenarios**:

1. **Given** the manifests exist in `manifests/retail-store/`, **When** running `kubectl apply -k manifests/retail-store/`, **Then** all 6 namespaces are created: ui, catalog, carts, checkout, orders, other.
2. **Given** the deployment command has been executed, **When** all rollouts complete, **Then** all deployments report ready replicas: ui, catalog, carts, checkout, orders, carts-dynamodb, catalog-mysql, checkout-redis, orders-postgresql.
3. **Given** the application is deployed, **When** checking pod status across all namespaces, **Then** all pods are in Running state and passing their health checks (liveness and readiness probes).

---

### User Story 3 - Validate Deployment Health (Priority: P2)

As a developer, I want to verify that all services are healthy, interconnected, and accessible within the cluster so that I have confidence the deployment succeeded end-to-end.

**Why this priority**: Validation confirms the deployment is complete and functional. It depends on Story 2 but provides the confidence gate before considering the feature done.

**Independent Test**: Can be tested by running kubectl commands to verify namespace existence, deployment availability, pod health, and service resolution.

**Acceptance Scenarios**:

1. **Given** the application is deployed, **When** listing namespaces, **Then** all 6 namespaces exist: ui, catalog, carts, checkout, orders, other.
2. **Given** the application is deployed, **When** checking deployment status in each namespace, **Then** all deployments show available replicas matching desired replicas.
3. **Given** the application is deployed, **When** checking services in each namespace, **Then** the following services are resolvable: ui (ui namespace), catalog and catalog-mysql (catalog namespace), carts and carts-dynamodb (carts namespace), checkout and checkout-redis (checkout namespace), orders and orders-postgresql (orders namespace).
4. **Given** the UI service is running, **When** the UI pod starts, **Then** it can resolve its backend service endpoints (catalog.catalog.svc, carts.carts.svc, orders.orders.svc, checkout.checkout.svc).

---

### Edge Cases

- What happens if a namespace already exists from a previous deployment attempt? The deployment should succeed idempotently without errors.
- What happens if a pod fails to pull its container image? The deployment should report the image pull failure clearly in pod events.
- What happens if a database pod (MySQL, PostgreSQL, Redis, DynamoDB-local) fails to start? Dependent application pods should fail their readiness probes and report as not ready.
- What happens if the cluster has insufficient resources (CPU/memory) to schedule all pods? Pods should remain in Pending state with clear scheduling failure events.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST copy all Kustomize manifests from the upstream GitHub repository (`aws-samples/eks-workshop-v2`, path `manifests/base-application/`) into `manifests/retail-store/` in the local repository.
- **FR-002**: System MUST preserve the exact upstream directory structure: root `kustomization.yaml` referencing subdirectories `carts/`, `catalog/`, `checkout/`, `orders/`, `ui/`, `other/`.
- **FR-003**: System MUST NOT modify any upstream manifest content — all files must be copied as-is.
- **FR-004**: System MUST deploy the application using `kubectl apply -k manifests/retail-store/` (Kustomize-based deployment).
- **FR-005**: System MUST create 6 separate Kubernetes namespaces: ui, catalog, carts, checkout, orders, other.
- **FR-006**: System MUST deploy 5 application services (ui, catalog, carts, checkout, orders) and 4 data store services (catalog-mysql, carts-dynamodb, checkout-redis, orders-postgresql).
- **FR-007**: System MUST wait for all deployments to roll out successfully before considering deployment complete.
- **FR-008**: System MUST validate that all pods are Running and passing health checks after deployment.
- **FR-009**: System MUST validate that all Kubernetes services are created and resolvable within the cluster.

### Key Entities

- **Namespace**: Kubernetes namespace isolating each microservice (6 total: ui, catalog, carts, checkout, orders, other).
- **Deployment**: Kubernetes Deployment managing pod replicas for each service and its data store.
- **Service**: Kubernetes ClusterIP Service providing in-cluster networking for each component.
- **ConfigMap**: Configuration data for each service (e.g., UI endpoint URLs, database connection strings).
- **Secret**: Sensitive configuration for database credentials (catalog-db, orders-db).
- **StatefulSet**: Used for catalog-mysql to provide stable storage.
- **ServiceAccount**: Per-service identity for Kubernetes RBAC.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 37 manifest files are present in `manifests/retail-store/` with content identical to the upstream source.
- **SC-002**: All 6 namespaces are created and active in the cluster within 30 seconds of deployment.
- **SC-003**: All 9 deployments (5 application + 4 data store) report available replicas within 5 minutes of deployment.
- **SC-004**: All pods across all namespaces reach Running state and pass health checks within 5 minutes of deployment.
- **SC-005**: The deployment is idempotent — running `kubectl apply -k manifests/retail-store/` a second time produces no errors and results in the same desired state.

## Assumptions

- The EKS cluster is already provisioned and the developer's kubectl context is configured to communicate with it.
- The cluster has sufficient resources (CPU, memory, storage) to run all 9 deployments simultaneously.
- The cluster has internet access to pull public container images from `public.ecr.aws`.
- No conflicting resources (namespaces, services, deployments) with the same names exist in the cluster.
- Kustomize is available via `kubectl` (built-in since kubectl v1.14+).

## Manifest File Inventory

The following files will be copied from upstream, organized by subdirectory:

| Directory                         | Files                                                                                                                                           |
|-----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| `manifests/retail-store/`         | `kustomization.yaml`                                                                                                                            |
| `manifests/retail-store/carts/`   | `namespace.yaml`, `serviceAccount.yaml`, `configMap.yaml`, `deployment.yaml`, `deployment-db.yaml`, `service.yaml`, `service-db.yaml`, `kustomization.yaml` |
| `manifests/retail-store/catalog/` | `namespace.yaml`, `serviceAccount.yaml`, `configMap.yaml`, `secrets.yaml`, `deployment.yaml`, `statefulset-mysql.yaml`, `service.yaml`, `service-mysql.yaml`, `kustomization.yaml` |
| `manifests/retail-store/checkout/`| `namespace.yaml`, `serviceAccount.yaml`, `configMap.yaml`, `deployment.yaml`, `deployment-redis.yaml`, `service.yaml`, `service-redis.yaml`, `kustomization.yaml` |
| `manifests/retail-store/orders/`  | `namespace.yaml`, `serviceAccount.yaml`, `configMap.yaml`, `secrets.yaml`, `deployment.yaml`, `deployment-postgresql.yaml`, `service.yaml`, `service-postgresql.yaml`, `kustomization.yaml` |
| `manifests/retail-store/ui/`      | `namespace.yaml`, `serviceAccount.yaml`, `configMap.yaml`, `deployment.yaml`, `service.yaml`, `kustomization.yaml`                               |
| `manifests/retail-store/other/`   | `namespace.yaml`, `configMap.yaml`, `kustomization.yaml`                                                                                         |

**Total**: 37 files across 7 directories.
