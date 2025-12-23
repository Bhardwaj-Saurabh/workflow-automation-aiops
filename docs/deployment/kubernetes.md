# Kubernetes Deployment Guide

Complete guide for deploying the AI Assessment System to Kubernetes using Helm with **microservices architecture**.

---

## Architecture Overview

The application is deployed as two separate services:

```
┌─────────────────────────────────────────────────────┐
│                Kubernetes Cluster                    │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │         Ingress (NGINX)                     │    │
│  └──────────────────┬─────────────────────────┘    │
│                     │                               │
│  ┌──────────────────▼─────────────────────────┐    │
│  │    Frontend Service (LoadBalancer)          │    │
│  │    ai-assessment-frontend                   │    │
│  └──────────────────┬─────────────────────────┘    │
│                     │                               │
│  ┌──────────────────▼─────────────────────────┐    │
│  │    Frontend Deployment (2-8 pods)           │    │
│  │    Streamlit UI                             │    │
│  │    Port: 8501                               │    │
│  └──────────────────┬─────────────────────────┘    │
│                     │ HTTP/REST                     │
│  ┌──────────────────▼─────────────────────────┐    │
│  │    Backend Service (ClusterIP)              │    │
│  │    ai-assessment-backend                    │    │
│  └──────────────────┬─────────────────────────┘    │
│                     │                               │
│  ┌──────────────────▼─────────────────────────┐    │
│  │    Backend Deployment (2-10 pods)           │    │
│  │    FastAPI + Business Logic                 │    │
│  │    Port: 8000                               │    │
│  └──────────────────┬─────────────────────────┘    │
│                     │                               │
│                     ▼                               │
│              OpenAI API (External)                  │
└─────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Required Tools

- **kubectl** 1.24+ - Kubernetes CLI
- **Helm** 3.8+ - Package manager for Kubernetes
- **Docker** 20.10+ - For building images
- **OpenAI API Key** - For AI evaluation

### Kubernetes Cluster

You need access to a Kubernetes cluster. Options:

- **Local**: Minikube, Kind, Docker Desktop
- **Cloud**: GKE, EKS, AKS
- **Self-hosted**: kubeadm, k3s

---

## Quick Start

### 1. Build and Push Images

```bash
# Build backend
docker build -f Dockerfile.backend -t ghcr.io/bhardwaj-saurabh/ai-assessment-backend:1.0.0 .

# Build frontend
docker build -f Dockerfile.frontend -t ghcr.io/bhardwaj-saurabh/ai-assessment-frontend:1.0.0 .

# Login to registry
echo $GITHUB_TOKEN | docker login ghcr.io -u bhardwaj-saurabh --password-stdin

# Push images
docker push ghcr.io/bhardwaj-saurabh/ai-assessment-backend:1.0.0
docker push ghcr.io/bhardwaj-saurabh/ai-assessment-frontend:1.0.0
```

### 2. Create Namespace

```bash
kubectl create namespace ai-assessment
```

### 3. Deploy with Helm

```bash
helm install ai-assessment ./helm \
  --namespace ai-assessment \
  --set backend.image.repository=ghcr.io/bhardwaj-saurabh/ai-assessment-backend \
  --set backend.image.tag=1.0.0 \
  --set frontend.image.repository=ghcr.io/bhardwaj-saurabh/ai-assessment-frontend \
  --set frontend.image.tag=1.0.0 \
  --set secrets.openaiApiKey=$OPENAI_API_KEY
```

### 4. Verify Deployment

```bash
# Check pods (should see both frontend and backend pods)
kubectl get pods -n ai-assessment

# Check services
kubectl get svc -n ai-assessment

# View logs
kubectl logs -f deployment/ai-assessment-backend -n ai-assessment
kubectl logs -f deployment/ai-assessment-frontend -n ai-assessment
```

### 5. Access Application

```bash
# Port forward frontend
kubectl port-forward svc/ai-assessment-frontend 8501:80 -n ai-assessment

