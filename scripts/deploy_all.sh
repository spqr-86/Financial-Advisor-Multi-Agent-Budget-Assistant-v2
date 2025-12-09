#!/bin/bash
set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Budget Assistant v2.0 Deployment${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Check required environment variables
: "${GCP_PROJECT_ID:?Error: GCP_PROJECT_ID not set}"
: "${TELEGRAM_BOT_TOKEN:?Error: TELEGRAM_BOT_TOKEN not set}"
: "${GOOGLE_API_KEY:?Error: GOOGLE_API_KEY not set}"
: "${WEBHOOK_SECRET:?Error: WEBHOOK_SECRET not set}"
: "${GOOGLE_SHEETS_SPREADSHEET_ID:?Error: GOOGLE_SHEETS_SPREADSHEET_ID not set}"

REGION="${GCP_REGION:-us-central1}"

echo -e "${YELLOW}Using configuration:${NC}"
echo "  Project: ${GCP_PROJECT_ID}"
echo "  Region: ${REGION}"
echo ""

# Check if secrets exist, create if not
echo -e "${YELLOW}Step 0: Checking secrets...${NC}"
if ! gcloud secrets describe service-account-json --project=${GCP_PROJECT_ID} &>/dev/null; then
    echo "Creating secret: service-account-json"
    if [ ! -f "./service-account.json" ]; then
        echo -e "${RED}Error: service-account.json not found!${NC}"
        exit 1
    fi
    gcloud secrets create service-account-json \
        --data-file=./service-account.json \
        --replication-policy=automatic \
        --project=${GCP_PROJECT_ID}
fi

if ! gcloud secrets describe telegram-bot-token --project=${GCP_PROJECT_ID} &>/dev/null; then
    echo "Creating secret: telegram-bot-token"
    echo -n "${TELEGRAM_BOT_TOKEN}" | gcloud secrets create telegram-bot-token \
        --data-file=- \
        --replication-policy=automatic \
        --project=${GCP_PROJECT_ID}
fi

if ! gcloud secrets describe google-api-key --project=${GCP_PROJECT_ID} &>/dev/null; then
    echo "Creating secret: google-api-key"
    echo -n "${GOOGLE_API_KEY}" | gcloud secrets create google-api-key \
        --data-file=- \
        --replication-policy=automatic \
        --project=${GCP_PROJECT_ID}
fi

if ! gcloud secrets describe webhook-secret --project=${GCP_PROJECT_ID} &>/dev/null; then
    echo "Creating secret: webhook-secret"
    echo -n "${WEBHOOK_SECRET}" | gcloud secrets create webhook-secret \
        --data-file=- \
        --replication-policy=automatic \
        --project=${GCP_PROJECT_ID}
fi

echo -e "${GREEN}✓ Secrets configured${NC}"
echo ""

# Step 1: Deploy MCP Service
echo -e "${YELLOW}Step 1: Deploying MCP Service...${NC}"
./scripts/deploy_mcp.sh

# Get MCP service URL
MCP_URL=$(gcloud run services describe budget-mcp \
    --region ${REGION} \
    --platform managed \
    --format 'value(status.url)' \
    --project ${GCP_PROJECT_ID})

echo -e "${GREEN}✓ MCP deployed: ${MCP_URL}${NC}"
echo ""

# Step 2: Deploy API Gateway
echo -e "${YELLOW}Step 2: Deploying API Gateway...${NC}"
export MCP_API_URL="${MCP_URL}"
./scripts/deploy_api.sh

# Get API service URL
API_URL=$(gcloud run services describe budget-api \
    --region ${REGION} \
    --platform managed \
    --format 'value(status.url)' \
    --project ${GCP_PROJECT_ID})

echo -e "${GREEN}✓ API deployed: ${API_URL}${NC}"
echo ""

# Step 3: Deploy Bot
echo -e "${YELLOW}Step 3: Deploying Bot...${NC}"
export BUDGET_API_URL="${API_URL}"
./scripts/deploy_bot.sh

# Get Bot service URL
BOT_URL=$(gcloud run services describe budget-bot \
    --region ${REGION} \
    --platform managed \
    --format 'value(status.url)' \
    --project ${GCP_PROJECT_ID})

echo -e "${GREEN}✓ Bot deployed: ${BOT_URL}${NC}"
echo ""

# Step 4: Set Telegram Webhook
echo -e "${YELLOW}Step 4: Setting Telegram webhook...${NC}"
WEBHOOK_URL="${BOT_URL}/webhook"
WEBHOOK_RESPONSE=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook?url=${WEBHOOK_URL}&secret_token=${WEBHOOK_SECRET}")

if echo "${WEBHOOK_RESPONSE}" | grep -q '"ok":true'; then
    echo -e "${GREEN}✓ Webhook set successfully${NC}"
else
    echo -e "${RED}✗ Webhook setup failed: ${WEBHOOK_RESPONSE}${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Service URLs:"
echo "  MCP:  ${MCP_URL}"
echo "  API:  ${API_URL}"
echo "  Bot:  ${BOT_URL}"
echo ""
echo "Test commands:"
echo "  curl ${MCP_URL}/health"
echo "  curl ${API_URL}/health"
echo "  curl ${BOT_URL}/health"
echo ""
echo "Telegram webhook: ${WEBHOOK_URL}"
echo ""
echo -e "${YELLOW}Next: Test your bot in Telegram!${NC}"
