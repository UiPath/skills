#!/usr/bin/env bash
# Rotate the run's UiPath login with the record-before-handout rule: mint into a
# staging file, append the new tokens to the host-side issued-tokens list, verify
# every one is recorded, and only then install the file graders read
# (~/.uipath/.auth). If recording fails the new login is never handed out (the old
# one stays) and $RUNNER_TEMP/publication-disabled is written; the artifact scrub
# then refuses to publish this run. ROTATE_QUIET=1 silences all output (the
# background refresher: nothing it prints could be masked anyway).
# Env: refresh-auth.sh's inputs, plus RUNNER_TEMP.
set -uo pipefail
: "${RUNNER_TEMP:?RUNNER_TEMP not set}"
if [ -n "${ROTATE_QUIET:-}" ]; then exec >/dev/null 2>&1; fi
umask 077
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
staging="$RUNNER_TEMP/auth.next"
record="$RUNNER_TEMP/issued-tokens"

disable() {
  rm -f "$staging"
  : > "$RUNNER_TEMP/publication-disabled"
  echo "::error::auth rotation could not be recorded; publication disabled for this run"
  exit 1
}

rm -f "$staging"
if ! AUTH_FILE="$staging" bash "$here/refresh-auth.sh"; then
  rm -f "$staging"
  exit 1
fi
tokens="$(grep -E '^UIPATH_(ACCESS|REFRESH)_TOKEN=' "$staging" | cut -d= -f2- | awk 'length > 28')"
if ! printf '%s\n' "$tokens" | grep -q .; then
  rm -f "$staging"
  echo "::error::minted login holds no token"
  exit 1
fi
printf '%s\n' "$tokens" >> "$record" || disable
while IFS= read -r token; do
  [ -z "$token" ] || grep -qxF -- "$token" "$record" || disable
done <<< "$tokens"

mkdir -p "$HOME/.uipath"
chmod o+r "$staging" || true  # readable by container root the instant it is installed
mv -f "$staging" "$HOME/.uipath/.auth" || { rm -f "$staging"; exit 1; }
# coder-eval 0.11+ drops DAC_OVERRIDE/DAC_READ_SEARCH from task containers, so
# container-root cannot read the host-owned ~/.uipath mount by capability; widen
# it via the "other" bits (mirrors coder-eval's own grant_container_access).
chmod -R o+rwX "$HOME/.uipath" || true  # root-owned files from a container must not fail an installed rotation
