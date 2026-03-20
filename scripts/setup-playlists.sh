#!/usr/bin/env bash
# Setup Grafana playlists via API
# Run after docker compose up: ./scripts/setup-playlists.sh
set -euo pipefail

GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASS="${GRAFANA_PASS:-admin}"

echo "Setting up Grafana playlists..."

# Helper function to create or update playlist
create_playlist() {
  local name="$1"
  local interval="$2"
  shift 2
  local items="$*"

  # Check if playlist exists
  local existing
  existing=$(curl -s -u "$GRAFANA_USER:$GRAFANA_PASS" \
    "$GRAFANA_URL/api/playlists" | jq -r ".[] | select(.name == \"$name\") | .uid")

  local payload
  payload=$(jq -n \
    --arg name "$name" \
    --arg interval "$interval" \
    --argjson items "$items" \
    '{name: $name, interval: $interval, items: $items}')

  if [[ -n "$existing" ]]; then
    echo "  Updating: $name"
    curl -s -X PUT -u "$GRAFANA_USER:$GRAFANA_PASS" \
      -H "Content-Type: application/json" \
      -d "$payload" \
      "$GRAFANA_URL/api/playlists/$existing" > /dev/null
  else
    echo "  Creating: $name"
    curl -s -X POST -u "$GRAFANA_USER:$GRAFANA_PASS" \
      -H "Content-Type: application/json" \
      -d "$payload" \
      "$GRAFANA_URL/api/playlists" > /dev/null
  fi
}

# DevOS Overview - Quick situational awareness (30s per dashboard)
create_playlist "DevOS Overview" "30s" '[
  {"type": "dashboard_by_uid", "value": "devos-mission-control"},
  {"type": "dashboard_by_uid", "value": "devos-sessions"},
  {"type": "dashboard_by_uid", "value": "devos-friction"},
  {"type": "dashboard_by_uid", "value": "devos-quality"},
  {"type": "dashboard_by_uid", "value": "devos-hooks"}
]'

# DevOS Deep Dive - Longer analysis (60s per dashboard)
create_playlist "DevOS Deep Dive" "60s" '[
  {"type": "dashboard_by_uid", "value": "devos-mission-control"},
  {"type": "dashboard_by_uid", "value": "devos-friction"},
  {"type": "dashboard_by_uid", "value": "devos-quality"},
  {"type": "dashboard_by_uid", "value": "devos-cues"},
  {"type": "dashboard_by_uid", "value": "devos-project-focus"},
  {"type": "dashboard_by_uid", "value": "devos-time-effort"},
  {"type": "dashboard_by_uid", "value": "devos-weekly"}
]'

# DevOS Weekly Review - All dashboards (45s per dashboard)
create_playlist "DevOS Weekly Review" "45s" '[
  {"type": "dashboard_by_uid", "value": "devos-mission-control"},
  {"type": "dashboard_by_uid", "value": "devos-sessions"},
  {"type": "dashboard_by_uid", "value": "devos-friction"},
  {"type": "dashboard_by_uid", "value": "devos-quality"},
  {"type": "dashboard_by_uid", "value": "devos-hooks"},
  {"type": "dashboard_by_uid", "value": "devos-cues"},
  {"type": "dashboard_by_uid", "value": "devos-project-focus"},
  {"type": "dashboard_by_uid", "value": "devos-collaboration"},
  {"type": "dashboard_by_uid", "value": "devos-time-effort"},
  {"type": "dashboard_by_uid", "value": "devos-weekly"}
]'

echo ""
echo "Done! Playlists available at:"
echo "  - $GRAFANA_URL/playlists"
echo ""
echo "Kiosk mode URLs:"
curl -s -u "$GRAFANA_USER:$GRAFANA_PASS" "$GRAFANA_URL/api/playlists" | \
  jq -r '.[] | "  - \(.name): '"$GRAFANA_URL"'/playlists/play/\(.uid)?kiosk"'
