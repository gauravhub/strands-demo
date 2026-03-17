# Data Model: EKS Retail Store Deployment

**Date**: 2026-03-17
**Feature**: 011-eks-retail-store-deploy

## Kubernetes Resource Inventory

This feature does not introduce application-level data models. The "data model" is the set of Kubernetes resources created by the manifests.

### Namespaces (6)

| Name | Purpose |
|------|---------|
| ui | Frontend web UI |
| catalog | Product catalog service + MySQL |
| carts | Shopping cart service + DynamoDB-local |
| checkout | Checkout flow service + Redis |
| orders | Order management service + PostgreSQL |
| other | Shared configuration |

### Deployments (9)

| Name | Namespace | Replicas | Image |
|------|-----------|----------|-------|
| ui | ui | 1 | public.ecr.aws/aws-containers/retail-store-sample-ui:1.2.1 |
| catalog | catalog | 1 | public.ecr.aws/aws-containers/retail-store-sample-catalog:1.2.1 |
| carts | carts | 1 | public.ecr.aws/aws-containers/retail-store-sample-cart:1.2.1 |
| checkout | checkout | 1 | public.ecr.aws/aws-containers/retail-store-sample-checkout:1.2.1 |
| orders | orders | 1 | public.ecr.aws/aws-containers/retail-store-sample-orders:1.2.1 |
| carts-dynamodb | carts | 1 | amazon/dynamodb-local |
| checkout-redis | checkout | 1 | redis:6-alpine |
| orders-postgresql | orders | 1 | postgresql |

### StatefulSets (1)

| Name | Namespace | Replicas | Image |
|------|-----------|----------|-------|
| catalog-mysql | catalog | 1 | mysql:8.0 |

### Services (11)

| Name | Namespace | Type | Port |
|------|-----------|------|------|
| ui | ui | ClusterIP | 80→8080 |
| catalog | catalog | ClusterIP | 80→8080 |
| catalog-mysql | catalog | ClusterIP | 3306→3306 |
| carts | carts | ClusterIP | 80→8080 |
| carts-dynamodb | carts | ClusterIP | 8000→8000 |
| checkout | checkout | ClusterIP | 80→8080 |
| checkout-redis | checkout | ClusterIP | 6379→6379 |
| orders | orders | ClusterIP | 80→8080 |
| orders-postgresql | orders | ClusterIP | 5432→5432 |

### ConfigMaps (6)

| Name | Namespace | Key Data |
|------|-----------|----------|
| ui | ui | Backend service endpoint URLs |
| catalog | catalog | DB connection config |
| carts | carts | DynamoDB endpoint config |
| checkout | checkout | Redis URL, orders endpoint |
| orders | orders | PostgreSQL connection config |
| other | other | Shared configuration |

### Secrets (2)

| Name | Namespace | Purpose |
|------|-----------|---------|
| catalog-db | catalog | MySQL credentials |
| orders-db | orders | PostgreSQL credentials |

### ServiceAccounts (5)

| Name | Namespace |
|------|-----------|
| ui | ui |
| catalog | catalog |
| carts | carts |
| checkout | checkout |
| orders | orders |
