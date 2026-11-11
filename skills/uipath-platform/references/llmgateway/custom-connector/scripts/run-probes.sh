#!/usr/bin/env bash
# Sends compatibility-probe requests to a connection through Integration Service and checks each
# answer the way the LLM Gateway does (file format: references/probes-guide.md). What runs:
#   ../assets/probes/default/    every product's probes: the gateway's base probe for the flavor, and
#                                the basic probes any product's configuration can list
#   ../assets/probes/<product>/  that product's own: a probe the gateway's code builds for it, in place
#                                of the base probe, and the probes only that product lists
# A file marked "optIn": true runs only when named with --probe <PROBE_ID>, because the feature's Model
# Hub configuration lists it; a ProbeId is unique, so it is found in any folder.
#
#   bash run-probes.sh --flavor <API_FLAVOR> [--product <PRODUCT>] [--feature <FEATURE>] \
#     [--llm-name <CATALOG_MODEL>] [--probe <PROBE_ID>]... --list
#   bash run-probes.sh --flavor … [--product …] [--feature …] [--llm-name …] [--probe …]... \
#     --model <VENDOR_MODEL_ID> --connection <CONNECTION_ID> --helper <WORK_DIR>/is-api.sh --out <DIR>
#
# --list prints the probes that apply and sends nothing. Otherwise every request is sent with
# the `api` function of the step 6 helper, which holds the token; this script never reads it.
# A probe marked "roundTrip": true is two streamed calls with values drawn for the run (see below).
# Exit 0 when every probe passes, 1 when one fails, 2 when none was sent (a usage error, an
# unknown flavor, or no probe for that product, feature and flavor; --list exits 0 then).
set -o pipefail

