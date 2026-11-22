# Performance HTTP Recording Rules Guide (hartolocust/v1)

Rules file shape, rule types, generation diagnostics, and diff-report triage for `uip tm perf-scenario http-recordings update-rules`. Workflow and commands: [perf-http-recordings-guide.md](perf-http-recordings-guide.md).

The service checks rules against its hartolocust/v1 JSON schema, where every object is closed (`additionalProperties: false`). Never invent fields. Copy shapes from this page, the recording's current `ConfigRulesJson` (`http-recordings get`), or a template's `RulesJson` (`correlation-templates list`).

## Shape

```json
{
  "schemaVersion": 1,
  "settings": {
    "hosts": ["<APP_HOST>"],
    "excludeStatic": true,
    "excludePreflight": true,
    "excludeAborted": true,
    "excludeBeacon": true,
    "excludeFromCache": true,
    "exclude": [{ "request": "* /socket.io/**" }],
    "dropHeaders": ["x-client-trace-id"],
    "seedRecordedCookies": false
  },
  "rules": []
}
```

`schemaVersion`, `settings`, and `rules` are required. `"settings": {}` and `"rules": []` replay the HAR as recorded.

| Setting | Effect |
|---------|--------|
| `hosts` | Host allowlist; `null` = every host in the HAR. The script replays against one host (`ReplayHost` in the report): list the application's API host only. Other-host entries count as `UnmatchedRecorded.OtherHosts` |
| `excludeStatic` / `excludePreflight` / `excludeAborted` / `excludeBeacon` / `excludeFromCache` | Drop images/fonts/scripts/css, CORS `OPTIONS`, status-0 entries, telemetry beacons, browser-cache hits |
| `exclude` | Extra request matchers to drop |
| `dropHeaders` | Request headers stripped from every request, added to the fixed drop list (`cookie`, `sec-*`, pseudo-headers) |
| `seedRecordedCookies` | Seed the cookie jar once with the recorded session's cookies. Writes live session values into the script; use only to replay inside a still-alive recorded session with a test user |

## Matchers

`"METHOD /path/template"`. METHOD: `GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS|MERGE|*`. `{name}` or `*` = one path segment, `**` = any number of segments. Matches method + path only — no host, no query. Optional `"occurrence": "first" | "last" | <N>` (0-based among matches). Rule ids match `^[a-z][a-z0-9_]{0,63}$` and are unique.

## Rule Types

### correlation

Value from a response, sent in later requests. When extraction fails at run time (for example login failed), the request still goes out with the recorded value.

```json
{ "id": "auth_token", "type": "correlation",
  "from": { "request": "POST /api/login" },
  "extract": { "json": "$.token" },
  "replace": [ { "in": { "request": "* /api/**" }, "header": "Authorization", "prefix": "Bearer " } ] }
```

- Extractor, exactly one: `{"json": "$.a.b[0]"}`, `{"header": "x-csrf-token", "pattern": "<ONE_CAPTURE_GROUP>"}` (pattern optional), `{"regex": "<ONE_CAPTURE_GROUP>"}` over the body, `{"html": {"input": "<NAME>"}}` or `{"html": {"meta": "<NAME>"}}`. Optional `"transform"`: ordered list of `htmlUnescape`, `urlDecode`, `urlEncode`, `base64Decode`, `base64Encode`. Optional `"part"` (1-based or `"any"`) for multipart bodies; not on `header`.
- Replace target, exactly one per entry: `"header"` (name), `"json"` (JSONPath to a scalar), `"query"`, `"form"`, `"path"` (1-based segment index). Optional `"prefix"`, ignored for `json`. A `header` target absent from the recorded request is added, so a correlation can restore an `Authorization` header a sanitized HAR export stripped.
- Targets must come later in the HAR than the first `from` match.

### parameter

Fixed value in one slot.

```json
{ "id": "user_name", "type": "parameter", "target": { "request": "POST /api/login" },
  "selector": "body", "at": "$.email", "literal": "<TEST_USER_NAME>" }
```

`selector`: `body` (JSONPath in `at`) | `header` | `query` | `form` (name in `at`). `literal`: string, number, boolean, or `null`. A parameter beats a correlation on the same slot (`PARAM_OVERRIDES_CORRELATION`).

