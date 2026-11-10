#!/usr/bin/env bash
# Sends compatibility-probe requests to a connection through Integration Service and checks each
# answer the way the LLM Gateway does (file format: references/probes-guide.md). What runs:
#   ../assets/probes/default/    the gateway's own base probe for the flavor: the default, every product
#   ../assets/probes/<product>/  a probe the gateway's code builds for that product, in place of the default
#   ../assets/probes/product-defined/[<product>/]<PROBE_ID>.json, only when named with --probe (opt in):
#                                the probes a product's Model Hub configuration lists for the feature
#
#   bash run-probes.sh --flavor <API_FLAVOR> [--product <PRODUCT>] [--feature <FEATURE>] \
#     [--llm-name <CATALOG_MODEL>] [--probe <PROBE_ID>]... --list
#   bash run-probes.sh --flavor … [--product …] [--feature …] [--llm-name …] [--probe …]... \
#     --model <VENDOR_MODEL_ID> --connection <CONNECTION_ID> --helper <WORK_DIR>/is-api.sh --out <DIR>
#
# --list prints the probes that apply and sends nothing. Otherwise every request is sent with
# the `api` function of the step 6 helper, which holds the token; this script never reads it.
# Exit 0 when every probe passes, 1 when one fails, 2 on a usage error.
set -o pipefail

usage() { sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }

PRODUCT= FEATURE= FLAVOR= LLM_NAME= MODEL= CONNECTION= HELPER= OUT= LIST=
PROBE_IDS=()
while [ $# -gt 0 ]; do
    case "$1" in
        --product) PRODUCT=$2; shift 2 ;;
        --feature) FEATURE=$2; shift 2 ;;
        --flavor) FLAVOR=$2; shift 2 ;;
        --llm-name) LLM_NAME=$2; shift 2 ;;
        --probe) PROBE_IDS+=("$2"); shift 2 ;;
        --model) MODEL=$2; shift 2 ;;
        --connection) CONNECTION=$2; shift 2 ;;
        --helper) HELPER=$2; shift 2 ;;
        --out) OUT=$2; shift 2 ;;
        --list) LIST=1; shift ;;
        *) usage ;;
    esac