# Open browser
open http://localhost:8501

# Access backend API docs
kubectl port-forward svc/ai-assessment-backend 8000:8000 -n ai-assessment
open http://localhost:8000/docs
```

---

## Helm Chart Structure

The Helm chart deploys two separate services:

```
helm/
├── Chart.yaml                 # Chart metadata
├── values.yaml               # Default configuration (microservices)
├── values-dev.yaml          # Development overrides
├── values-prod.yaml         # Production overrides
└── templates/
    ├── deployment.yaml      # Frontend + Backend Deployments
    ├── service.yaml         # Frontend + Backend Services
    ├── ingress.yaml         # Ingress (routes to frontend)
    ├── secret.yaml          # API keys
    ├── hpa.yaml            # Autoscalers for both services
    ├── serviceaccount.yaml  # Service account
    └── _helpers.tpl         # Template helpers
```

---

## Configuration

### Environment-Specific Values

**Development** (`helm/values-dev.yaml`):
- Backend: 1 replica, reduced resources
- Frontend: 1 replica, NodePort service
- Autoscaling disabled
- Debug enabled

**Production** (`helm/values-prod.yaml`):
- Backend: 5 replicas, higher resources
- Frontend: 3 replicas, LoadBalancer service
- Autoscaling enabled (backend: 3-20, frontend: 2-10)
- Debug disabled

### Key Configuration Values

```yaml
# Backend Configuration
backend:
  replicaCount: 3
  image:
    repository: ghcr.io/bhardwaj-saurabh/ai-assessment-backend
    tag: "1.0.0"
  service:
    type: ClusterIP  # Internal only
    port: 8000
  resources:
    limits:
      cpu: 1500m
      memory: 2Gi
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10

# Frontend Configuration
frontend:
  replicaCount: 2
  image:
    repository: ghcr.io/bhardwaj-saurabh/ai-assessment-frontend
    tag: "1.0.0"
  service:
    type: LoadBalancer  # External access
    port: 80
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 8
  env:
    BACKEND_API_URL: "http://ai-assessment-backend:8000"
```

### Custom Values

Override values during installation:

```bash
helm install ai-assessment ./helm \
  --set backend.replicaCount=5 \
  --set frontend.replicaCount=3 \
  --set backend.resources.limits.memory=4Gi \
  --set frontend.autoscaling.maxReplicas=15
```

---

## Ingress Setup

### Install NGINX Ingress Controller

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install nginx-ingress ingress-nginx/ingress-nginx
```

### Configure DNS

Point your domain to the LoadBalancer IP:

```bash
# Get LoadBalancer IP
kubectl get svc nginx-ingress-controller

# Add DNS A record
# ai-assessment.example.com -> <LoadBalancer-IP>
```

### Enable TLS with cert-manager

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

---

## Monitoring

### View Logs

```bash
# All pods
kubectl logs -l app.kubernetes.io/name=ai-assessment -n ai-assessment

# Specific pod
kubectl logs ai-assessment-<pod-id> -n ai-assessment

# Follow logs
kubectl logs -f deployment/ai-assessment -n ai-assessment
```

### Check Resource Usage

```bash
# Pod metrics
kubectl top pods -n ai-assessment

# Node metrics
kubectl top nodes
```

### Horizontal Pod Autoscaler Status

```bash
kubectl get hpa -n ai-assessment
kubectl describe hpa ai-assessment -n ai-assessment
```

---

## Scaling

### Manual Scaling

```bash
kubectl scale deployment ai-assessment --replicas=5 -n ai-assessment
```

### Autoscaling

HPA is configured by default:
- Min replicas: 2
- Max replicas: 10
- Target CPU: 70%
- Target Memory: 80%

Adjust in `values.yaml`:

```yaml
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 60
```

---

## Updates and Rollbacks

### Update Deployment

