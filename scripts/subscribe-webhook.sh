#!/usr/bin/env bash
# Subscribes the Shopify store to stock changes (INVENTORY_LEVELS_UPDATE) so they reach the
# `Low stock alert` workflow in n8n. The subscription lives in Shopify, not in n8n or this repo,
# so this script is how it gets rebuilt (D20, step 1.12). Safe to run again: it only creates
# the subscription when it is missing.
#
# Usage: ./scripts/subscribe-webhook.sh   (reads SHOPIFY_* and N8N_WEBHOOK_URL from .env)
set -euo pipefail
cd "$(dirname "$0")/.."

set -a; . ./.env; set +a

API_VERSION=2026-10
SHOP_URL="https://${SHOPIFY_STORE}.myshopify.com"
# Must match the path of the Webhook node in the `Low stock alert` workflow.
CALLBACK_URL="${N8N_WEBHOOK_URL}webhook/shopify/inventory-levels-update"

# Client credentials token (valid 24 hours). Held in a variable so it never reaches the screen.
TOKEN=$(curl -sS --fail "$SHOP_URL/admin/oauth/access_token" \
  --data-urlencode grant_type=client_credentials \
  --data-urlencode "client_id=$SHOPIFY_CLIENT_ID" \
  --data-urlencode "client_secret=$SHOPIFY_CLIENT_SECRET" | jq -r '.access_token // empty')
if [[ -z $TOKEN ]]; then
  echo "No access token from Shopify. Check SHOPIFY_STORE and the client ID and secret." >&2
  exit 1
fi

# Sends one GraphQL request ($1 query, $2 variables as JSON) and prints the reply.
# Shopify answers HTTP 200 even when a query fails, so a reply with "errors" counts as a failure.
graphql() {
  local response
  response=$(jq -n --arg q "$1" --argjson v "$2" '{query: $q, variables: $v}' |
    curl -sS --fail "$SHOP_URL/admin/api/$API_VERSION/graphql.json" \
      -H "Content-Type: application/json" \
      -H "X-Shopify-Access-Token: $TOKEN" \
      --data-binary @-)
  if jq -e '.errors' <<<"$response" >/dev/null; then
    echo "GraphQL error: $(jq -c '.errors' <<<"$response")" >&2
    return 1
  fi
  echo "$response"
}

# Look for an existing subscription to this topic that points at our URL.
EXISTING=$(graphql '
  query {
    webhookSubscriptions(first: 50, topics: [INVENTORY_LEVELS_UPDATE]) {
      nodes { id uri }
    }
  }' '{}' |
  jq -r --arg url "$CALLBACK_URL" \
    '.data.webhookSubscriptions.nodes[] | select(.uri == $url) | .id' | head -n 1)

if [[ -n $EXISTING ]]; then
  echo "Already subscribed: $EXISTING -> $CALLBACK_URL"
  exit 0
fi

CREATED=$(graphql '
  mutation ($input: WebhookSubscriptionInput!) {
    webhookSubscriptionCreate(topic: INVENTORY_LEVELS_UPDATE, webhookSubscription: $input) {
      webhookSubscription { id uri }
      userErrors { field message }
    }
  }' "$(jq -n --arg url "$CALLBACK_URL" '{input: {uri: $url, format: "JSON"}}')")

# userErrors are Shopify refusing the input (bad URL, missing scope), not a transport failure.
if jq -e '.data.webhookSubscriptionCreate.userErrors | length > 0' <<<"$CREATED" >/dev/null; then
  echo "Shopify refused: $(jq -c '.data.webhookSubscriptionCreate.userErrors' <<<"$CREATED")" >&2
  exit 1
fi

echo "Created: $(jq -r '.data.webhookSubscriptionCreate.webhookSubscription.id' <<<"$CREATED") -> $CALLBACK_URL"
