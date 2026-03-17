# Tasks: CloudFront + Private ALB for Retail Store UI

**Input**: Design documents from `/specs/014-cloudfront-private-alb/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: No automated tests — validation is manual (AWS CLI, kubectl, curl, browser).

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup (Verification)

**Purpose**: Verify prerequisites before making changes

<!-- parallel-group: 1 -->
- [ ] T001 Verify AWS CLI credentials for us-east-1 (`aws sts get-caller-identity`)
- [ ] T002 [P] Verify kubectl access to EKS cluster (`kubectl get nodes`)
- [ ] T003 [P] Verify UI service is running (`kubectl get svc -n ui && kubectl get pods -n ui`)
- [ ] T004 [P] Verify private subnets have `kubernetes.io/role/internal-elb=1` tag (`aws ec2 describe-subnets --filters Name=vpc-id,Values=vpc-0def9b94fcbd9db8c "Name=tag:kubernetes.io/role/internal-elb,Values=1"`)

---

## Phase 2: User Story 2 — Internal ALB via Kubernetes Ingress (Priority: P1)

**Goal**: Deploy an internal ALB in private subnets via EKS Auto Mode Ingress

**Independent Test**: ALB is provisioned with `internal` scheme in private subnets, unreachable from internet

<!-- sequential -->
- [ ] T005 [US2] Create `manifests/retail-store/ui/ingressclassparams.yaml` with `scheme: internal` and `apiGroup: eks.amazonaws.com/v1`
- [ ] T006 [P] [US2] Create `manifests/retail-store/ui/ingressclass.yaml` with controller `eks.amazonaws.com/alb` referencing the IngressClassParams
- [ ] T007 [P] [US2] Create `manifests/retail-store/ui/ingress.yaml` with `ingressClassName: alb`, annotations for `target-type: ip`, health check `/actuator/health/liveness` on port 8080, routing `/` to service `ui` port 80
- [ ] T008 [US2] Update `manifests/retail-store/ui/kustomization.yaml` to include `ingressclassparams.yaml`, `ingressclass.yaml`, and `ingress.yaml`
- [ ] T009 [US2] Apply manifests with `kubectl apply -k manifests/retail-store/`
- [ ] T010 [US2] Wait for internal ALB provisioning — verify Ingress has ADDRESS (`kubectl get ingress -n ui`, retry up to 5 minutes)
- [ ] T011 [US2] Validate ALB is internal: `aws elbv2 describe-load-balancers` — confirm scheme is `internal` and subnets are private
- [ ] T012 [US2] Validate ALB targets are healthy: `aws elbv2 describe-target-health`

**Checkpoint**: Internal ALB provisioned, healthy targets, scheme=internal

---

## Phase 3: User Story 1 — CloudFront Distribution with VPC Origin (Priority: P1) 🎯 MVP

**Goal**: Create CloudFront distribution with VPC origin pointing to the internal ALB, providing HTTPS access

**Independent Test**: Navigate to CloudFront HTTPS URL and see the retail store UI

**Depends on**: Phase 2 (internal ALB must exist)

<!-- sequential -->
- [ ] T013 [US1] Get the internal ALB ARN from `aws elbv2 describe-load-balancers` for use in VPC origin creation
- [ ] T014 [US1] Create CloudFront VPC origin pointing to the internal ALB ARN (`aws cloudfront create-vpc-origin`) — capture the VPC origin ID
- [ ] T015 [US1] Wait for VPC origin status to be `Deployed` (`aws cloudfront get-vpc-origin`, retry up to 5 minutes)
- [ ] T016 [US1] Create CloudFront distribution with: VPC origin as origin, `CachingDisabled` cache policy (`4135ea2d-6df8-44a3-9df3-4b5a84be39ad`), viewer-protocol-policy `redirect-to-https`, origin-protocol-policy `http-only`, comment `retail-store-ui` (`aws cloudfront create-distribution`)
- [ ] T017 [US1] Wait for CloudFront distribution to deploy — status `Deployed` (`aws cloudfront get-distribution`, retry up to 15 minutes)
- [ ] T018 [US1] Get the CloudFront domain name (`dXXXXXXXXXX.cloudfront.net`) from the distribution
- [ ] T019 [US1] Validate HTTPS access: `curl -sI https://<cloudfront-domain>` — confirm HTTP 200 and valid TLS
- [ ] T020 [US1] Validate HTTP-to-HTTPS redirect: `curl -sI http://<cloudfront-domain>` — confirm 301/302 redirect to HTTPS
- [ ] T021 [US1] Validate retail store UI loads in browser via CloudFront URL

