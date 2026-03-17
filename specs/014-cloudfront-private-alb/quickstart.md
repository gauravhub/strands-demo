# Quickstart: CloudFront + Private ALB

**Date**: 2026-03-17 | **Branch**: `014-cloudfront-private-alb`

## Prerequisites

- AWS CLI v2 configured for us-east-1
- kubectl configured for EKS cluster `casual-indie-mushroom`
- Retail store UI deployed in `ui` namespace
- Private subnets tagged with `kubernetes.io/role/internal-elb=1`

## Steps

### 1. Deploy Internal ALB via Kubernetes Ingress

```bash
kubectl apply -k manifests/retail-store/
# Wait for internal ALB to provision
kubectl get ingress -n ui -w
```

### 2. Create CloudFront VPC Origin

```bash
ALB_ARN=$(aws elbv2 describe-load-balancers --region us-east-1 \
  --query 'LoadBalancers[?Scheme==`internal`] | [0].LoadBalancerArn' --output text)

VPC_ORIGIN_ID=$(aws cloudfront create-vpc-origin \
  --vpc-origin-endpoint-config \
    "Name=retail-store-alb,Arn=$ALB_ARN,HTTPPort=80,ProtocolPolicy=http-only,OriginSslProtocols={Quantity=1,Items=[TLSv1.2]}" \
  --query 'VpcOrigin.Id' --output text)
```

### 3. Create CloudFront Distribution

```bash
aws cloudfront create-distribution \
  --distribution-config '{...}'  # See tasks for full config
```

### 4. Update App Configuration

```bash
CF_URL="https://$(aws cloudfront list-distributions \
  --query 'DistributionList.Items[?Comment==`retail-store-ui`].DomainName' --output text)"
# Update .env, .env.example, and AgentCore Runtime
```

## Expected Result

- CloudFront URL (https://dXXXXXXXXXX.cloudfront.net) serves the retail store UI over HTTPS
- Internal ALB is NOT accessible from the public internet
- ALB security group only allows CloudFront VPC origin traffic