`"literal": "${env:<NAME>}"` reads a robot environment variable at run time. Serverless robots — where validation and recording load groups run — set none, so the value goes out empty: use a literal test value. No random or unique-value generator exists: values that must be unique per iteration are a known limitation; tell the user.

### verification

Override the expected outcome of matching requests.

```json
{ "id": "order_created", "type": "verification", "when": { "request": "POST /api/orders" },
  "expect": { "status": [201], "json": { "$.status": "OPEN" }, "contains": "orderId" } }
```

Default without a rule: the recorded status; recorded `304` accepts `200` or `304`; recorded `0` (aborted) has no status check. A failed check fails the request; the replay continues.

### remove

Drop query/header/form fields, optionally only values matching `valueMatches` (RE2).

```json
{ "id": "no_cache_buster", "type": "remove", "target": { "request": "GET /**" }, "in": "query", "names": ["_"] }
```

### rewrite

Regex replace in `path`, `query`, or `body` at generate time; `$1`..`$9` backrefs, no variables. Cannot change the host.

```json
{ "id": "env_host_path", "type": "rewrite", "target": { "request": "* /tenant-a/**" },
  "in": "path", "pattern": "^/tenant-a/", "replace": "/tenant-b/" }
```

## Patterns by App Type

| App | Typical rules |
|-----|---------------|
| SPA + JSON API (JWT) | Token correlation from login `$.token` / `$.access_token` → `Authorization` header, prefix `Bearer `; created-object ids `$.data.id` → `path` or `json` of later calls |
| Classic form login | `html.input` for the CSRF/authenticity token → `form` of the POST; session via Set-Cookie (automatic) |
| SAP Fiori / OData | `x-csrf-token` header from the `x-csrf-token: Fetch` GET → `header` on modifying calls (POST/PATCH/MERGE/`$batch`). SAML chain: `html.input` `SAMLResponse` / `RelayState` / `authenticity_token` → `form`. IdP needs MFA → `seedRecordedCookies` inside the recorded session |
| Anything with telemetry | `exclude` beacon/analytics paths; `hosts` allowlist |

Session cookies: per-request `Cookie` headers are always dropped; the replay client keeps Set-Cookie from live responses. Login inside the recording → nothing to do. Recording starts already logged in → `seedRecordedCookies: true` (works only while that session lives) or re-record including login.

## Generation Diagnostics

`generate-script` returns warnings in `Data.Warnings`. An error fails the command (`hartolocust generate failed: <CODE>: <message>`) and moves the recording to `Failed` with the reason in `get` → `ErrorMessage`. `update-rules` may also reject a file outright with HTTP 400 naming the schema problem.

