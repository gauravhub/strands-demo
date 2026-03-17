# Quickstart: ALB Ingress for EKS Retail Store UI

**Date**: 2026-03-17 | **Branch**: `012-alb-ingress-ui`

## Prerequisites

- AWS CLI v2 configured with credentials for `us-east-1`
- kubectl configured for EKS cluster `casual-indie-mushroom`
- Retail store application already deployed (UI service running in `ui` namespace)

## Steps

### 1. Create VPC Public Infrastructure

```bash
# Create and attach Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway --query 'InternetGateway.InternetGatewayId' --output text --region us-east-1)
aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id vpc-0def9b94fcbd9db8c --region us-east-1

# Create public subnets
SUBNET_1A=$(aws ec2 create-subnet --vpc-id vpc-0def9b94fcbd9db8c --cidr-block 10.0.0.0/20 --availability-zone us-east-1a --query 'Subnet.SubnetId' --output text --region us-east-1)
SUBNET_1B=$(aws ec2 create-subnet --vpc-id vpc-0def9b94fcbd9db8c --cidr-block 10.0.16.0/20 --availability-zone us-east-1b --query 'Subnet.SubnetId' --output text --region us-east-1)

# Enable auto-assign public IPs
aws ec2 modify-subnet-attribute --subnet-id $SUBNET_1A --map-public-ip-on-launch --region us-east-1
aws ec2 modify-subnet-attribute --subnet-id $SUBNET_1B --map-public-ip-on-launch --region us-east-1

# Create and configure public route table
RT_ID=$(aws ec2 create-route-table --vpc-id vpc-0def9b94fcbd9db8c --query 'RouteTable.RouteTableId' --output text --region us-east-1)
aws ec2 create-route --route-table-id $RT_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID --region us-east-1
aws ec2 associate-route-table --route-table-id $RT_ID --subnet-id $SUBNET_1A --region us-east-1
aws ec2 associate-route-table --route-table-id $RT_ID --subnet-id $SUBNET_1B --region us-east-1

# Tag public subnets for ALB discovery
for SUBNET in $SUBNET_1A $SUBNET_1B; do
  aws ec2 create-tags --resources $SUBNET --tags Key=kubernetes.io/role/elb,Value=1 Key=kubernetes.io/cluster/casual-indie-mushroom,Value=shared --region us-east-1
done

# Tag private subnets for internal ELB
for SUBNET in subnet-0d4fd966d44fc9c0c subnet-04fee54afd4f1c444 subnet-04bfcab1b517df4fe; do
  aws ec2 create-tags --resources $SUBNET --tags Key=kubernetes.io/role/internal-elb,Value=1 --region us-east-1
done
```

### 2. Apply Kubernetes Ingress

```bash
kubectl apply -k manifests/retail-store/
```

### 3. Validate

```bash
# Wait for ALB address (may take 2-3 minutes)
kubectl get ingress -n ui -w

# Once ADDRESS appears, test with curl
ALB_URL=$(kubectl get ingress ui -n ui -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl -s -o /dev/null -w "%{http_code}" http://$ALB_URL
```

## Expected Result

- `kubectl get ingress -n ui` shows an ALB DNS address
- `curl http://<ALB_URL>` returns HTTP 200
- Browser navigation to `http://<ALB_URL>` loads the retail store UI
