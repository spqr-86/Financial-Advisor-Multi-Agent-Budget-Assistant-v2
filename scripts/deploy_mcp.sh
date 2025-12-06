#!/bin/bash
set -e

PROJECT_ID="${GCP_PROJECT_ID:?Error: GCP_PROJECT_ID not set}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="budget-mcp"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🧠 Deploying MCP Service..."

docker build -f docker/Dockerfile.mcp -t ${IMAGE} .
docker push ${IMAGE}

gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8082 \
    --memory 1Gi \
    --timeout 300 \
    --set-env-vars "GOOGLE_API_KEY=${GOOGLE_API_KEY:-},SPREADSHEET_NAME=${SPREADSHEET_NAME:-Бюджет}"

SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region ${REGION} --format 'value(status.url)')

echo "✅ MCP deployed: ${SERVICE_URL}"
echo "   Test: curl ${SERVICE_URL}/health"
