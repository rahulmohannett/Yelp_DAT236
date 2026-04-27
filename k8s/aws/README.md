# AWS EKS (EC2 Nodes) Deployment

This overlay deploys Yelp Prototype to **Amazon EKS with EC2 worker nodes**.

It keeps your existing `k8s/` manifests intact and applies AWS-specific behavior:

- ECR images instead of local images
- `imagePullPolicy: IfNotPresent`
- ALB Ingress for public access
- `gp3` StorageClass for PVCs
- Externalized secret creation (no hardcoded API keys in YAML)

## Prerequisites

- AWS account and IAM permissions for EKS, EC2, ELB, ECR
- `aws`, `kubectl`, `eksctl`, `helm` installed
- Docker available locally to build/push images

## 1) Create ECR repositories

```bash
aws ecr create-repository --repository-name yelp-backend
aws ecr create-repository --repository-name yelp-frontend
```

## 2) Build and push images

```bash
AWS_ACCOUNT_ID=<your-account-id>
AWS_REGION=<your-region>

aws ecr get-login-password --region "$AWS_REGION" | \
docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

docker build -t yelp-backend:latest ./backend
docker build -t yelp-frontend:latest ./frontend

docker tag yelp-backend:latest "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/yelp-backend:latest"
docker tag yelp-frontend:latest "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/yelp-frontend:latest"

docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/yelp-backend:latest"
docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/yelp-frontend:latest"
```

## 3) Create EKS cluster with EC2 nodes

```bash
eksctl create cluster \
  --name yelp-eks \
  --region "$AWS_REGION" \
  --nodes 2 \
  --node-type t3.large \
  --managed
```

## 4) Install AWS Load Balancer Controller

Follow AWS docs for IRSA + controller install:

- [AWS Load Balancer Controller Installation](https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html)

This is required for `k8s/aws/ingress.yaml` to create an ALB.

## 5) Prepare namespace + secret

```bash
kubectl apply -f k8s/namespace.yaml

kubectl create secret generic yelp-secrets \
  -n yelp-prototype \
  --from-literal=SECRET_KEY='<strong-random-secret>' \
  --from-literal=GOOGLE_API_KEY='<google-api-key>' \
  --from-literal=TAVILY_API_KEY='<tavily-api-key>'
```

If secret already exists, delete/recreate:

```bash
kubectl delete secret yelp-secrets -n yelp-prototype
```

## 6) Set ECR image names in kustomization

Edit `k8s/aws/kustomization.yaml`:

- replace `<AWS_ACCOUNT_ID>`
- replace `<AWS_REGION>`

Also edit `k8s/aws/configmap.yaml` and set `CORS_ORIGINS` to your real domain(s).

## 7) Deploy the stack

```bash
kubectl apply -k k8s/aws
kubectl get pods -n yelp-prototype
kubectl get svc -n yelp-prototype
kubectl get ingress -n yelp-prototype
```

## 8) Get ALB DNS

```bash
kubectl get ingress yelp-ingress -n yelp-prototype
```

Use the returned hostname as your public URL.

## TLS (recommended)

In `k8s/aws/ingress.yaml`, set:

- `alb.ingress.kubernetes.io/certificate-arn`
- HTTPS listen ports
- `alb.ingress.kubernetes.io/ssl-redirect: "443"`

Then reapply:

```bash
kubectl apply -k k8s/aws
```

## Notes

- This overlay currently runs single-replica services (same as base manifests).
- For production, add HPA, PodDisruptionBudgets, and CloudWatch log shipping.
