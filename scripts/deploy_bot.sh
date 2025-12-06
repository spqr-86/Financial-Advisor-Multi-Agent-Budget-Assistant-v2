#!/bin/bash
set -e

PROJECT_ID="${GCP_PROJECT_ID:?Error: GCP_PROJECT_ID not set}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="budget-bot"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🤖 Deploying Telegram Bot..."

# Build & push
docker build -f docker/Dockerfile.bot -t ${IMAGE} .
docker push ${IMAGE}

# Deploy
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --set-env-vars "TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}"

# Get URL and set webhook
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region ${REGION} --format 'value(status.url)')

curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook?url=${SERVICE_URL}/webhook"

echo "✅ Bot deployed: ${SERVICE_URL}"
