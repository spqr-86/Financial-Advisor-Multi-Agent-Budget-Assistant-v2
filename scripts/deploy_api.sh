#!/bin/bash
set -e

PROJECT_ID="${GCP_PROJECT_ID:?Error: GCP_PROJECT_ID not set}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="budget-api"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying API Server..."

docker build -f docker/Dockerfile.api -t ${IMAGE} .
docker push ${IMAGE}

gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8081 \
    --memory 512Mi \
    --set-env-vars "MCP_API_URL=${MCP_API_URL:-}" # Пока пустой

SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region ${REGION} --format 'value(status.url)')

echo "✅ API deployed: ${SERVICE_URL}"
echo "   Test: curl ${SERVICE_URL}/health"
