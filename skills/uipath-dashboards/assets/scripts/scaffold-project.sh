#!/usr/bin/env bash
# scaffold-project.sh — single-shot deterministic scaffold for uipath-dashboards.
#
# Replaces ~30 individual subagent Write calls + ~5 Bash calls with one bash
# invocation. The subagent that runs this saves ~60-90 seconds of LLM
# round-trip latency on first build.
#
# What this script does (everything below is mechanical, no LLM reasoning):
#   1. mkdir project tree at <project-path>
#   2. Render every assets/templates/scaffold/*.template file with {{var}}
#      substitutions.
#   3. Write .env.local with VITE_UIPATH_PAT.
#   4. Write initial .dashboard/state.json.
#   5. Pin the resolved @uipath/uipath-typescript version in package.json.
#   6. npm install.
#   7. Reuse the preflight sdk-manifest.json if SDK version matches.
#   8. shadcn init + add card button badge table chart separator skeleton.
#   9. Restore src/index.css + tailwind.config.ts (shadcn overwrites them).
#  10. Pin tailwindcss@^3.4.13 if shadcn bumped to v4.
#  11. Run sanity checks (UiPath orange HSL present, Poppins link present,
#      chart.tsx produced).
#  12. Emit a JSON summary on stdout.
#
# What this script does NOT do (LLM reasoning required, stays in subagent):
#   - Generate widget files / detail views / query hooks (per-prompt logic).
#   - Compose Dashboard.tsx (per-prompt widget layout).
#   - Run validation gates (tsc / API existence / smoke).
#   - Boot the dev server.
#
# Usage:
#   scaffold-project.sh \
#     --skill-dir <path-to-uipath-dashboards-skill> \
#     --project-path <path> \
#     --cache-dir <path-to-workspace-cache> \
#     --app-name "Agent Health Dashboard" \
#     [--routing-name govdash-agent-health-x7k2] \
#     --org-name <org> \
#     --tenant-name <tenant> \
#     --env <env> \
#     --base-url <url> \
#     --env-infix <infix> \
#     --semver 1.0.0 \
#     [--pat rt_...] \
#     --sdk-version 1.3.2 \
#     --output json
#
# --app-name is the user-friendly Title Case display name shown in the
# dashboard Header AND on the deploy plan ("App name" line).
# --routing-name is the deploy slug (lowercase, hyphens only). If omitted,
# the script derives it via assets/scripts/derive-routing-name.sh as
# `govdash-<kebab-of-app-name>-<4-rand>` (with abbreviations + length cap
# to fit the 32-char server limit). Pass --routing-name explicitly only
# when overriding (e.g., on a routing-name uniqueness collision retry).
# --pat is optional. If omitted, auto-pat.sh mints one via the identity_
# API using the user's `uip login` session (cached in <cache-dir>/pat.json
# for reuse). Pass --pat explicitly only to override (e.g., dev with a
# specific scope-restricted token).
#
# Output: JSON object on stdout with shape:
#   { ready: bool, projectPath, sdkVersion, appName, routingName,
#     templatesRendered, errors[] }

set -euo pipefail

# --- Argument parsing --------------------------------------------------------
SKILL_DIR="" PROJECT_PATH="" CACHE_DIR=""
APP_NAME="" ROUTING_NAME="" ORG_NAME="" TENANT_NAME=""
ENV="" BASE_URL="" ENV_INFIX="" SEMVER=""
PAT="" SDK_VERSION="" OUTPUT="text"

usage() {
  sed -n '/^# Usage:/,/^# Output:/p' "$0" | sed 's/^# \?//'
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill-dir)     SKILL_DIR="$2"; shift 2 ;;
    --project-path)  PROJECT_PATH="$2"; shift 2 ;;
    --cache-dir)     CACHE_DIR="$2"; shift 2 ;;
    --app-name)      APP_NAME="$2"; shift 2 ;;
    --routing-name)  ROUTING_NAME="$2"; shift 2 ;;
    --org-name)      ORG_NAME="$2"; shift 2 ;;
    --tenant-name)   TENANT_NAME="$2"; shift 2 ;;
    --env)           ENV="$2"; shift 2 ;;
    --base-url)      BASE_URL="$2"; shift 2 ;;
    --env-infix)     ENV_INFIX="$2"; shift 2 ;;
    --semver)        SEMVER="$2"; shift 2 ;;
    --pat)           PAT="$2"; shift 2 ;;
    --sdk-version)   SDK_VERSION="$2"; shift 2 ;;
    --output)        OUTPUT="$2"; shift 2 ;;
    -h|--help)       usage ;;
    *) echo "Unknown arg: $1" >&2; usage ;;
  esac
