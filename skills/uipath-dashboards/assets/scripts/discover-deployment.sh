#!/usr/bin/env bash
# Discover systemName / deploymentId for a dashboard that was deployed outside of state.json tracking.
# Used to auto-reconcile when CLI returns `1004 app already deployed in folder`.

set -euo pipefail

usage() {
  echo "Usage: $0 --env <env> --org-id <orgId> --tenant-id <tenantId> --folder <folderKey> --search <appName>"
  exit 1
}

ENV="" ORG_ID="" TENANT_ID="" FOLDER="" SEARCH=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)        ENV="$2"; shift 2 ;;
    --org-id)     ORG_ID="$2"; shift 2 ;;
    --tenant-id)  TENANT_ID="$2"; shift 2 ;;
    --folder)     FOLDER="$2"; shift 2 ;;
    --search)     SEARCH="$2"; shift 2 ;;
    -h|--help)    usage ;;
    *) echo "Unknown: $1"; usage ;;
  esac
done
[[ -z "$ENV" || -z "$ORG_ID" || -z "$TENANT_ID" || -z "$FOLDER" || -z "$SEARCH" ]] && usage

TOKEN=$(jq -r '.accessToken // .access_token // empty' "$HOME/.uipath/.auth.json")
[[ -z "$TOKEN" ]] && { echo "Not logged in" >&2; exit 2; }

HDRS=(
  -H "Authorization: Bearer ${TOKEN}"
  -H "x-uipath-internal-tenantid: ${TENANT_ID}"
  -H "x-uipath-folderkey: ${FOLDER}"
)
BASE="https://${ENV}.uipath.com/${ORG_ID}/apps_/default/api/v1/default/models"

# List deployed apps in folder; find one matching search
DEPLOYED=$(curl -sS "${BASE}/deployed/apps" "${HDRS[@]}")
MATCH=$(echo "$DEPLOYED" | jq -r --arg s "$SEARCH" '.value[] | select(.title==$s or .systemName==$s) | {id, title, systemName, semVersion, deployVersion}' | head -1)

if [[ -z "$MATCH" || "$MATCH" == "null" ]]; then
  echo "NOT_FOUND" >&2
  exit 3
fi

echo "$MATCH"
