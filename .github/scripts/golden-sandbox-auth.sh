#!/usr/bin/env bash
set -euo pipefail

AUTH_FILE="${AUTH_FILE:-$HOME/.uipath/.auth}"
BASE="${TOKEN_KEEPER_DIR:-${RUNNER_TEMP:-${TMPDIR:-/tmp}}}"
STATE="$BASE/token-refresher"
SANDBOX_AUTH_DIR="$BASE/sandbox-auth"
SANDBOX_HOME_DIR="$BASE/sandbox-uipath"
CONTAINER_AUTH=/.uipath-auth/.auth
REFRESH_AUTH_SCRIPT="${REFRESH_AUTH_SCRIPT:-$(dirname "$0")/refresh-auth.sh}"
SANDBOX_FIELDS='^(UIPATH_ACCESS_TOKEN|UIPATH_URL|UIPATH_ORGANIZATION_NAME|UIPATH_ORGANIZATION_ID|UIPATH_TENANT_NAME|UIPATH_TENANT_ID)='

warn() {
    if [ -n "${GITHUB_ACTIONS:-}" ]; then echo "::warning::$1"; else echo "WARN: $1" >&2; fi
}

write_copy() {
    local tmp="$SANDBOX_AUTH_DIR/.auth.tmp"
    (umask 077; grep -E "$SANDBOX_FIELDS" "$AUTH_FILE" > "$tmp") || { rm -f "$tmp"; return 1; }
    if ! grep -q '^UIPATH_ACCESS_TOKEN=.' "$tmp"; then
        rm -f "$tmp"
        return 1
    fi
    chmod 644 "$tmp"
    mv -f "$tmp" "$SANDBOX_AUTH_DIR/.auth"
}

write_sandbox() {
    mkdir -p "$SANDBOX_AUTH_DIR" "$SANDBOX_HOME_DIR"
    chmod 755 "$SANDBOX_AUTH_DIR"
    chmod 777 "$SANDBOX_HOME_DIR"
    ln -sfn "$CONTAINER_AUTH" "$SANDBOX_HOME_DIR/.auth"
    write_copy || { echo "no access token in $AUTH_FILE" >&2; return 1; }
}

record_tokens() {
    (
        umask 077
        sed -n -E 's/^UIPATH_(ACCESS|REFRESH)_TOKEN=//p' "$AUTH_FILE" >> "$STATE/minted"
        sed -n 's/^UIPATH_REFRESH_TOKEN=//p' "$AUTH_FILE" >> "$STATE/refresh"
    )
}

mint() {
    bash "$REFRESH_AUTH_SCRIPT" > /dev/null 2>&1 || return 1
    record_tokens
    write_copy || return 1
    date -u +%H:%M:%S >> "$STATE/refreshed"
}

refresh_loop() {
    local interval="${TOKEN_KEEPER_INTERVAL:-3000}" wait attempt delays
    read -r -a delays <<< "${TOKEN_KEEPER_RETRY_DELAYS:-60 120 240}"
    wait="$interval"
    while sleep "$wait"; do
        wait="$interval"
        attempt=0
        until mint; do
            if [ "$attempt" -ge "${#delays[@]}" ]; then
                date -u +%H:%M:%S >> "$STATE/failed"
                wait="${TOKEN_KEEPER_FAILED_WAIT:-300}"
                break
            fi
            date -u +%H:%M:%S >> "$STATE/retried"
            sleep "${delays[$attempt]}"
            attempt=$((attempt + 1))
        done
    done
}

start() {
    mkdir -p "$STATE"
    chmod 700 "$STATE"
    : > "$STATE/minted"
    : > "$STATE/refresh"
    chmod 600 "$STATE/minted" "$STATE/refresh"
    record_tokens
    write_sandbox
    (umask 077; refresh_loop) > /dev/null 2>&1 < /dev/null &
    echo "$!" > "$STATE/pid"
    if [ -n "${GITHUB_ENV:-}" ]; then
        {
            echo "UIPATH_SANDBOX_HOME_DIR=$SANDBOX_HOME_DIR"
            echo "UIPATH_SANDBOX_AUTH_DIR=$SANDBOX_AUTH_DIR"
        } >> "$GITHUB_ENV"
    fi
    echo "Task containers get a read-only access token, refreshed every $((${TOKEN_KEEPER_INTERVAL:-3000} / 60)) minutes; the refresh token stays on the host."
}