done

for v in SKILL_DIR PROJECT_PATH APP_NAME ORG_NAME TENANT_NAME ENV SEMVER SDK_VERSION; do
  if [[ -z "${!v}" ]]; then
    echo "Missing required arg: $v" >&2
    exit 2
  fi
done

# --- Use uip CLI access token as SDK secret if --pat not supplied ------------
# The user's `uip login` already mints an access token with the scopes the SDK
# needs for read-only dashboard data. Reading it from ~/.uipath/.auth (env-file
# format) and using it as VITE_UIPATH_PAT is simpler, faster, and avoids a
# brittle PAT-mint API path that needed scopes the session token didn't carry.
#
# Read order:
#   1. ~/.uipath/.auth — env-file with shell-style assignments
#      (the canonical token store on current uip CLI builds).
#   2. ~/.uipath/.auth.json — JSON with `access_token` / `accessToken` field
#      (older / alternate uip versions).
# Caller can pass --pat explicitly to override (e.g. to test with a
# scope-restricted PAT).
if [[ -z "$PAT" ]]; then
  AUTH_ENV="${HOME}/.uipath/.auth"
  AUTH_JSON="${HOME}/.uipath/.auth.json"

  # Try env-file shape first.
  if [[ -f "$AUTH_ENV" ]]; then
    # `grep -m1` stops after the first match — avoids the head-closes-pipe
    # SIGPIPE race that `set -o pipefail` would promote to a hard failure on
    # Git Bash + Windows. Same reason we don't pipe to head anywhere else.
    PAT=$(grep -m1 -E '^UIPATH_ACCESS_TOKEN=' "$AUTH_ENV" 2>/dev/null | cut -d= -f2-)
    # Strip surrounding quotes (single or double).
    PAT="${PAT#\"}"; PAT="${PAT%\"}"
    PAT="${PAT#\'}"; PAT="${PAT%\'}"
  fi

  # Fall back to JSON shape.
  if [[ -z "$PAT" && -f "$AUTH_JSON" ]]; then
    # Pass path via env var so node -e doesn't see a Windows-mangled C:\... path.
    PAT=$(AUTH_JSON_PATH="$AUTH_JSON" node -e "
      const fs = require('fs');
      try {
        const a = JSON.parse(fs.readFileSync(process.env.AUTH_JSON_PATH, 'utf8'));
        process.stdout.write(a.access_token || a.accessToken || '');
      } catch (_) {}
    ")
  fi

  if [[ -z "$PAT" ]]; then
    case "$ENV" in
      cloud)         AUTHORITY="https://cloud.uipath.com" ;;
      alpha|staging) AUTHORITY="https://${ENV}.uipath.com" ;;
      *)             AUTHORITY="https://<env>.uipath.com" ;;
    esac
    echo "[scaffold] No access token in $AUTH_ENV or $AUTH_JSON." >&2
    echo "[scaffold] Run 'uip login --authority $AUTHORITY' first, OR pass --pat with a manually-generated PAT." >&2
    exit 3
  fi
  echo "[scaffold] Using access token from uip login session as SDK secret." >&2
fi

# --- Derive BASE_URL if not supplied -----------------------------------------
# Canonical mapping: API subdomain, no portal URL.
#   alpha   → https://alpha.api.uipath.com
#   staging → https://staging.api.uipath.com
#   cloud   → https://api.uipath.com   (no env prefix on prod)
# Caller can override --base-url for non-standard hosts; otherwise we compute.
if [[ -z "$BASE_URL" ]]; then
  case "$ENV" in
    cloud) BASE_URL="https://api.uipath.com" ;;
    alpha|staging) BASE_URL="https://${ENV}.api.uipath.com" ;;
    *)
      echo "Unknown --env '$ENV' (expected alpha/staging/cloud); pass --base-url explicitly to override." >&2
      exit 2
      ;;
  esac
fi

# --- Derive ROUTING_NAME if not supplied -------------------------------------
# Single source of truth: assets/scripts/derive-routing-name.sh. Same logic
# the Plan-phase agent should call so the slug shown in the plan matches the
# slug actually persisted at scaffold-time.
if [[ -z "$ROUTING_NAME" ]]; then
  ROUTING_NAME=$(bash "${SKILL_DIR}/assets/scripts/derive-routing-name.sh" --app-name "$APP_NAME") || {
    echo "[scaffold] derive-routing-name.sh failed for app-name '$APP_NAME'" >&2
    exit 2
  }
