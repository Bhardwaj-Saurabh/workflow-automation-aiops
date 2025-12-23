# Docker Deployment Guide

This guide covers deploying the AI Assessment System using Docker and Docker Compose.

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

### 3. Access the Application

Open your browser to: `http://localhost:8501`

---

## Building the Docker Image

### Build Locally

```bash
docker build -t ai-assessment:1.0.0 .
```

### Build with Specific Target

```bash
# Production image
docker build --target production -t ai-assessment:prod .
```

---

## Running the Container

### Basic Run

```bash
docker run -d \
  -p 8501:8501 \
  -e OPENAI_API_KEY=sk-your-key \
  --name ai-assessment \
  ai-assessment:1.0.0
```

### With Environment File

```bash
docker run -d \
  -p 8501:8501 \
  --env-file .env \
  --name ai-assessment \
  ai-assessment:1.0.0
```

### With Volume Mounts

```bash
docker run -d \
  -p 8501:8501 \
  -e OPENAI_API_KEY=sk-your-key \
  -v $(pwd)/tests/sample_documents:/app/tests/sample_documents:ro \
  --name ai-assessment \
  ai-assessment:1.0.0
```

---

## Docker Compose

### Start Services

```bash
docker-compose up -d
```

### View Logs

```bash
docker-compose logs -f
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

## Image Optimization

### Check Image Size

```bash
docker images ai-assessment
```

### Multi-Stage Build Benefits

Our Dockerfile uses multi-stage builds to:
- Reduce final image size
- Separate build dependencies from runtime
- Improve security by minimizing attack surface

### Best Practices Applied

1. **Minimal Base Image**: Using `python:3.11-slim`
2. **Layer Caching**: Dependencies installed before code copy
3. **Non-Root User**: Runs as user `appuser` (UID 1000)
4. **Health Checks**: Built-in health monitoring
5. **.dockerignore**: Excludes unnecessary files

---

## Pushing to Registry

### Docker Hub

```bash
# Login
docker login

# Tag
docker tag ai-assessment:1.0.0 yourusername/ai-assessment:1.0.0

# Push
docker push yourusername/ai-assessment:1.0.0
```

### GitHub Container Registry

```bash
# Login
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Tag
docker tag ai-assessment:1.0.0 ghcr.io/bhardwaj-saurabh/ai-assessment:1.0.0

# Push
docker push ghcr.io/bhardwaj-saurabh/ai-assessment:1.0.0
```

---

## Troubleshooting

### Container Won't Start

Check logs:
```bash
docker logs ai-assessment
```

### Health Check Failing

Check health status:
```bash
docker inspect --format='{{json .State.Health}}' ai-assessment
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
