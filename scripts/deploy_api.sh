#!/bin/bash
set -e

PROJECT_ID="${GCP_PROJECT_ID:?Error: GCP_PROJECT_ID not set}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="budget-api"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

: "${MCP_API_URL:?Error: MCP_API_URL not set. Run deploy_all.sh instead.}"

echo "🚀 Deploying API Gateway..."

docker build -f docker/Dockerfile.api -t ${IMAGE} .
docker push ${IMAGE}

gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --service-account cloud-run-sa@budjet-agent.iam.gserviceaccount.com \
    --port 8081 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 60 \
    --max-instances 10 \
    --min-instances 0 \
    --concurrency 100 \
    --set-env-vars "MCP_API_URL=${MCP_API_URL},REQUEST_TIMEOUT=30,LOG_LEVEL=INFO,ENVIRONMENT=production" \
    --project ${PROJECT_ID}

SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region ${REGION} --format 'value(status.url)' --project ${PROJECT_ID})

echo "✅ API deployed: ${SERVICE_URL}"
echo "   Test: curl ${SERVICE_URL}/health"
