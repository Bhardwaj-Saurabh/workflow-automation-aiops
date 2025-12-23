#!/bin/bash
# Deployment script for AI Assessment System
# Usage: ./deploy.sh [environment] [version]

set -e

# Configuration
ENVIRONMENT=${1:-dev}
VERSION=${2:-1.0.0}
IMAGE_REGISTRY="ghcr.io/bhardwaj-saurabh"
IMAGE_NAME="ai-assessment"
NAMESPACE="ai-assessment"

echo "🚀 Deploying AI Assessment System"
echo "Environment: $ENVIRONMENT"
echo "Version: $VERSION"
echo ""

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl is required but not installed."; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "❌ Helm is required but not installed."; exit 1; }

# Build Docker image
echo "📦 Building Docker image..."
docker build -t ${IMAGE_REGISTRY}/${IMAGE_NAME}:${VERSION} .
docker tag ${IMAGE_REGISTRY}/${IMAGE_NAME}:${VERSION} ${IMAGE_REGISTRY}/${IMAGE_NAME}:latest

# Push to registry
echo "📤 Pushing image to registry..."
docker push ${IMAGE_REGISTRY}/${IMAGE_NAME}:${VERSION}
docker push ${IMAGE_REGISTRY}/${IMAGE_NAME}:latest

# Create namespace if it doesn't exist
echo "📁 Creating namespace..."
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY environment variable not set"
    read -sp "Enter OpenAI API Key: " OPENAI_API_KEY
    echo ""
fi

# Deploy with Helm
echo "⚙️  Deploying with Helm..."
helm upgrade --install ai-assessment ./helm \
    --namespace ${NAMESPACE} \
    --set image.repository=${IMAGE_REGISTRY}/${IMAGE_NAME} \
    --set image.tag=${VERSION} \
    --set secrets.openaiApiKey=${OPENAI_API_KEY} \
    -f helm/values-${ENVIRONMENT}.yaml \
    --wait \
    --timeout 5m

# Check deployment status
echo "✅ Checking deployment status..."
kubectl rollout status deployment/ai-assessment -n ${NAMESPACE}

# Get service information
echo ""
echo "📊 Deployment Information:"
kubectl get pods -n ${NAMESPACE}
kubectl get svc -n ${NAMESPACE}
kubectl get ingress -n ${NAMESPACE}

echo ""
echo "✅ Deployment complete!"
echo ""
echo "To access the application:"
echo "  kubectl port-forward svc/ai-assessment 8501:80 -n ${NAMESPACE}"
echo "  Then open: http://localhost:8501"
