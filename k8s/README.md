# Kubernetes Deployment Guide - Yelp Prototype

## Overview

This guide walks through deploying the Yelp prototype on a Kubernetes cluster (tested with minikube).

## Architecture

```
Frontend (nginx SPA) → Routes by path prefix → Backend Services:
  - /auth/*, /users/*, /favorites/*, /history/* → user-service (8001)
  - /restaurants/*, /ai-assistant/* → restaurant-service (8002)
  - /reviews/* → review-service (8003)
  - /owner/* → owner-service (8004)

All services connect to: mysql (port 3306)
All services share: uploads PVC
```

## Prerequisites

- **Docker** (with container images already built)
- **minikube** (or any Kubernetes cluster)
- **kubectl** (v1.20+)
- **At least 6GB RAM and 4 CPUs** available for minikube

Install on macOS with M-series:

```bash
# Install minikube
brew install minikube

# Install kubectl
brew install kubectl

# Start minikube with sufficient resources (M-series ARM64)
minikube start --cpus=4 --memory=6144 --driver=docker
```

## Step 1: Prepare Images

### Build Backend Image

```bash
# Evaluate minikube's Docker environment
eval $(minikube docker-env)

# Build backend image (uses local Dockerfile)
cd backend
docker build -t yelp-backend:latest .
cd ..
```

### Build Frontend Image

```bash
# Make sure you're still in minikube's Docker context
eval $(minikube docker-env)

# Build frontend image
cd frontend
docker build -t yelp-frontend:latest .
cd ..
```

Verify images exist:
```bash
docker images | grep yelp
# Should see:
# yelp-backend   latest
# yelp-frontend  latest
```

## Step 2: Set Up Secrets

Update secrets with your actual API keys:

```bash
# Create secret with your credentials
kubectl create secret generic yelp-secrets \
  --from-literal=MYSQL_ROOT_PASSWORD=rootpass \
  --from-literal=SECRET_KEY=seekrit4ron \
  --from-literal=GOOGLE_API_KEY=your_actual_google_api_key \
  --from-literal=TAVILY_API_KEY=your_actual_tavily_api_key \
  -n yelp-prototype
```

## Step 3: Deploy to Kubernetes

### Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### Create ConfigMap and Secrets

```bash
# Option 1: Using YAML (update placeholder values first)
kubectl apply -f k8s/config.yaml

# Option 2: Already created via kubectl create secret above (use this if you created secrets manually)
```

### Deploy MySQL

```bash
kubectl apply -f k8s/mysql.yaml

# Wait for MySQL to be ready
kubectl wait --for=condition=ready pod -l app=mysql -n yelp-prototype --timeout=300s

# Verify MySQL is running
kubectl get statefulset -n yelp-prototype
kubectl get pods -n yelp-prototype | grep mysql
```

### Deploy Uploads PVC

```bash
kubectl apply -f k8s/uploads-pvc.yaml

# Verify PVC is created
kubectl get pvc -n yelp-prototype
```

### Deploy Backend Services

```bash
kubectl apply -f k8s/backend.yaml

# Wait for all backend services to be ready
kubectl wait --for=condition=ready pod -l app=user-service -n yelp-prototype --timeout=300s
kubectl wait --for=condition=ready pod -l app=restaurant-service -n yelp-prototype --timeout=300s
kubectl wait --for=condition=ready pod -l app=review-service -n yelp-prototype --timeout=300s
kubectl wait --for=condition=ready pod -l app=owner-service -n yelp-prototype --timeout=300s

# Verify backend services are running
kubectl get deployments -n yelp-prototype
kubectl get pods -n yelp-prototype | grep service
```

### Deploy Frontend

```bash
kubectl apply -f k8s/frontend.yaml

# Wait for frontend to be ready
kubectl wait --for=condition=ready pod -l app=frontend -n yelp-prototype --timeout=300s

# Verify frontend is running
kubectl get pods -n yelp-prototype | grep frontend
```

### Full Stack at Once

Or, apply all manifests at once:

```bash
# Create namespace first
kubectl apply -f k8s/namespace.yaml

# Then apply all resources
kubectl apply -f k8s/config.yaml
kubectl apply -f k8s/uploads-pvc.yaml
kubectl apply -f k8s/mysql.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod --all -n yelp-prototype --timeout=600s
```

## Step 4: Access the Application

### Get Service Access

```bash
# For NodePort services, get the external IP/port
kubectl get svc -n yelp-prototype

# Frontend is accessible via NodePort 30080
minikube service frontend -n yelp-prototype
# This opens a browser automatically
```

Or manually:

```bash
# Get minikube IP
minikube ip

# Access frontend at: http://<minikube-ip>:30080
# Example: http://192.168.49.2:30080
```

### Access Backend API Docs

Backend services are not exposed outside the cluster, but you can port-forward to access them:

```bash
# Forward user-service to localhost:8001
kubectl port-forward -n yelp-prototype svc/user-service 8001:8001

# Access swagger docs: http://localhost:8001/docs
```

Similarly for other services:

```bash
kubectl port-forward -n yelp-prototype svc/restaurant-service 8002:8002
kubectl port-forward -n yelp-prototype svc/review-service 8003:8003
kubectl port-forward -n yelp-prototype svc/owner-service 8004:8004
```

## Step 5: Verify Everything Works

### Test Login

Use the pre-seeded test accounts:
- **Customer**: customer@test.com / password
- **Owner**: owner@test.com / password

### Test Connectivity Between Services

```bash
# Enter a pod and test service discovery
kubectl exec -it -n yelp-prototype <pod-name> -- /bin/bash

# Inside the pod, test DNS resolution
nslookup user-service.yelp-prototype.svc.cluster.local
nslookup mysql.yelp-prototype.svc.cluster.local

# Test HTTP connectivity
curl http://user-service:8001/health
curl http://mysql:3306  # Will fail but shows service is reachable
```