```bash
# Update image
helm upgrade ai-assessment ./helm \
  --set image.tag=1.1.0 \
  -n ai-assessment

# Update configuration
helm upgrade ai-assessment ./helm \
  -f helm/values-prod.yaml \
  -n ai-assessment
```

### Rollback

```bash
# View history
helm history ai-assessment -n ai-assessment

# Rollback to previous version
helm rollback ai-assessment -n ai-assessment

# Rollback to specific revision
helm rollback ai-assessment 2 -n ai-assessment
```

### Kubernetes Rollback

```bash
# Rollback deployment
kubectl rollout undo deployment/ai-assessment -n ai-assessment

# Check rollout status
kubectl rollout status deployment/ai-assessment -n ai-assessment
```

---

## Troubleshooting

### Pods Not Starting

```bash
# Describe pod
kubectl describe pod ai-assessment-<pod-id> -n ai-assessment

# Check events
kubectl get events -n ai-assessment --sort-by='.lastTimestamp'
```

### Image Pull Errors

```bash
# Check image pull secrets
kubectl get secrets -n ai-assessment

# Create image pull secret for private registry
kubectl create secret docker-registry regcred \
  --docker-server=ghcr.io \
  --docker-username=<username> \
  --docker-password=<token> \
  -n ai-assessment
```

### Service Not Accessible

```bash
# Check service endpoints
kubectl get endpoints -n ai-assessment

# Test from within cluster
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://ai-assessment.ai-assessment.svc.cluster.local
```

### Health Check Failures

```bash
# Check probe configuration
kubectl describe pod ai-assessment-<pod-id> -n ai-assessment

# Test health endpoint
kubectl exec -it ai-assessment-<pod-id> -n ai-assessment -- \
  curl localhost:8501/_stcore/health
```

---

## Security Best Practices

### 1. Use Secrets Management

**Option A: Kubernetes Secrets** (Basic)
```bash
kubectl create secret generic ai-assessment-secret \
  --from-literal=openai-api-key=$OPENAI_API_KEY
```

**Option B: Sealed Secrets** (Better)
```bash
# Install sealed-secrets controller
helm install sealed-secrets sealed-secrets/sealed-secrets

# Create sealed secret
echo -n $OPENAI_API_KEY | kubectl create secret generic ai-assessment-secret \
  --dry-run=client --from-file=openai-api-key=/dev/stdin -o yaml | \
  kubeseal -o yaml > sealed-secret.yaml

kubectl apply -f sealed-secret.yaml
```

**Option C: HashiCorp Vault** (Best)
- External secrets operator
- Dynamic secret generation
- Audit logging

### 2. Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-assessment-netpol
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: ai-assessment
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8501
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443  # HTTPS for OpenAI API
```

### 3. Pod Security Standards

Already configured in `values.yaml`:
- Non-root user (UID 1000)
- Read-only root filesystem
- Dropped all capabilities
- No privilege escalation

---

## Performance Optimization

### Resource Tuning

Monitor and adjust based on actual usage:

```bash
# Check current usage
kubectl top pods -n ai-assessment

# Update resources
helm upgrade ai-assessment ./helm \
  --set resources.requests.cpu=1000m \
  --set resources.limits.memory=3Gi
```

### Pod Disruption Budget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: ai-assessment-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app.kubernetes.io/name: ai-assessment
```

---

## Cost Optimization

1. **Right-size resources** - Monitor and adjust
2. **Use HPA** - Scale down during low traffic
3. **Spot instances** - For non-critical workloads
4. **Resource quotas** - Prevent over-provisioning

---

## Cleanup

### Uninstall Application

```bash
helm uninstall ai-assessment -n ai-assessment
```

### Delete Namespace

```bash
kubectl delete namespace ai-assessment
```

---

## Next Steps

- [Production Best Practices](production.md)
- [Monitoring Setup](../monitoring.md)
- [CI/CD Integration](../cicd.md)