fi

# --- Sanity-check APP_NAME shape --------------------------------------------
# If --app-name looks like a deploy slug (lowercase alphanumeric + hyphens
# only, no spaces), warn — this is almost certainly a bug where the calling
# agent passed the routing slug as the app name. The dashboard's Header
# component renders state.app.name as the page title; users want a friendly
# Title Case string, not "agent-health-dashboard".
if [[ "$APP_NAME" =~ ^[a-z0-9-]+$ && "$APP_NAME" == *"-"* ]]; then
  echo "Warning: --app-name '$APP_NAME' looks like a deploy slug, not a friendly title." >&2
  echo "         The dashboard Header will display this verbatim. If you intended a" >&2
  echo "         Title Case display name (e.g. 'Agent Health Dashboard'), pass that" >&2
  echo "         to --app-name and let the script derive the slug." >&2
fi

TEMPLATE_DIR="${SKILL_DIR}/assets/templates/scaffold"
[[ -d "$TEMPLATE_DIR" ]] || { echo "Templates dir not found: $TEMPLATE_DIR" >&2; exit 2; }

# --- Substitution helper -----------------------------------------------------
# Uses `|` as sed separator (URLs contain / and :, never |).
substitute() {
  sed \
    -e "s|{{name}}|${APP_NAME}|g" \
    -e "s|{{orgName}}|${ORG_NAME}|g" \
    -e "s|{{tenantName}}|${TENANT_NAME}|g" \
    -e "s|{{env}}|${ENV}|g" \
    -e "s|{{baseUrl}}|${BASE_URL}|g" \
    -e "s|{{envInfix}}|${ENV_INFIX}|g" \
    -e "s|{{routingName}}|${ROUTING_NAME}|g" \
    -e "s|{{semver}}|${SEMVER}|g"
}

# --- Step 1+2: mkdir project, render templates ------------------------------
mkdir -p "$PROJECT_PATH/.dashboard"

TEMPLATES_RENDERED=0
while IFS= read -r -d '' template; do
  rel="${template#$TEMPLATE_DIR/}"
  rel="${rel%.template}"
  out="$PROJECT_PATH/$rel"
  mkdir -p "$(dirname "$out")"
  substitute < "$template" > "$out"
  TEMPLATES_RENDERED=$((TEMPLATES_RENDERED + 1))
done < <(find "$TEMPLATE_DIR" -name "*.template" -type f -print0)

# --- Step 3: .env.local with PAT (NOT a template — PAT is sensitive) --------
cat > "$PROJECT_PATH/.env.local" <<EOF
VITE_UIPATH_BASE_URL=${BASE_URL}
VITE_UIPATH_ORG_NAME=${ORG_NAME}
VITE_UIPATH_TENANT_NAME=${TENANT_NAME}
VITE_UIPATH_PAT=${PAT}
EOF
chmod 600 "$PROJECT_PATH/.env.local" 2>/dev/null || true

# --- Step 4: initial state.json ---------------------------------------------
cat > "$PROJECT_PATH/.dashboard/state.json" <<EOF
{
  "schemaVersion": 1,
  "env": "${ENV}",
  "orgName": "${ORG_NAME}",
  "tenantName": "${TENANT_NAME}",
  "folderKey": null,
  "app": {
    "name": "${APP_NAME}",
    "routingName": "${ROUTING_NAME}",
    "semver": "${SEMVER}"
  },
  "deployment": {
    "systemName": null,
    "deploymentId": null,
    "deployVersion": null,
    "appUrl": null,
    "deployedAt": null,
    "lastPublishAt": null
  }
}
EOF

# --- Step 5: pin SDK version in package.json --------------------------------
cd "$PROJECT_PATH"
node -e "
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
pkg.dependencies['@uipath/uipath-typescript'] = '${SDK_VERSION}';
fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2) + '\n');
"

# --- Step 6: npm install -----------------------------------------------------
npm install --silent --no-audit --no-fund

