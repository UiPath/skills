#!/usr/bin/env bash
# ROPC token fetch for the coder-eval-bot user. Mints a fresh access token
# via username/password against the UiPath identity server and writes it
# to ~/.uipath/.auth. Each call is fully independent — no refresh-token
# chain to maintain.
#
# Vendored into this repo so run-coder-eval.yml doesn't depend on coder_eval's
# internal script layout (it formerly ran coder_eval/dashboard/scripts/ci/
# refresh-auth.sh, which moved out of coder_eval). Mirrors the VM cron's ROPC
# flow; keep in sync if the upstream token request changes.
#
# Required env (provide via the workflow's `env:` block or `set -a && source`):
#   UIPATH_URL UIPATH_ORGANIZATION_NAME UIPATH_ORGANIZATION_ID
#   UIPATH_TENANT_NAME UIPATH_TENANT_ID
#   CLIENT_ID CLIENT_SECRET CE_USERNAME CE_PASSWORD
set -euo pipefail

: "${UIPATH_URL:=https://alpha.uipath.com}"
: "${UIPATH_ORGANIZATION_ID:?UIPATH_ORGANIZATION_ID not set}"
: "${UIPATH_ORGANIZATION_NAME:?UIPATH_ORGANIZATION_NAME not set}"
: "${UIPATH_TENANT_NAME:?UIPATH_TENANT_NAME not set}"
: "${UIPATH_TENANT_ID:?UIPATH_TENANT_ID not set}"
: "${CLIENT_ID:?CLIENT_ID not set}"
: "${CLIENT_SECRET:?CLIENT_SECRET not set}"
: "${CE_USERNAME:?CE_USERNAME not set}"
: "${CE_PASSWORD:?CE_PASSWORD not set}"

AUTH_FILE="${HOME}/.uipath/.auth"
mkdir -p "$(dirname "$AUTH_FILE")"

SCOPES="openid profile email offline_access Orchestrator OrchestratorApiUserAccess StudioWebBackend StudioWebTypeCacheService ProcessMining ConnectionService ConnectionServiceUser DataService DataServiceApiUserAccess DocumentUnderstanding Du.AiProxy Du.Classification.Api Du.DataDeletion.Api Du.Digitization.Api Du.Extraction.Api Du.Metering Du.Storage.PresignedUrl Du.Training.Service Du.Validation.Api EnterpriseContextService Directory IdentityServerApi JamJamApi LLMGateway LLMOps OMS RCS.FolderAuthorization RCS.TagsManagement Insights Insights.Integrations Insights.RealTimeData Audit.Read AITL.Audit.Export AutomationSolutions AutopilotForEveryone Academy AiFabric ASPortalBackend.Client BusinessUserPortalProxyApi ConversationalAgents CustomerPortal GlobalClientManagement.Internal ManageLicense PIMS PerfService ReferenceToken Reinfer Relay.Service Robot.Local SCP.Jobs.Read SCP.Runtimes SCP.Runtimes.Read SRS.Events SRS.Recommendations TaskMining TestmanagerApiUserAccess TM.Attachments TM.CustomFieldDefinitions TM.CustomFieldValues TM.ObjectLabels TM.PerformanceScenarioExecutions TM.PerformanceScenarios TM.Projects TM.Requirements TM.TestCases TM.TestExecutions TM.TestSets Traces.Api AT.TrackOperations Docs.Service Docs.GPT.Search"

echo "Fetching token for ${CE_USERNAME} against ${UIPATH_URL} (org ${UIPATH_ORGANIZATION_ID})"

response=$(curl -sS -L -X POST "${UIPATH_URL}/identity_/connect/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "x-uipath-internal-accountid: ${UIPATH_ORGANIZATION_ID}" \
    --data-urlencode "grant_type=password" \
    --data-urlencode "client_id=${CLIENT_ID}" \
    --data-urlencode "client_secret=${CLIENT_SECRET}" \
    --data-urlencode "username=${CE_USERNAME}" \
    --data-urlencode "password=${CE_PASSWORD}" \
    --data-urlencode "acr_values=tenant:${UIPATH_ORGANIZATION_ID}" \
    --data-urlencode "scope=${SCOPES}")

if err=$(echo "$response" | jq -e -r '.error // empty') && [ -n "$err" ]; then
    echo "Token request failed: $(echo "$response" | jq -r '.error_description // .error')" >&2
    exit 1
fi

access_token=$(echo "$response" | jq -r '.access_token')
refresh_token=$(echo "$response" | jq -r '.refresh_token')

if [ -z "$access_token" ] || [ "$access_token" = "null" ]; then
    echo "Token response did not contain an access_token" >&2
    exit 1
fi

umask 077
tmp="${AUTH_FILE}.tmp"
cat > "$tmp" <<EOF
UIPATH_ACCESS_TOKEN=${access_token}
UIPATH_REFRESH_TOKEN=${refresh_token}
UIPATH_URL=${UIPATH_URL}
UIPATH_ORGANIZATION_NAME=${UIPATH_ORGANIZATION_NAME}
UIPATH_ORGANIZATION_ID=${UIPATH_ORGANIZATION_ID}
UIPATH_TENANT_NAME=${UIPATH_TENANT_NAME}
UIPATH_TENANT_ID=${UIPATH_TENANT_ID}
EOF
mv -f "$tmp" "$AUTH_FILE"

echo "Done. Token written to $AUTH_FILE"
