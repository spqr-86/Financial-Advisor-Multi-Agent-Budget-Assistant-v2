#!/bin/bash
set -e

PROJECT_ID="${GCP_PROJECT_ID:?Error: GCP_PROJECT_ID not set}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="budget-bot"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

: "${BUDGET_API_URL:?Error: BUDGET_API_URL not set. Run deploy_all.sh instead.}"

echo "🤖 Deploying Telegram Bot..."

docker build -f docker/Dockerfile.bot -t ${IMAGE} .
docker push ${IMAGE}

gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --service-account cloud-run-sa@budjet-agent.iam.gserviceaccount.com \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 60 \
    --max-instances 5 \
    --min-instances 0 \
    --concurrency 100 \
    --set-secrets "TELEGRAM_BOT_TOKEN=telegram-bot-token:latest,WEBHOOK_SECRET=webhook-secret:latest" \
    --set-env-vars "BUDGET_API_URL=${BUDGET_API_URL},LOG_LEVEL=INFO,ENVIRONMENT=production" \
    --project ${PROJECT_ID}

SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region ${REGION} --format 'value(status.url)' --project ${PROJECT_ID})

echo "✅ Bot deployed: ${SERVICE_URL}"
echo "   Test: curl ${SERVICE_URL}/health"