# --- Step 7: reuse preflight sdk-manifest.json if version matches -----------
# Pass paths via env vars so node -e doesn't see Windows-mangled C:\... paths
# when the script is run from Git Bash on Windows (interpolating $VAR into a
# JS string literal turns "/c/Users/..." into "C:\Users\..." which then fails
# the readFileSync).
if [[ -n "$CACHE_DIR" && -f "$CACHE_DIR/sdk-manifest.json" ]]; then
  CACHE_VERSION=$(MANIFEST_PATH="$CACHE_DIR/sdk-manifest.json" node -e "
    const fs = require('fs');
    try {
      const m = JSON.parse(fs.readFileSync(process.env.MANIFEST_PATH, 'utf8'));
      process.stdout.write(m.sdkVersion || '');
    } catch (_) {}
  " 2>/dev/null || echo "")
  PROJECT_VERSION=$(SDK_PKG_PATH="$PROJECT_PATH/node_modules/@uipath/uipath-typescript/package.json" node -e "
    const fs = require('fs');
    try {
      const p = JSON.parse(fs.readFileSync(process.env.SDK_PKG_PATH, 'utf8'));
      process.stdout.write(p.version || '');
    } catch (_) {}
  " 2>/dev/null || echo "")
  if [[ -n "$CACHE_VERSION" && "$CACHE_VERSION" == "$PROJECT_VERSION" ]]; then
    mkdir -p "$PROJECT_PATH/.dashboard"
    cp "$CACHE_DIR/sdk-manifest.json" "$PROJECT_PATH/.dashboard/sdk-manifest.json"
  fi
fi

# --- Step 8: shadcn init + add ----------------------------------------------
# Remove components.json so `shadcn init --yes` doesn't hang on the
# overwrite-confirmation prompt (--yes does not suppress that specific prompt).
rm -f components.json
npx shadcn@latest init --yes --defaults > /dev/null 2>&1
npx shadcn@latest add --yes card button badge table chart separator skeleton > /dev/null 2>&1

# --- Step 9: restore index.css + tailwind.config.ts -------------------------
substitute < "$TEMPLATE_DIR/src/index.css.template"          > src/index.css
substitute < "$TEMPLATE_DIR/tailwind.config.ts.template"     > tailwind.config.ts

# --- Step 10: pin tailwind v3 if shadcn bumped to v4 ------------------------
TW_VERSION=$(node -e "console.log(require('./node_modules/tailwindcss/package.json').version)" 2>/dev/null || echo "")
if [[ -n "$TW_VERSION" && ! "$TW_VERSION" =~ ^3\. ]]; then
  npm install --save-dev tailwindcss@^3.4.13 --silent --no-audit --no-fund
fi

# --- Step 11: sanity checks --------------------------------------------------
ERRORS=()
grep -q "14 96% 53%" src/index.css || ERRORS+=("index.css missing UiPath orange HSL (--chart-1: 14 96% 53%)")
grep -q "oklch(" src/index.css     && ERRORS+=("index.css contains shadcn oklch defaults — restore step 9 didn't run")
grep -q "fonts.googleapis.com/css2?family=Poppins" index.html || ERRORS+=("index.html missing Poppins font link")
[[ -f src/components/ui/chart.tsx ]] || ERRORS+=("src/components/ui/chart.tsx missing — shadcn add chart did not produce it")
[[ "${TW_VERSION:0:2}" == "3." ]] || ERRORS+=("tailwindcss is not v3 (got: $TW_VERSION)")

# --- Step 12: emit JSON summary ---------------------------------------------
if [[ "$OUTPUT" == "json" ]]; then
  # Build errors JSON array using node so we don't depend on jq.
  ERRORS_JSON=$(node -e "
    const errs = process.argv.slice(1);
    process.stdout.write(JSON.stringify(errs));
  " "${ERRORS[@]+"${ERRORS[@]}"}")
  READY=$([ ${#ERRORS[@]} -eq 0 ] && echo true || echo false)
  cat <<EOF
{
  "ready": ${READY},
  "projectPath": "${PROJECT_PATH}",
  "appName": "${APP_NAME}",
  "routingName": "${ROUTING_NAME}",
  "sdkVersion": "${SDK_VERSION}",
  "templatesRendered": ${TEMPLATES_RENDERED},
  "tailwindVersion": "${TW_VERSION}",
  "errors": ${ERRORS_JSON}
}
EOF
else
  echo "Project scaffolded at: $PROJECT_PATH"
  echo "App name:              $APP_NAME"
  echo "Routing name:          $ROUTING_NAME"
  echo "Templates rendered:    $TEMPLATES_RENDERED"
  echo "SDK version:           $SDK_VERSION"
  echo "Tailwind version:      $TW_VERSION"
  if [[ ${#ERRORS[@]} -gt 0 ]]; then
    echo "Errors:"
    printf '  - %s\n' "${ERRORS[@]}"
    exit 3
  fi
fi
