# Helm Chart for AI Assessment System

This Helm chart deploys the AI Assessment System with microservices architecture to Kubernetes.

---

## Architecture

The chart deploys two services:

1. **Backend** (FastAPI)
   - ClusterIP service (internal only)
   - 2-10 replicas with autoscaling
   - Handles AI evaluation and business logic

2. **Frontend** (Streamlit)
   - LoadBalancer service (external access)
   - 2-8 replicas with autoscaling
   - User interface

---

## Installation

### Quick Install

```bash
helm install ai-assessment ./helm \
  --namespace ai-assessment \
  --create-namespace \
  --set backend.image.repository=ghcr.io/yourusername/ai-assessment-backend \
  --set frontend.image.repository=ghcr.io/yourusername/ai-assessment-frontend \
  --set secrets.openaiApiKey=$OPENAI_API_KEY
```

### With Custom Values File

```bash
helm install ai-assessment ./helm \
  --namespace ai-assessment \
  -f helm/values-prod.yaml
```

---

## Configuration

### Required Values

- `secrets.openaiApiKey` - OpenAI API key (required)
- `backend.image.repository` - Backend Docker image
- `frontend.image.repository` - Frontend Docker image

### Backend Configuration

```yaml
backend:
  replicaCount: 3
  image:
    repository: ghcr.io/yourusername/ai-assessment-backend
    tag: "1.0.0"
  service:
    type: ClusterIP
    port: 8000
  resources:
    limits:
      cpu: 1500m
      memory: 2Gi
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
```

### Frontend Configuration

```yaml
frontend:
  replicaCount: 2
  image:
    repository: ghcr.io/yourusername/ai-assessment-frontend
    tag: "1.0.0"
  service:
    type: LoadBalancer
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

---

## Upgrading

### Update Image Version

```bash
helm upgrade ai-assessment ./helm \
  --set backend.image.tag=1.1.0 \
  --set frontend.image.tag=1.1.0
```

### Update Configuration

```bash
helm upgrade ai-assessment ./helm \
  -f helm/values-prod.yaml
```

---

## Uninstalling

```bash
helm uninstall ai-assessment --namespace ai-assessment
```

---

## Values Reference

### Global Settings

| Parameter          | Description         | Default |
| ------------------ | ------------------- | ------- |
| `nameOverride`     | Override chart name | `""`    |
| `fullnameOverride` | Override full name  | `""`    |
| `imagePullSecrets` | Image pull secrets  | `[]`    |

### Backend Settings

| Parameter                         | Description                | Default     |
| --------------------------------- | -------------------------- | ----------- |
| `backend.replicaCount`            | Number of backend replicas | `3`         |
| `backend.image.repository`        | Backend image repository   | Required    |
| `backend.image.tag`               | Backend image tag          | `"1.0.0"`   |
| `backend.service.type`            | Service type               | `ClusterIP` |
| `backend.service.port`            | Service port               | `8000`      |
| `backend.autoscaling.enabled`     | Enable autoscaling         | `true`      |
| `backend.autoscaling.minReplicas` | Min replicas               | `2`         |
| `backend.autoscaling.maxReplicas` | Max replicas               | `10`        |

### Frontend Settings

| Parameter                          | Description                 | Default                             |
| ---------------------------------- | --------------------------- | ----------------------------------- |
| `frontend.replicaCount`            | Number of frontend replicas | `2`                                 |
| `frontend.image.repository`        | Frontend image repository   | Required                            |
| `frontend.image.tag`               | Frontend image tag          | `"1.0.0"`                           |
| `frontend.service.type`            | Service type                | `LoadBalancer`                      |
| `frontend.service.port`            | Service port                | `80`                                |
| `frontend.autoscaling.enabled`     | Enable autoscaling          | `true`                              |
| `frontend.autoscaling.minReplicas` | Min replicas                | `2`                                 |
| `frontend.autoscaling.maxReplicas` | Max replicas                | `8`                                 |
| `frontend.env.BACKEND_API_URL`     | Backend URL                 | `http://ai-assessment-backend:8000` |

### Ingress Settings

| Parameter                   | Description    | Default                     |
| --------------------------- | -------------- | --------------------------- |
| `ingress.enabled`           | Enable ingress | `true`                      |
| `ingress.className`         | Ingress class  | `nginx`                     |
| `ingress.hosts[0].host`     | Hostname       | `ai-assessment.example.com` |
| `ingress.tls[0].secretName` | TLS secret     | `ai-assessment-tls`         |

---

## Examples

### Development Deployment

```bash
helm install ai-assessment ./helm \
  --namespace ai-assessment-dev \
  -f helm/values-dev.yaml \
  --set secrets.openaiApiKey=$OPENAI_API_KEY
```

### Production Deployment with Custom Domain

```bash
helm install ai-assessment ./helm \
  --namespace ai-assessment-prod \
  -f helm/values-prod.yaml \
  --set ingress.hosts[0].host=assessment.mycompany.com \
  --set ingress.tls[0].hosts[0]=assessment.mycompany.com \
  --set secrets.openaiApiKey=$OPENAI_API_KEY
```

### High Availability Setup

```bash
helm install ai-assessment ./helm \
  --namespace ai-assessment \
  --set backend.replicaCount=5 \
  --set backend.autoscaling.maxReplicas=20 \
  --set frontend.replicaCount=3 \
  --set frontend.autoscaling.maxReplicas=15 \
  --set secrets.openaiApiKey=$OPENAI_API_KEY
```

---

## Troubleshooting

### Check Helm Release

```bash
helm list -n ai-assessment
helm status ai-assessment -n ai-assessment
```

### View Rendered Templates

```bash
helm template ai-assessment ./helm
```

### Debug Installation

```bash
helm install ai-assessment ./helm --dry-run --debug
```

---

## See Also

- [Kubernetes Deployment Guide](../deployment/kubernetes.md)
- [Docker Deployment Guide](../deployment/docker.md)
- [Production Best Practices](../deployment/production.md)
