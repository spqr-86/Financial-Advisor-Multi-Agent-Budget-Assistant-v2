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
    --service-account cloud-run-sa@budjet-agent.iam.gserviceaccount.com \
    --port 8082 \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --concurrency 80 \
    --set-secrets "GOOGLE_API_KEY=google-api-key:latest,GOOGLE_APPLICATION_CREDENTIALS=service-account-json:latest" \
    --set-env-vars "GOOGLE_SHEETS_SPREADSHEET_ID=${GOOGLE_SHEETS_SPREADSHEET_ID},GEMINI_MODEL=${GEMINI_MODEL:-gemini-flash-latest},LOG_LEVEL=INFO,ENVIRONMENT=production,MCP_TRANSPORT=both" \
    --project ${PROJECT_ID}

SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region ${REGION} --format 'value(status.url)' --project ${PROJECT_ID})

echo "✅ MCP deployed: ${SERVICE_URL}"
echo "   Test: curl ${SERVICE_URL}/health"
