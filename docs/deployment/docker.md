# Docker Deployment Guide

This guide covers deploying the AI Assessment System using Docker and Docker Compose with **microservices architecture**.

---

## Architecture Overview

The application is split into two services:

1. **Backend API** (FastAPI) - Port 8000
   - Business logic and AI evaluation
   - REST API endpoints
   - OpenAI integration

2. **Frontend UI** (Streamlit) - Port 8501
   - User interface
   - Communicates with backend via HTTP

```
┌─────────────┐      HTTP      ┌─────────────┐
│  Frontend   │ ─────────────→ │   Backend   │
│ (Streamlit) │                │  (FastAPI)  │
│  Port 8501  │                │  Port 8000  │
└─────────────┘                └──────┬──────┘
                                      │
                                      ▼
                               ┌─────────────┐
                               │  OpenAI API │
                               └─────────────┘
```

---

## Prerequisites

- Docker 20.10+ installed
- Docker Compose 2.0+ installed
- OpenAI API key

---

## Quick Start

### 1. Set Environment Variables

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
CONFIDENCE_THRESHOLD=0.7
```

### 2. Run with Docker Compose

```bash
docker-compose up -d
```

This starts both services:
- Backend API: http://localhost:8000
- Frontend UI: http://localhost:8501

### 3. Access the Application

**Frontend UI**: Open http://localhost:8501 in your browser

**Backend API Docs**: http://localhost:8000/docs (Swagger UI)

---

## Building Individual Images

### Build Backend

```bash
docker build -f Dockerfile.backend -t ai-assessment-backend:1.0.0 .
```

### Build Frontend

```bash
docker build -f Dockerfile.frontend -t ai-assessment-frontend:1.0.0 .
```

---

## Running Individual Containers

### Run Backend Only

```bash
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-your-key \
  --name ai-assessment-backend \
  ai-assessment-backend:1.0.0
```

### Run Frontend Only

```bash
docker run -d \
  -p 8501:8501 \
  -e BACKEND_API_URL=http://backend:8000 \
  --name ai-assessment-frontend \
  ai-assessment-frontend:1.0.0
```

### Run Both with Docker Network

```bash
# Create network
docker network create ai-assessment-network

# Run backend
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-your-key \
  --network ai-assessment-network \
  --name backend \
  ai-assessment-backend:1.0.0

# Run frontend
docker run -d \
  -p 8501:8501 \
  -e BACKEND_API_URL=http://backend:8000 \
  --network ai-assessment-network \
  --name frontend \
  ai-assessment-frontend:1.0.0
```

---

## Docker Compose

### Start Services

```bash
docker-compose up -d
```

### View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

### Stop Services

```bash
docker-compose down
```

### Rebuild and Restart

```bash
docker-compose up -d --build
```

---

## Service Communication

The frontend communicates with the backend via the `BACKEND_API_URL` environment variable:

- **In Docker Compose**: `http://backend:8000` (service name)
- **In Kubernetes**: `http://ai-assessment-backend:8000` (service name)
- **Local development**: `http://localhost:8000`

---

## Image Optimization

### Check Image Sizes

```bash
docker images | grep ai-assessment
```

Expected sizes:
- Backend: ~500-700 MB
- Frontend: ~400-600 MB

### Multi-Stage Build Benefits

Both Dockerfiles use multi-stage builds to:
- Reduce final image size
- Separate build dependencies from runtime
- Improve security by minimizing attack surface

### Best Practices Applied

1. **Minimal Base Images**: Using `python:3.11-slim`
2. **Layer Caching**: Dependencies installed before code copy
3. **Non-Root User**: Both run as user `appuser` (UID 1000)
4. **Health Checks**: Built-in health monitoring
5. **.dockerignore**: Excludes unnecessary files

---

## Pushing to Registry

### Docker Hub

```bash
# Tag images
docker tag ai-assessment-backend:1.0.0 yourusername/ai-assessment-backend:1.0.0
docker tag ai-assessment-frontend:1.0.0 yourusername/ai-assessment-frontend:1.0.0

# Push
docker push yourusername/ai-assessment-backend:1.0.0
docker push yourusername/ai-assessment-frontend:1.0.0
```

### GitHub Container Registry

```bash
# Login
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Tag
docker tag ai-assessment-backend:1.0.0 ghcr.io/bhardwaj-saurabh/ai-assessment-backend:1.0.0
docker tag ai-assessment-frontend:1.0.0 ghcr.io/bhardwaj-saurabh/ai-assessment-frontend:1.0.0

# Push
docker push ghcr.io/bhardwaj-saurabh/ai-assessment-backend:1.0.0
docker push ghcr.io/bhardwaj-saurabh/ai-assessment-frontend:1.0.0
```

---

## API Endpoints

The backend exposes the following REST API endpoints:

### Document Processing
- `POST /api/v1/upload` - Upload document file
- `POST /api/v1/submit-text` - Submit text directly

### Evaluation
- `POST /api/v1/evaluate` - Start AI evaluation (async)
- `GET /api/v1/workflow/{id}` - Get workflow status

### Human Review
- `POST /api/v1/feedback` - Submit human feedback

### Reports
- `POST /api/v1/generate-report/{id}` - Generate report
- `GET /api/v1/report/{id}/markdown` - Get report as markdown

### System
- `GET /health` - Health check
- `GET /api/v1/workflows` - List all workflows

**API Documentation**: http://localhost:8000/docs (Swagger UI)

---

## Troubleshooting

### Backend Won't Start

Check logs:
```bash
docker logs ai-assessment-backend
```

Common issues:
- Missing `OPENAI_API_KEY`
- Port 8000 already in use

### Frontend Can't Connect to Backend

Check backend URL:
```bash
docker exec ai-assessment-frontend env | grep BACKEND_API_URL
```

Should be `http://backend:8000` in Docker Compose.

### Health Check Failing

Check health status:
```bash
# Backend
docker inspect --format='{{json .State.Health}}' ai-assessment-backend

# Frontend
docker inspect --format='{{json .State.Health}}' ai-assessment-frontend
```

### Network Issues

Verify services are on same network:
```bash
docker network inspect ai-assessment-network
```

### Permission Issues

Ensure volumes have correct permissions:
```bash
chmod -R 755 tests/sample_documents
```

### Out of Memory

Increase Docker memory limit or reduce container resources in `docker-compose.yml`.

---

## Security Considerations

1. **Never commit `.env` file** - Contains sensitive API keys
2. **Use secrets management** - For production, use Docker secrets or external vaults
3. **Scan images** - Use `docker scan` or Trivy
4. **Update base images** - Regularly rebuild with latest base images
5. **Run as non-root** - Already configured in Dockerfile

---

## Next Steps

- [Kubernetes Deployment](kubernetes.md) - Deploy to Kubernetes
- [Production Guide](production.md) - Production best practices
