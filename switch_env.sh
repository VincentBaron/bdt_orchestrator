#!/bin/bash

# Script to switch webhooks between prod and dev environments
# Uses variables from .env to connect to Flatchr and Jemmo.

set -e

USAGE="Usage: $0 [prod|dev]"

ENV=$1
if [ -z "$ENV" ]; then
  echo "$USAGE"
  exit 1
fi

if [ "$ENV" != "prod" ] && [ "$ENV" != "dev" ]; then
  echo "Error: Invalid environment. Use 'prod' or 'dev'."
  exit 1
fi

echo "Switching to $ENV environment..."

# Load variables from .env
if [ -f .env ]; then
  # Export .env variables to the script environment securely
  set -a
  source .env
  set +a
else
  echo ".env file not found in current directory!"
  exit 1
fi

if [ "$ENV" = "dev" ] && [ -z "$DEV_URL" ]; then
  echo "Error: DEV_URL is not set in your .env file."
  echo "Please add DEV_URL=https://your-localtunnel-url.loca.lt to your .env"
  exit 1
fi

if [ "$ENV" = "prod" ] && [ -z "$PROD_URL" ]; then
  echo "Error: PROD_URL is not set in your .env file."
  echo "Please add PROD_URL=https://bdt-orchestrator.fly.dev to your .env"
  exit 1
fi

BASE_URL=""
if [ "$ENV" = "prod" ]; then
  BASE_URL=$PROD_URL
elif [ "$ENV" = "dev" ]; then
  BASE_URL="${DEV_URL%/}" # Removing trailing slash if any
fi

echo "Base Webhook URL: $BASE_URL"

# Validate required variables
if [ -z "$WEBHOOK_SECRET_PATH" ] || [ -z "$FLATCHR_TOKEN" ] || [ -z "$SOURCING_API_KEY" ] || [ -z "$SOURCING_API_URL" ]; then
  echo "Error: Missing required variables in .env (WEBHOOK_SECRET_PATH, FLATCHR_TOKEN, SOURCING_API_KEY, SOURCING_API_URL)"
  exit 1
fi

# Hardcoded Flatchr company slug based on user request
FLATCHR_COMPANY_SLUG=$FLATCHR_COMPANY_SLUG
FLATCHR_HOOK_STORE=$FLATCHR_HOOK_STORE

echo "------------------------------------------------------"
echo "1. Managing Flatchr Webhook"

# Delete the old Flatchr hook if ID was saved locally
if [ -f "$FLATCHR_HOOK_STORE" ]; then
  OLD_FLATCHR_HOOK_ID=$(cat "$FLATCHR_HOOK_STORE")
  if [ -n "$OLD_FLATCHR_HOOK_ID" ]; then
    echo "Deleting old Flatchr hook: $OLD_FLATCHR_HOOK_ID"
    # We ignore standard error/output and exit code here in case hook is already absent
    curl -s "https://api.flatchr.io/company/$FLATCHR_COMPANY_SLUG/hook/$OLD_FLATCHR_HOOK_ID" \
      -X 'DELETE' \
      -H "authorization: $FLATCHR_SCRIPT_TOKEN" \
      -H 'accept: */*' > /dev/null || true
  fi
fi

FLATCHR_WEBHOOK_URL="$BASE_URL/webhooks/ats/$WEBHOOK_SECRET_PATH/job-created"
echo "Creating new Flatchr hook pointing to: $FLATCHR_WEBHOOK_URL"

FLATCHR_PAYLOAD=$(cat <<EOF
{
  "app_id": 9,
  "url": "$FLATCHR_WEBHOOK_URL",
  "options": {
    "config": {
      "company": "$FLATCHR_WEBHOOK_URL"
    },
    "filters": []
  },
  "event": "new_vacancy"
}
EOF
)

# POST to create the flatchr webhook
FLATCHR_RESPONSE=$(curl -s "https://api.flatchr.io/company/$FLATCHR_COMPANY_SLUG/hook" \
  -H 'accept: */*' \
  -H "authorization: $FLATCHR_SCRIPT_TOKEN" \
  -H 'content-type: application/json' \
  --data-raw "$FLATCHR_PAYLOAD")

# Parse new Flatchr Hook ID using Python
NEW_FLATCHR_HOOK_ID=$(python3 -c "
import sys, json
try:
    print(json.loads(sys.stdin.read()).get('id', ''))
except:
    pass
" <<< "$FLATCHR_RESPONSE")

if [ -n "$NEW_FLATCHR_HOOK_ID" ]; then
  echo "Successfully created new Flatchr hook: $NEW_FLATCHR_HOOK_ID"
  echo "$NEW_FLATCHR_HOOK_ID" > "$FLATCHR_HOOK_STORE"
else
  echo "Failed to create or parse new Flatchr hook. Response:"
  echo "$FLATCHR_RESPONSE"
fi

JEMMO_HOOK_STORE=".jemmo_hook_id.txt"

echo "------------------------------------------------------"
echo "2. Managing Jemmo Webhook"

# Delete the old Jemmo hook if ID was saved locally
if [ -f "$JEMMO_HOOK_STORE" ]; then
  OLD_JEMMO_HOOK_ID=$(cat "$JEMMO_HOOK_STORE")
  if [ -n "$OLD_JEMMO_HOOK_ID" ]; then
    echo "Deleting old Jemmo hook: $OLD_JEMMO_HOOK_ID"
    # We ignore standard error/output and exit code here in case hook is already absent
    curl -s -X DELETE "$SOURCING_API_URL/api/v1/webhooks/$OLD_JEMMO_HOOK_ID" \
      -H "x-api-key: $SOURCING_API_KEY" > /dev/null || true
  fi
fi

JEMMO_WEBHOOK_URL="$BASE_URL/webhooks/sourcing/$WEBHOOK_SECRET_PATH/events"
echo "Creating new Jemmo hook pointing to: $JEMMO_WEBHOOK_URL"

JEMMO_PAYLOAD=$(cat <<EOF
{
  "url": "$JEMMO_WEBHOOK_URL",
  "events": [
    "match.completed"
  ]
}
EOF
)

JEMMO_RESPONSE=$(curl -s "$SOURCING_API_URL/api/v1/webhooks" \
  --request POST \
  --header 'Content-Type: application/json' \
  --header "x-api-key: $SOURCING_API_KEY" \
  --data "$JEMMO_PAYLOAD")

# Parse new Jemmo Hook ID using Python
NEW_JEMMO_HOOK_ID=$(python3 -c "
import sys, json
try:
    print(json.loads(sys.stdin.read()).get('id', ''))
except:
    pass
" <<< "$JEMMO_RESPONSE")

if [ -n "$NEW_JEMMO_HOOK_ID" ]; then
  echo "Successfully created new Jemmo hook: $NEW_JEMMO_HOOK_ID"
  echo "$NEW_JEMMO_HOOK_ID" > "$JEMMO_HOOK_STORE"
else
  echo "Failed to create or parse new Jemmo hook. Response:"
  echo "$JEMMO_RESPONSE"
fi

echo "------------------------------------------------------"
echo "Environment successfully switched to $ENV."
echo "Base Webhook URL used: $BASE_URL"