### Check Logs

```bash
# View logs for a specific service
kubectl logs -n yelp-prototype deployment/user-service -f
kubectl logs -n yelp-prototype deployment/restaurant-service -f
kubectl logs -n yelp-prototype deployment/frontend -f

# View MySQL logs
kubectl logs -n yelp-prototype statefulset/mysql -f
```

### Describe Resources

```bash
# Get detailed info about a pod
kubectl describe pod -n yelp-prototype <pod-name>

# Check resource usage
kubectl top nodes
kubectl top pods -n yelp-prototype
```

## Troubleshooting

### Pods Not Starting

Check pod status and events:

```bash
kubectl get pods -n yelp-prototype -o wide
kubectl describe pod -n yelp-prototype <pod-name>
kubectl events -n yelp-prototype --sort-by='.lastTimestamp'
```

### Database Connection Errors

Verify MySQL is healthy:

```bash
kubectl get statefulset -n yelp-prototype
kubectl describe statefulset mysql -n yelp-prototype
kubectl logs -n yelp-prototype statefulset/mysql | tail -20

# Test MySQL directly
kubectl port-forward -n yelp-prototype statefulset/mysql 3306:3306
mysql -h localhost -u root -prootpass yelp_db
```

### Backend Service Errors

Check service endpoints:

```bash
kubectl get endpoints -n yelp-prototype
kubectl describe svc user-service -n yelp-prototype

# Test service connectivity from another pod
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- curl http://user-service:8001/health
```

### Frontend Not Loading

Check frontend logs and nginx config:

```bash
kubectl logs -n yelp-prototype deployment/frontend -f

# Exec into frontend pod and check nginx
kubectl exec -it -n yelp-prototype <frontend-pod> -- cat /var/log/nginx/error.log
kubectl exec -it -n yelp-prototype <frontend-pod> -- cat /var/log/nginx/access.log
```

### Secrets Not Available

Verify secrets exist:

```bash
kubectl get secrets -n yelp-prototype
kubectl describe secret yelp-secrets -n yelp-prototype
```

## Cleanup

### Remove Everything

```bash
# Delete the entire namespace (removes all resources within it)
kubectl delete namespace yelp-prototype

# Or delete individual resources
kubectl delete deployment --all -n yelp-prototype
kubectl delete statefulset --all -n yelp-prototype
kubectl delete svc --all -n yelp-prototype
kubectl delete pvc --all -n yelp-prototype
kubectl delete configmap --all -n yelp-prototype
kubectl delete secret --all -n yelp-prototype
```

### Stop minikube

```bash
minikube stop
minikube delete  # Completely removes minikube VM
```

## Scaling

Scale any service to multiple replicas:

```bash
# Scale user-service to 3 replicas
kubectl scale deployment user-service --replicas=3 -n yelp-prototype

# View scaled deployment
kubectl get deployment user-service -n yelp-prototype
```

**Note**: With multiple backend replicas sharing a single `uploads-pvc`, ensure the PVC has `accessMode: ReadWriteMany` or mount the same volume to all replicas. By default, we use `ReadWriteOnce` which works fine with single replicas.

## Production Considerations

For a production deployment:

1. **Use a managed Kubernetes service** (EKS, GKE, AKS)
2. **Store secrets in a vault** (HashiCorp Vault, AWS Secrets Manager)
3. **Enable RBAC** and pod security policies
4. **Use persistent volumes** with proper backup strategies
5. **Implement resource quotas** and network policies
6. **Set up monitoring** (Prometheus, Grafana)
7. **Use Ingress** instead of NodePort for public access
8. **Implement auto-scaling** with HPA
9. **Use a container registry** (Docker Hub, ECR, GCR)
10. **Configure environment-specific values** (dev, staging, prod)

## File Structure

```
k8s/
├── namespace.yaml         # Namespace definition
├── config.yaml            # ConfigMap + Secret
├── mysql.yaml            # MySQL StatefulSet + Service + PVC
├── backend.yaml          # 4 Backend Deployments + 4 Services
├── frontend.yaml         # Frontend Deployment + Service
├── uploads-pvc.yaml      # Shared uploads PVC
└── README.md             # This file
```

## Quick Redeploy

To redeploy after code changes:

```bash
# Rebuild images
eval $(minikube docker-env)
docker build -t yelp-backend:latest ./backend
docker build -t yelp-frontend:latest ./frontend

# Restart deployments to pick up new images
kubectl rollout restart deployment/user-service -n yelp-prototype
kubectl rollout restart deployment/restaurant-service -n yelp-prototype
kubectl rollout restart deployment/review-service -n yelp-prototype
kubectl rollout restart deployment/owner-service -n yelp-prototype
kubectl rollout restart deployment/frontend -n yelp-prototype

# Watch rollout progress
kubectl rollout status deployment/user-service -n yelp-prototype -w
```

## Useful Commands Summary

```bash
# Get all resources
kubectl get all -n yelp-prototype

# Watch pods in real-time
kubectl get pods -n yelp-prototype -w

# Get detailed pod info
kubectl get pods -n yelp-prototype -o wide

# Stream logs from a deployment
kubectl logs -f deployment/user-service -n yelp-prototype --tail=100

# Execute command in a pod
kubectl exec -it <pod-name> -n yelp-prototype -- <command>

# Port-forward a service
kubectl port-forward svc/user-service 8001:8001 -n yelp-prototype

# Restart a deployment
kubectl rollout restart deployment/user-service -n yelp-prototype

# Check events
kubectl get events -n yelp-prototype --sort-by='.lastTimestamp'
```