**Checkpoint**: Retail store UI accessible via HTTPS CloudFront URL, HTTP redirects to HTTPS

---

## Phase 4: Security Validation (Part of US2)

**Goal**: Confirm the ALB is not accessible from the internet and security group is locked down

<!-- parallel-group: 2 -->
- [ ] T022 [US2] Verify ALB DNS does NOT resolve publicly — `nslookup <alb-dns> 8.8.8.8` should fail or return private IPs only
- [ ] T023 [P] [US2] Verify ALB security group — confirm no `0.0.0.0/0` inbound rules, only CloudFront VPC origin traffic allowed (`aws ec2 describe-security-groups`)

**Checkpoint**: ALB confirmed unreachable from internet, security group locked to CloudFront only

---

## Phase 5: User Story 3 — Update Demo App Configuration (Priority: P2)

**Goal**: Update RETAIL_STORE_URL to CloudFront HTTPS URL in all configurations

**Depends on**: Phase 3 (CloudFront URL must be known)

<!-- sequential -->
- [ ] T024 [US3] Update `RETAIL_STORE_URL` in `.env` to the CloudFront HTTPS URL
- [ ] T025 [P] [US3] Update `RETAIL_STORE_URL` in `.env.example` to the CloudFront HTTPS URL
- [ ] T026 [US3] Upload new source zip to S3 and trigger CodeBuild to rebuild AgentCore Runtime container (`aws codebuild start-build`)
- [ ] T027 [US3] Wait for CodeBuild to succeed, then update AgentCore Runtime with new image and `RETAIL_STORE_URL` env var (use real API key from `.env`, restore Cognito JWT authorizer)
- [ ] T028 [US3] Verify AgentCore Runtime is READY and agent responds correctly

**Checkpoint**: All configurations point to CloudFront HTTPS URL, agent works with new URL

---

## Phase 6: Polish & Cross-Cutting

**Purpose**: Final validation

<!-- parallel-group: 3 -->
- [ ] T029 Verify existing cluster workloads unaffected (`kubectl get pods --all-namespaces`)
- [ ] T030 [P] Verify private subnet route tables unchanged (`aws ec2 describe-route-tables`)
- [ ] T031 Record CloudFront URL, distribution ID, VPC origin ID, and ALB ARN for reference

---

## Dependencies & Execution Order

- **Phase 1**: No dependencies — start immediately
- **Phase 2**: Depends on Phase 1 — internal ALB creation
- **Phase 3**: Depends on Phase 2 — CloudFront needs ALB ARN
- **Phase 4**: Depends on Phase 3 — security validation after CloudFront sets up SG rules
- **Phase 5**: Depends on Phase 3 — needs CloudFront URL
- **Phase 6**: Depends on all phases complete

### Parallel Opportunities

- T002, T003, T004 (setup verification)
- T006, T007 (different manifest files)
- T022, T023 (independent security checks)
- T024, T025 (different .env files)
- T029, T030 (independent validation)

---

## Implementation Strategy

### MVP (Phases 1-3)

1. Verify prerequisites
2. Deploy internal ALB via Ingress
3. Create CloudFront VPC origin + distribution
4. **VALIDATE**: HTTPS access works via CloudFront URL

### Full Delivery

5. Validate security (Phase 4)
6. Update app config + redeploy runtime (Phase 5)
7. Final validation (Phase 6)

---

## Notes

- CloudFront VPC origin automatically manages ALB security group — no manual SG rules needed
- CloudFront distribution deployment takes 5-15 minutes — T017 should poll with patience
- Use `CachingDisabled` managed policy ID: `4135ea2d-6df8-44a3-9df3-4b5a84be39ad`
- AgentCore Runtime update: use real API key from `.env` (CloudFormation returns `****` for NoEcho params)
- Restore Cognito JWT authorizer on every runtime update (it gets wiped otherwise)