lines() {
    if [ -f "$1" ]; then grep -c . "$1" || true; else echo 0; fi
}

mask_tokens() {
    [ -n "${GITHUB_ACTIONS:-}" ] || return 0
    local token
    while IFS= read -r token; do
        echo "::add-mask::$token"
    done < <(grep -vxE '(null)?' "$STATE/minted" 2> /dev/null | sort -u)
}

revoke() {
    local tokens=() headers=() token endpoint status revoked=0
    while IFS= read -r token; do
        tokens+=("$token")
    done < <(grep -vxE '(null)?' "$STATE/refresh" 2> /dev/null | sort -u)
    [ "${#tokens[@]}" -gt 0 ] || return 0
    if [ -z "${UIPATH_URL:-}" ] || [ -z "${CLIENT_ID:-}" ] || [ -z "${CLIENT_SECRET:-}" ]; then
        warn "no client credentials to revoke the run's ${#tokens[@]} refresh token(s); they stay valid until they expire"
        return 0
    fi
    endpoint="$(curl -sS --max-time 10 "${UIPATH_URL}/identity_/.well-known/openid-configuration" 2> /dev/null \
        | sed -n 's/.*"revocation_endpoint" *: *"\([^"]*\)".*/\1/p' | head -n 1)" || endpoint=""
    if [ -z "$endpoint" ]; then
        warn "found no revocation endpoint; the run's ${#tokens[@]} refresh token(s) stay valid until they expire"
        return 0
    fi
    headers=(-H "Content-Type: application/x-www-form-urlencoded")
    if [ -n "${UIPATH_ORGANIZATION_ID:-}" ]; then
        headers+=(-H "x-uipath-internal-accountid: ${UIPATH_ORGANIZATION_ID}")
    fi
    (umask 077; printf '%s' "$CLIENT_SECRET" > "$STATE/client_secret")
    for token in "${tokens[@]}"; do
        (umask 077; printf '%s' "$token" > "$STATE/token")
        status="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 -X POST "$endpoint" "${headers[@]}" \
            --data-urlencode "token@$STATE/token" \
            --data-urlencode "token_type_hint=refresh_token" \
            --data-urlencode "client_id=${CLIENT_ID}" \
            --data-urlencode "client_secret@$STATE/client_secret" 2> /dev/null)" || status="000"
        if [ "$status" = "200" ]; then
            revoked=$((revoked + 1))
        fi
    done
    rm -f "$STATE/token" "$STATE/client_secret"
    echo "Revoked $revoked of ${#tokens[@]} refresh token(s) the run minted."
    if [ "$revoked" -lt "${#tokens[@]}" ]; then
        warn "$((${#tokens[@]} - revoked)) refresh token(s) the run minted were not revoked; they stay valid until they expire"
    fi
}

stop() {
    if [ ! -f "$STATE/pid" ]; then
        echo "No token refresher ran."
        return 0
    fi
    local pid
    pid="$(cat "$STATE/pid")"
    pkill -P "$pid" 2> /dev/null || true
    kill "$pid" 2> /dev/null || true
    sleep 1
    record_tokens
    mask_tokens
    echo "Bot token refreshed $(lines "$STATE/refreshed") time(s) during the run."
    if [ -s "$STATE/retried" ]; then
        echo "A mint was retried at $(paste -sd ' ' "$STATE/retried") UTC."
    fi
    if [ -s "$STATE/failed" ]; then
        warn "bot token refresh failed at $(paste -sd ' ' "$STATE/failed") UTC after retries; tasks after that may have failed sign-in"
    fi
    revoke || true
    rm -f "$SANDBOX_AUTH_DIR/.auth" "$SANDBOX_AUTH_DIR/.auth.tmp"
    sudo -n chown -R "$(id -u):$(id -g)" "$SANDBOX_HOME_DIR" 2> /dev/null || true
}

case "${1:-}" in
    sandbox)
        write_sandbox
        echo "export UIPATH_SANDBOX_HOME_DIR='$SANDBOX_HOME_DIR'"
        echo "export UIPATH_SANDBOX_AUTH_DIR='$SANDBOX_AUTH_DIR'"
        ;;
    start) start ;;
    stop) stop ;;
    *)
        echo "usage: $0 sandbox|start|stop" >&2
        exit 2
        ;;
esac