done
[ -n "$FLAVOR" ] || usage
[ -n "$LIST" ] || { [ -n "$MODEL" ] && [ -n "$CONNECTION" ] && [ -n "$HELPER" ] && [ -n "$OUT" ] || usage; }
command -v jq >/dev/null || { echo 'run-probes: jq is required.' >&2; exit 2; }
if [ -z "$LIST" ]; then
    [[ "$CONNECTION" =~ ^[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$ ]] || { echo 'run-probes: --connection must be a connection id (a UUID).' >&2; exit 2; }
    [[ "$MODEL" =~ ^[A-Za-z0-9._:@/+-]+$ && "$MODEL" != *..* ]] || { echo 'run-probes: --model holds a character a model id never has.' >&2; exit 2; }
fi

PROBES_DIR="$(cd "$(dirname "$0")/../assets/probes" && pwd)" || exit 2
shopt -s nullglob
FILES=("$PROBES_DIR"/default/*.json)
if [ -n "$PRODUCT" ] && [ "$PRODUCT" != default ] && [ "$PRODUCT" != product-defined ] && [ -d "$PROBES_DIR/$PRODUCT" ]; then
    FILES+=("$PROBES_DIR/$PRODUCT"/*.json)
fi
for id in "${PROBE_IDS[@]}"; do
    found=()
    if [[ "$id" =~ ^[A-Za-z0-9_.-]+$ ]]; then
        for candidate in "$PROBES_DIR"/product-defined/"$id".json "$PROBES_DIR"/product-defined/*/"$id".json; do
            [ -f "$candidate" ] && found+=("$candidate")
        done
    fi
    if [ "${#found[@]}" -ne 1 ]; then
        echo "run-probes: no single product-defined probe '$id'. Known: $(find "$PROBES_DIR/product-defined" -name '*.json' -exec basename {} .json \; | sort | tr '\n' ' ')" >&2
        exit 2
    fi
    FILES+=("${found[0]}")
done

RESULT=$(jq -n --arg flavor "$FLAVOR" --arg feature "$FEATURE" --arg llm "$LLM_NAME" '
    def applies:
        (.match // []) as $m
        | (($m | length) == 0 or any($m[];
              (.feature == null or .feature == $feature) and (.llmName == null or .llmName == $llm)))
          and (((.excludeFeatures // []) | index($feature)) == null);
    [inputs | . + {file: input_filename}] as $all
    | ($all | map(select(.apiFlavor == $flavor and applies))) as $kept
    | ([$kept[].replaces // [] | .[]]) as $gone
    | {selected: ($kept | map(select(.id as $id | ($gone | index($id)) == null)) | sort_by(.order // 50, .file)),
       skipped: [$all[] | select((.file | test("/product-defined/")) and .apiFlavor != $flavor) | "\(.id) (\(.apiFlavor))"]}' \
    "${FILES[@]}") || { echo 'run-probes: a probe file is not valid JSON.' >&2; exit 2; }
SELECTED=$(jq -c '.selected' <<<"$RESULT")
jq -r '.skipped[]' <<<"$RESULT" | tr -d '\r' | while read -r skipped; do
    echo "SKIPPED $skipped: not $FLAVOR, and the gateway runs only a product's probes of the configuration's flavor" >&2
done

COUNT=$(jq 'length' <<<"$SELECTED" | tr -d '\r')
if [ "$COUNT" = 0 ]; then
    echo "No probe applies to ${PRODUCT:-any product} / ${FEATURE:-any feature} / $FLAVOR." >&2
    exit 0
fi

if [ -n "$LIST" ]; then
    jq -r '.[] | "\(.id)\t\(.path)\t\(.file | sub(".*/assets/probes/"; ""))"' <<<"$SELECTED" | tr -d '\r'
    exit 0
fi

mkdir -p "$OUT" || exit 2
# shellcheck disable=SC1090
source "$HELPER" || exit 1

FAILED=0
send() {
    local path=$1 request=$2 response=$3
    api "$T/elements_/v3/element/instances/$CONNECTION$path" --data-binary @"$request" -o "$response" -w '%{http_code}' 2>&1 | tr -d '\r' | tail -n 1
}

for i in $(seq 0 $((COUNT - 1))); do
    PROBE=$(jq -c --argjson i "$i" '.[$i]' <<<"$SELECTED")
    ID=$(jq -r '.id' <<<"$PROBE" | tr -d '\r')
    NAME=$(jq -r '.file | sub(".*/"; "") | sub("\\.json$"; "")' <<<"$PROBE" | tr -d '\r')
    REQUEST="$OUT/$NAME.request.json"
    RESPONSE="$OUT/$NAME.response.json"
    PATH_=$(jq -r --arg m "$MODEL" '.path | gsub("\\{\\{model\\}\\}"; $m)' <<<"$PROBE" | tr -d '\r')
    jq --arg m "$MODEL" '.body | walk(if type == "string" then gsub("\\{\\{model\\}\\}"; $m) else . end)' <<<"$PROBE" >"$REQUEST"

    STATUS=$(send "$PATH_" "$REQUEST" "$RESPONSE")
    RETRY=$(jq -c --arg status "$STATUS" --rawfile body "$RESPONSE" '
        [.retries // [] | .[] | select((.status | tostring) == $status and all(.ifBodyContains[]; . as $s | $body | contains($s)))] | first // empty' <<<"$PROBE" 2>/dev/null)
    if [ -n "$RETRY" ]; then
        jq "$(jq -r '.edit' <<<"$RETRY" | tr -d '\r')" "$REQUEST" >"$REQUEST.retry" && mv "$REQUEST.retry" "$REQUEST"
        echo "RETRY   $ID: HTTP $STATUS, $(jq -r '.why' <<<"$RETRY" | tr -d '\r')"
        STATUS=$(send "$PATH_" "$REQUEST" "$RESPONSE")
    fi

    if ! [[ "$STATUS" =~ ^[0-9]{3}$ ]]; then
        echo "ERROR   $ID: the call did not complete: $STATUS"
        FAILED=1; continue
    fi
    if [[ ! "$STATUS" =~ ^2 ]]; then
        echo "UNAVAILABLE $ID: HTTP $STATUS — $(head -c 300 "$RESPONSE" | tr -d '\r\n')"
        FAILED=1; continue
    fi
    CHECKS=$(jq '.checks // [] | length' <<<"$PROBE" | tr -d '\r')
    if [ "$CHECKS" = 0 ]; then
        echo "PASS    $ID (any 2xx answer passes)"
        continue
    fi
    if ! jq -e . "$RESPONSE" >/dev/null 2>&1; then
        echo "INCOMPATIBLE $ID: MALFORMED_RESPONSE (the answer is not JSON)"
        FAILED=1; continue
    fi
    REASON=
    for j in $(seq 0 $((CHECKS - 1))); do
        CHECK=$(jq -r --argjson j "$j" '.checks[$j].jq' <<<"$PROBE" | tr -d '\r')
        if ! jq -e "$CHECK" "$RESPONSE" >/dev/null 2>&1; then
            REASON=$(jq -r --argjson j "$j" '.checks[$j] | "\(.reason) (\(.says))"' <<<"$PROBE" | tr -d '\r')
            break
        fi
    done
    if [ -n "$REASON" ]; then
        echo "INCOMPATIBLE $ID: $REASON"
        FAILED=1
    else
        echo "PASS    $ID"
    fi
done

echo "Requests and answers: $OUT"
exit "$FAILED"
