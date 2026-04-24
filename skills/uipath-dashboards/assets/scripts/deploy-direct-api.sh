#!/usr/bin/env bash
# Direct-API deploy for UiPath Coded Web Apps.
# Works around the `uip codedapp deploy` hardcoded-`versions/1` bug.
# Uses bash + curl + jq for cross-platform compatibility (Win Git Bash / macOS / Linux).

set -euo pipefail

usage() {
  cat <<EOF
Usage: $0 --env <env> --org <orgName> --org-id <orgId> --tenant <tenantName> --tenant-id <tenantId>
          --folder <folderKey> --version <deployVersion> --title <appTitle> --routing <routingName>
          [--system <systemName>] [--deployment <deploymentId>]

If --deployment is set, PATCH (upgrade). Else if --system is set, POST (fresh). Else fail.
EOF
  exit 1
}

ENV="" ORG="" ORG_ID="" TENANT="" TENANT_ID="" FOLDER="" SYSTEM="" DEPLOYMENT="" VERSION="" TITLE="" ROUTING=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)        ENV="$2"; shift 2 ;;
    --org)        ORG="$2"; shift 2 ;;
    --org-id)     ORG_ID="$2"; shift 2 ;;
    --tenant)     TENANT="$2"; shift 2 ;;
    --tenant-id)  TENANT_ID="$2"; shift 2 ;;
    --folder)     FOLDER="$2"; shift 2 ;;
    --system)     SYSTEM="$2"; shift 2 ;;
    --deployment) DEPLOYMENT="$2"; shift 2 ;;
    --version)    VERSION="$2"; shift 2 ;;
    --title)      TITLE="$2"; shift 2 ;;
    --routing)    ROUTING="$2"; shift 2 ;;
    -h|--help)    usage ;;
    *) echo "Unknown: $1"; usage ;;
  esac
done

[[ -z "$ENV" || -z "$ORG" || -z "$ORG_ID" || -z "$TENANT_ID" || -z "$FOLDER" || -z "$VERSION" || -z "$TITLE" ]] && usage

# Resolve auth token from uip
AUTH_FILE="$HOME/.uipath/.auth.json"
if [[ ! -f "$AUTH_FILE" ]]; then
  echo "No auth file at $AUTH_FILE; run 'uip login' first." >&2
  exit 2
fi
TOKEN=$(jq -r '.accessToken // .access_token // empty' "$AUTH_FILE")
[[ -z "$TOKEN" ]] && { echo "Could not extract access token from $AUTH_FILE" >&2; exit 2; }

BASE="https://${ENV}.uipath.com/${ORG_ID}/apps_/default/api/v1/default/models"
QS="?x-uipath-tenantname=${TENANT}&x-uipath-orgname=${ORG}"
HDRS=(
  -H "Authorization: Bearer ${TOKEN}"
  -H "x-uipath-internal-tenantid: ${TENANT_ID}"
  -H "x-uipath-folderkey: ${FOLDER}"
  -H "Content-Type: application/json"
)

if [[ -n "$DEPLOYMENT" ]]; then
  # Upgrade path
  BODY=$(jq -n --arg t "$TITLE" --argjson v "$VERSION" '{title: $t, version: $v}')
  RESP=$(curl -sS -X PATCH "${BASE}/deployed/apps/${DEPLOYMENT}${QS}" "${HDRS[@]}" -d "$BODY")
  echo "$RESP"
elif [[ -n "$SYSTEM" ]]; then
  # Fresh deploy path
  BODY=$(jq -n --arg t "$TITLE" --arg r "$ROUTING" '{title: $t, routingName: $r}')
  RESP=$(curl -sS -X POST "${BASE}/${SYSTEM}/publish/versions/${VERSION}/deploy${QS}" "${HDRS[@]}" -d "$BODY")
  # Detect 1004 already-deployed
  CODE=$(echo "$RESP" | jq -r '.code // empty')
  if [[ "$CODE" == "1004" ]]; then
    echo "ALREADY_DEPLOYED" >&2
    echo "$RESP"
    exit 3
  fi
  echo "$RESP"
else
  echo "Either --deployment (upgrade) or --system (fresh) required" >&2
  exit 1
fi