| Code | Level | Meaning | Fix |
|------|-------|---------|-----|
| `CORR_VALUE_NOT_FOUND` | error | Extractor found the value in none of the recorded `from` responses | Inspect the response structure ([jq recipes](perf-http-recordings-guide.md#inspect-the-local-har-structure-only)); fix JSONPath/regex/header name; narrow `from` with `occurrence` |
| `CORR_EXTRACT_PARTIAL` | info | Found in only some `from` responses | Usually fine; narrow `from` with `occurrence` when the wrong response carries it |
| `CORR_REPLACE_EMPTY` | error | `replace` missing or empty | Add at least one target |
| `CORR_REPLACE_NO_TARGET` | warning | `replace.in` matched nothing after the first carrier | Fix the matcher (`*` or `{name}` for id segments), or `from` matches too late |
| `PARAM_TARGET_NOT_FOUND` | warning | Slot absent from the matched requests | Fix `at` (JSONPath or name) or the matcher |
| `PARAM_OVERRIDES_CORRELATION` | warning | Parameter replaces a correlation on the same slot | Intended? Otherwise drop one |
| `REWRITE_UNMATCHED` / `REMOVE_UNMATCHED` | warning | Pattern or names never matched | Fix or drop the rule |
| `SCHEMA_INVALID` / `RULE_PARSE_ERROR` / `RULE_DUPLICATE_ID` / `RULES_JSON_INVALID` | error | Rules violate the schema | Read the message (path + reason); fix the file |
| `HAR_JSON_INVALID` / `NO_ENTRIES` / `HAR_OUT_OF_ORDER` | error | HAR unreadable, every entry excluded, or entries out of order | Check `hosts` and exclusions; otherwise re-export the HAR and `create` a new recording |
| `GEN_SYNTAX_ERROR` / `GEN_LINT` | error | Generator bug | Stop; report it with the rules file — not a rules problem |
| `STRING_LONE_SURROGATE` / `SCHEMA_MISSING` | warning | Invalid UTF-16 in a recorded string / service could not load its schema | Report; rules cannot fix it |

## Diff Report

`get-report` → `Data.Report`, PascalCase as the service wrote it (`null` when the run failed before comparing):

- Top level: `Success`, `CompletedIteration`, `IterationError`, `ReplayHost`, `RecordedHost`, `RecordedEntries`, `PassedEntries`, `FailedEntries`, `FinalVariables`, `UnmatchedRecorded` (`StaticAssets`, `OtherHosts`, `NotReplayedCount`, `NotReplayed[]` capped at 50 with `Index`, `Method`, `Url`, `Status`).
- `Entries[]`: `Index`, `RecordedIndex` (HAR `log.entries` index = `harIndex`; `null` = extra request not in the HAR), `Method`, `Url` (redacted), `ExpectedStatus`, `ActualStatus`, `StatusMatched`, `BodyMatched`, `Mismatches[]` (failed the entry), `Warnings[]` (soft), `ExtractedValues`, `Error`, `OutOfOrder`, `Success`, expected/actual content type and size.

Verdict: `Failed` when `Success` is false. `PassedWithWarnings` when `NotReplayedCount > 0` or any entry has `Warnings`, `OutOfOrder`, or `RecordedIndex: null`. Otherwise `Passed`.

Summary counts: `TotalRecorded` = `RecordedEntries`, `Matched` = `PassedEntries`, `Mismatched` = `FailedEntries`, `Missing` = `NotReplayedCount`, `Extra` = entries with `RecordedIndex: null`.

`ExtractedValues` and `FinalVariables` hold live tokens and ids: report only which names are present or empty, never values.

## Triage

Work from the **first** failing entry; later failures are usually its consequence.

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| 401/403 from the first protected call on | Token/session not correlated, or login failed | Check the login entry passed and its `ExtractedValues` has the token name; add or fix the token correlation; check the credentials parameter |
| Expected 302 got 200 (or reverse) at the start | SSO/SAML redirect chain differs, or recording started logged in | Correlate SAML form fields; or exclude the IdP hops and use `seedRecordedCookies`; or re-record including login |
| 403/400 on POST/PATCH/MERGE only | CSRF token missing | Correlation from the `x-csrf-token: Fetch` response header → `header` `x-csrf-token` |
| 404 on a path with an id | Id created during the flow, sent stale | Correlation from the creating call's response → `path` segment |
| 404 on every request | Replay sent to the wrong host (paths recorded against another host) | Compare `ReplayHost` with `RecordedHost`; set `settings.hosts` to the application's API host |
| 400/409/422 "duplicate" / "already exists" | Business key must be unique per run | Parameter with a fresh literal; explain the no-unique-value limitation |
| 304 expected, 200 got (warning) | Replay has no browser cache | Expected; accept |
| Status matches, correlation name empty in `ExtractedValues` | Live response shape differs from the recording | Compare live vs recorded structure; loosen JSONPath/regex |
| Many `NotReplayed` you need | Excluded by settings | Adjust `hosts` / `exclude*` settings |
| `CompletedIteration: false` with `IterationError` | Script stopped mid-journey | Read `IterationError`; fix the rule it names, else report |
| 5xx | Server-side state or load, or bad request body | Inspect the request with `get-har-entry`; body correct → server problem: tell the user |
| 429 | Rate limiting | Not a rules problem; tell the user |
| Timeout / connection error | Host unreachable from UiPath's serverless robots | Not a rules problem; the application needs a public DNS name — tell the user and stop |