usage() { sed -n '2,/^[^#]/p' "$0" | sed '$d; s/^# \{0,1\}//' >&2; exit 2; }

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
KNOWN_FLAVORS=$(jq -r '.apiFlavor' "$PROBES_DIR"/*/*.json | tr -d '\r' | sort -u)
grep -qxF -- "$FLAVOR" <<<"$KNOWN_FLAVORS" || {
    echo "run-probes: no probe has the flavor '$FLAVOR'. Known: $(tr '\n' ' ' <<<"$KNOWN_FLAVORS")" >&2
    exit 2
}
FILES=("$PROBES_DIR"/default/*.json)
if [[ "$PRODUCT" =~ ^[A-Za-z0-9_-]+$ ]] && [ "$PRODUCT" != default ] && [ -d "$PROBES_DIR/$PRODUCT" ]; then
    FILES+=("$PROBES_DIR/$PRODUCT"/*.json)
fi
for id in "${PROBE_IDS[@]}"; do
    found=()
    if [[ "$id" =~ ^[A-Za-z0-9_.-]+$ ]]; then
        for candidate in "$PROBES_DIR"/*/"$id".json; do
            jq -e '.optIn == true' "$candidate" >/dev/null 2>&1 && found+=("$candidate")
        done
    fi
    if [ "${#found[@]}" -ne 1 ]; then
        echo "run-probes: no single probe a product lists with the id '$id'. Known: $(jq -r 'select(.optIn == true) | .id' "$PROBES_DIR"/*/*.json | tr -d '\r' | sort | tr '\n' ' ')" >&2
        exit 2
    fi
    FILES+=("${found[0]}")
done
NAMED=$(jq -nc '$ARGS.positional' --args "${PROBE_IDS[@]}")

RESULT=$(jq -n --arg flavor "$FLAVOR" --arg feature "$FEATURE" --arg llm "$LLM_NAME" --argjson named "$NAMED" '
    def applies:
        (.match // []) as $m
        | (($m | length) == 0 or any($m[];
              (.feature == null or .feature == $feature) and (.llmName == null or .llmName == $llm)))
          and (((.excludeFeatures // []) | index($feature)) == null);
    def wanted: .optIn != true or (.id | IN($named[]));
    [inputs | . + {file: input_filename}] | unique_by(.file) as $all
    | ($all | map(select(.apiFlavor == $flavor and applies and wanted))) as $kept
    | ([$kept[].replaces // [] | .[]]) as $gone
    | {selected: ($kept | map(select(.id as $id | ($gone | index($id)) == null)) | sort_by(.order // 50, .file)),
       skipped: [$all[] | select(.optIn == true and (.id | IN($named[])) and .apiFlavor != $flavor) | "\(.id) (\(.apiFlavor))"]}' \
    "${FILES[@]}") || { echo 'run-probes: a probe file is not valid JSON.' >&2; exit 2; }
SELECTED=$(jq -c '.selected' <<<"$RESULT")
jq -r '.skipped[]' <<<"$RESULT" | tr -d '\r' | while read -r skipped; do
    echo "SKIPPED $skipped: not $FLAVOR, and the gateway runs only a product's probes of the configuration's flavor" >&2
done

COUNT=$(jq 'length' <<<"$SELECTED" | tr -d '\r')
if [ "$COUNT" = 0 ]; then
    echo "No probe applies to ${PRODUCT:-any product} / ${FEATURE:-any feature} / $FLAVOR." >&2
    # Nothing was tested: only a listing may call that a success.
    [ -n "$LIST" ] && exit 0
    exit 2
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

# --- Round-trip probes ("roundTrip": true) -------------------------------------------------------
# Two streamed calls with values drawn fresh for the run, as the gateway's
# AutopilotStreamRoundTripProbeValidator makes them: turn 1 must stream tool calls that carry the
# run's ids; turn 2 sends those calls back with their results and must stream an answer that quotes
# the codes only the results hold. Each turn's request and raw stream are kept in --out.
token() {
    local alphabet=ABCDEFGHJKMNPQRSTUVWXYZ23456789 out= n
    for ((n = 0; n < $1; n++)); do out+=${alphabet:RANDOM % ${#alphabet}:1}; done
    printf '%s' "$out"
}

send_stream() {
    local path=$1 request=$2 raw=$3
    api -N "$T/elements_/v3/element/instances/$CONNECTION$path" -H 'Accept: text/event-stream' \
        --data-binary @"$request" -o "$raw" -w '%{http_code}' 2>&1 | tr -d '\r' | tail -n 1
}

# The stream's events as one JSON array: Bedrock's event-stream frames, server-sent events, or a
# plain JSON body. A line that is not an event (Integration Service adds one on a draft) is dropped.
stream_events() {
    local flavor=$1 raw=$2
    if [ "$flavor" = AwsBedrockInvoke ] && grep -aq '"bytes":"' "$raw"; then
        grep -ao '"bytes":"[A-Za-z0-9+/=]*"' "$raw" | sed 's/^"bytes":"//; s/"$//' |
            while read -r frame; do printf '%s' "$frame" | base64 -d; echo; done | jq -s .
    elif grep -aq '^data:' "$raw"; then
        tr -d '\r' <"$raw" |
            jq -R 'select(startswith("data:")) | sub("^data: ?"; "") | select(. != "" and . != "[DONE]") | fromjson' | jq -s .
    else
        tr -d '\r' <"$raw" | jq -s 'if length == 1 and (.[0] | type) == "array" then .[0] else . end'
    fi
}

# Events -> {text, calls: [{id, name, arguments, thoughtSignature?}], thinking?} or {error: true}.
RT_READ=$(cat <<'JQ'
def idjoin: reduce .[] as $piece (""; if $piece == . then . else . + $piece end);
def pieces(f): [.[] | f | strings];
if $flavor == "OpenAiChatCompletions" then
    if any(.[]; .error != null) then {error: true} else
        [.[] | .choices[]? | select((.index // 0) == 0) | .delta // {}] as $deltas
        | [$deltas[] | .tool_calls[]?] as $fragments
        | if any($fragments[]; .index == null) then error("a tool-call delta has no index") else
            {text: ($deltas | pieces(.content) | join("")),
             calls: ($fragments | group_by(.index) | map({
                 id: (pieces(.id) | if length == 0 then null else idjoin end),
                 name: (pieces(.function.name) | if length == 0 then null else join("") end),
                 arguments: (pieces(.function.arguments) | join(""))}))}
          end
    end
elif $flavor == "OpenAiResponses" then
    if any(.[]; .type == "response.failed" or .type == "error") then {error: true} else
        {text: ([.[] | select(.type == "response.output_text.delta")] | pieces(.delta) | join("")),
         calls: [.[] | select(.type == "response.output_item.done" and .item.type == "function_call") | .item
                 | {id: .call_id, name, arguments: (.arguments // "")}]}
    end
elif $flavor == "GeminiGenerateContent" then
    if any(.[]; .error != null) then {error: true} else
        [.[] | .candidates[0].content.parts[]?] as $parts
        | {text: ([$parts[] | select(.functionCall == null and .thought != true)] | pieces(.text) | join("")),
           calls: [$parts[] | select(.functionCall != null)
                   | {id: .functionCall.id, name: .functionCall.name, arguments: ((.functionCall.args // {}) | tojson), thoughtSignature}]}
    end
else
    if any(.[]; .type == "error") then {error: true} else
        . as $events
        | def deltas($index; $kind; f): [$events[] | select(.type == "content_block_delta" and .index == $index and .delta.type == $kind)] | pieces(.delta | f) | join("");
          def starts(kinds): [$events[] | select(.type == "content_block_start" and (.content_block.type | IN(kinds)))] | sort_by(.index);
        {text: ([$events[] | if .type == "content_block_start" and .content_block.type == "text" then .content_block.text
                             elif .type == "content_block_delta" and .delta.type == "text_delta" then .delta.text else empty end | strings] | join("")),
         calls: (starts("tool_use") | map({id: .content_block.id, name: .content_block.name, arguments: deltas(.index; "input_json_delta"; .partial_json)})),
         thinking: (starts("thinking", "redacted_thinking") | map(.content_block as $block
             | deltas(.index; "thinking_delta"; .thinking) as $thinking | deltas(.index; "signature_delta"; .signature) as $signature
             | $block
               + (if ($thinking | length) > 0 or ($block | has("thinking")) then {thinking: (($block.thinking // "") + $thinking)} else {} end)
               + (if ($signature | length) > 0 or ($block | has("signature")) then {signature: (($block.signature // "") + $signature)} else {} end)))}
    end
end
JQ
)

# Turn 1's verdict: "" when its tool calls are this run's, else the gateway's reason.
RT_CALLS=$(cat <<'JQ'
def argument($name): (.arguments | if length == 0 then null else (try fromjson catch null) end)
    | if type == "object" then .[$name] else null end | if type == "string" then . else null end;
{lookup_order: ["order_id", $order], lookup_customer: ["customer_id", $customer]} as $offered
| .calls as $calls
| if ($calls | length) == 0 then "MISSING_TOOL_CALL (the model answered without a tool call)"
  elif any($calls[]; (.name // "") == "" or ($ids and (.id // "") == "")) then "INCORRECT_TOOL_CALL (a streamed tool call has no name or no id)"
  elif any($calls[]; $offered[.name] == null) then "INCORRECT_TOOL_CALL (the model called a tool the probe did not offer)"
  elif any($calls[]; . as $call | $offered[$call.name] as $want | ($call | argument($want[0])) != $want[1]) then "INCORRECT_TOOL_CALL (a call does not carry this run's id exactly as the prompt gives it)"
  elif $ids and (($calls | map(.id) | unique | length) < ($calls | length)) then "INCORRECT_TOOL_CALL (two streamed tool calls share one id)"
  else "" end
JQ
)

# Turn 2's request: turn 1's, plus the assistant's calls and their results in the flavor's own form.
RT_APPEND=$(cat <<'JQ'
def result($name): if $name == "lookup_order" then {order_id: $order, status_code: $status}
    elif $name == "lookup_customer" then {customer_id: $customer, tier_code: $tier}
    else {error: "Unknown tool"} end;
def input: (.arguments | if length == 0 then {} else (try fromjson catch {}) end) | if type == "object" then . else {} end;
$turn[0] as $first | $first.calls as $calls
| if $flavor == "OpenAiChatCompletions" then
    .messages += [{role: "assistant", content: null, tool_calls: [$calls[] | {id, type: "function", function: {name, arguments}}]}]
               + [$calls[] | {role: "tool", tool_call_id: .id, content: (result(.name) | tojson)}]
  elif $flavor == "OpenAiResponses" then
    .input += [$calls[] | {type: "function_call", call_id: .id, name, arguments}]
            + [$calls[] | {type: "function_call_output", call_id: .id, output: (result(.name) | tojson)}]
  elif $flavor == "GeminiGenerateContent" then
    .contents += [{role: "model", parts: [$calls[] | {functionCall: ({name, args: input} + (if .id != null then {id} else {} end))}
                                                     + (if .thoughtSignature != null then {thoughtSignature} else {} end)]},
                  {role: "user", parts: [$calls[] | {functionResponse: ({name, response: result(.name)} + (if .id != null then {id} else {} end))}]}]
  else
    .messages += [{role: "assistant", content: (($first.thinking // []) + [$calls[] | {type: "tool_use", id, name, input: input}])},
                  {role: "user", content: [$calls[] | {type: "tool_result", tool_use_id: .id, content: (result(.name) | tojson)}]}]
  end
JQ
)

# Turn 2's verdict: "" when the answer quotes the code of every call turn 1 made.
RT_ANSWER=$(cat <<'JQ'
if ((.text // "") | test("^\\s*$")) then
    (if (.calls | length) > 0 then "the model answered the tool results with another tool call" else "the answer to the tool results is empty" end)
else
    (.text | ascii_downcase) as $text
    | [$turn[0].calls[] | if .name == "lookup_order" then $status elif .name == "lookup_customer" then $tier else empty end] | unique
    | map(select(. as $code | $text | contains($code | ascii_downcase) | not))
    | if length == 0 then "" else "the answer does not quote \(join(" and ")) from the tool results" end
end
JQ
)

roundtrip() {
    local id=$1 name=$2 path=$3 flavor=$4 template=$5
    local order customer status tier ids=true n request raw read http problem
    order="ORD-$(token 8)" customer="CUS-$(token 8)" status="ST-$(token 6)" tier="TR-$(token 6)"
    [ "$flavor" = GeminiGenerateContent ] && ids=false
    local values=(--arg flavor "$flavor" --arg order "$order" --arg customer "$customer" --arg status "$status" --arg tier "$tier")
    for n in 1 2; do
        request="$OUT/$name.turn$n.request.json" raw="$OUT/$name.turn$n.stream.txt" read="$OUT/$name.turn$n.read.json"
        if [ "$n" = 1 ]; then
            jq "${values[@]}" 'walk(if type == "string" then gsub("\\{\\{order_id\\}\\}"; $order) | gsub("\\{\\{customer_id\\}\\}"; $customer) else . end)' "$template" >"$request"
        else
            jq "${values[@]}" --slurpfile turn "$OUT/$name.turn1.read.json" "$RT_APPEND" "$OUT/$name.turn1.request.json" >"$request"
        fi
        http=$(send_stream "$path" "$request" "$raw")
        if [ "$http" = 400 ] && grep -aqF "Use 'max_completion_tokens' instead" "$raw" && jq -e 'has("max_tokens")' "$request" >/dev/null 2>&1; then
            jq 'with_entries(if .key == "max_tokens" then .key = "max_completion_tokens" else . end)' "$request" >"$request.retry" && mv "$request.retry" "$request"
            echo "RETRY   $id: HTTP 400, the model wants max_completion_tokens; the gateway sends the turn once more with that field"
            http=$(send_stream "$path" "$request" "$raw")
        fi
        if ! [[ "$http" =~ ^[0-9]{3}$ ]]; then
            echo "ERROR   $id: turn $n did not complete: $http"; return 1
        fi
        if [[ ! "$http" =~ ^2 ]]; then
            echo "UNAVAILABLE $id: turn $n, HTTP $http — $(head -c 300 "$raw" | tr -d '\r\n')"; return 1
        fi
        if ! stream_events "$flavor" "$raw" 2>/dev/null | jq -c --arg flavor "$flavor" "$RT_READ" >"$read" 2>/dev/null || ! [ -s "$read" ]; then
            echo "INCOMPATIBLE $id: MALFORMED_RESPONSE (turn $n's stream is not the flavor's event stream)"; return 1
        fi
        if jq -e '.error == true' "$read" >/dev/null 2>&1; then
            echo "INCOMPATIBLE $id: INCORRECT_RESPONSE (turn $n's stream carries an error event)"; return 1
        fi
        if [ "$n" = 1 ]; then
            problem=$(jq -r "${values[@]}" --argjson ids "$ids" "$RT_CALLS" "$read" | tr -d '\r')
            [ -z "$problem" ] || { echo "INCOMPATIBLE $id: $problem"; return 1; }
        else
            problem=$(jq -r "${values[@]}" --slurpfile turn "$OUT/$name.turn1.read.json" "$RT_ANSWER" "$read" | tr -d '\r')
            [ -z "$problem" ] || { echo "INCOMPATIBLE $id: TOOL_RESULT_IGNORED ($problem)"; return 1; }
        fi
    done
    echo "PASS    $id (round trip: $(jq '.calls | length' "$OUT/$name.turn1.read.json" | tr -d '\r') streamed tool call(s), results quoted)"
}

for i in $(seq 0 $((COUNT - 1))); do
    PROBE=$(jq -c --argjson i "$i" '.[$i]' <<<"$SELECTED")
    ID=$(jq -r '.id' <<<"$PROBE" | tr -d '\r')
    NAME=$(jq -r '.file | sub(".*/"; "") | sub("\\.json$"; "")' <<<"$PROBE" | tr -d '\r')
    REQUEST="$OUT/$NAME.request.json"
    RESPONSE="$OUT/$NAME.response.json"
    PATH_=$(jq -r --arg m "$MODEL" '.path | gsub("\\{\\{model\\}\\}"; $m)' <<<"$PROBE" | tr -d '\r')
    jq --arg m "$MODEL" '.body | walk(if type == "string" then gsub("\\{\\{model\\}\\}"; $m) else . end)' <<<"$PROBE" >"$REQUEST"

    if [ "$(jq -r '.roundTrip == true' <<<"$PROBE" | tr -d '\r')" = true ]; then
        roundtrip "$ID" "$NAME" "$PATH_" "$(jq -r '.apiFlavor' <<<"$PROBE" | tr -d '\r')" "$REQUEST" || FAILED=1
        rm -f "$REQUEST"
        continue
    fi

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
