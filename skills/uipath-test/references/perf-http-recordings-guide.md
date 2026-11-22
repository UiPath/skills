# Performance HTTP Recordings (HAR Replay) Guide

Load-test from a browser recording instead of an automated test case: upload a HAR, correlate session values, generate and validate the replay script, promote it, and bind it to a load group. Covers `uip tm perf-scenario http-recordings`, `uip tm perf-scenario correlation-templates list`, and `--recording-id` / `--recording-name` on `perf-scenario load-groups add|update`.

Rules file format, generation diagnostics, and diff-report triage: [perf-http-recording-rules-guide.md](perf-http-recording-rules-guide.md). Running the scenario (dry run, licence, full run, results): SKILL.md § Performance (load) testing.

## Critical Rules

1. **Preview CLI only.** Probe once with `uip tm perf-scenario http-recordings --help --output json`. `unknown command` means a stable build: tell the user `uip update --channel preview` installs the preview build; run it only after the user agrees, then probe again.
2. **HARs hold secrets.** HAR files, `get-har-info`, `get-har-entry`, diff reports, `ExtractedValues`, and `FinalVariables` carry cookies, tokens, and credentials. Summarize; never print header values, bodies, or extracted values into the answer or a command line. Read a local HAR only with the structure-only `jq` filters below.
3. **Select by id.** Every recording verb needs `--recording-id <RECORDING_ID>` or `--recording-name <NAME>`, never both. Keep `Data.Id` from `create` and use `--recording-id` from then on; names are not unique.
4. **Confirm before robots run.** Before `validate` and before any `perf-scenario execute`, tell the user it starts a serverless robot job in the recording's Orchestrator folder, consumes robot time, and hits the target application for real — every write in the recorded flow repeats. Get a yes.
5. **Rules need a yes.** Write rules files to a scratch directory, never the user's repository. Explain each rule in one line and get a yes before `update-rules`.
6. **Regenerate after rules change.** `update-rules` drops the script and resets the recording to `Pending`; run `generate-script` before `validate` or `promote`.
7. **Promoted only.** A load group can use only a `Promoted` recording. A load group has a test case **or** a recording, never both.
8. **Public target only.** Replay runs on UiPath's serverless robots: the application must answer on a public DNS name. Hosts reachable only through VPN, `/etc/hosts`, or `localhost` fail with connection errors that no rule fixes — tell the user and stop.
9. **A Failed verdict is a result, not a CLI failure.** `validate --wait` exit `1` with `Code: HttpRecordingValidationFailed` and `Data.Status: Completed` starts the triage loop (Step 4). Do not retry the command unchanged.

## Lifecycle

Recording `Status`:

| Status | Meaning | Next |
|--------|---------|------|
| `Pending` | Uploaded, or rules just changed; no script | `update-rules`, `generate-script` |
| `ScriptReady` | Script generated | `validate`, `promote`, `update-rules` |
| `Replaying` | Validation running; rules and script locked (409) | Wait; `get-report` returns `Retry: RetryAfter30Seconds` |
| `Replayed` | Validation finished on the current script | `promote`, `validate`, `update-rules` |
| `Promoted` | Usable by load groups; stays `Promoted` after a later validation | `load-groups add\|update --recording-id` |
| `Failed` | Script generation failed; reason in `get` → `ErrorMessage` | `update-rules`, `generate-script` |

Validation `Status`: `Queued` → `JobRunning` → `TracesReceived` → `GeneratingReport` → `Completed` (with `Verdict` `Passed` / `PassedWithWarnings` / `Failed`), or `Failed` / `TimedOut` when the run itself broke. One validation per recording at a time.

## Commands

Every `http-recordings` verb except `create` and `list` takes `--recording-id <RECORDING_ID> --project-key <PROJECT_KEY> --output json`; shown below as `<SEL>`.

| Task | Command | Success `Code`; key `Data` |
|------|---------|----------------------------|
| Upload HAR | `uip tm perf-scenario http-recordings create --har-file <HAR_PATH> --project-key <PROJECT_KEY> [--name <NAME>] [--folder-path <FOLDER_PATH> \| --folder-key <FOLDER_KEY>] --output json` | `HttpRecordingCreate`; `Id`, `Name`, `Status: Pending` |
| List | `uip tm perf-scenario http-recordings list --project-key <PROJECT_KEY> --output json` | `HttpRecordingsList`; rows `Id`, `Name`, `FolderKey`, `Status`, `HarSizeBytes` |
| Get one | `uip tm perf-scenario http-recordings get <SEL>` | `HttpRecordingGet`; `Status`, `FolderKey`, `ConfigRulesJson` (string), `ErrorMessage` |
| HAR digest | `uip tm perf-scenario http-recordings get-har-info <SEL>` | `HttpRecordingHarInfo`; `HarInfo.summary` (`totalEntries`, `includedEntries`, `excluded`, `hosts`), `HarInfo.requests[]` (`harIndex`, `method`, `template`, `status`, `contentType`), `HarInfo.findings[]` |
| One request | `uip tm perf-scenario http-recordings get-har-entry <SEL> --har-index <N>` | `HttpRecordingHarEntry`; `Entry` (`method`, `path`, `status`, `contentType`, request `body` cut to 2 KB, `truncated`) — request side only |
| Templates | `uip tm perf-scenario correlation-templates list --project-key <PROJECT_KEY> --output json` | `CorrelationTemplatesList`; `TemplateId`, `Label`, `Description`, `RulesJson`, `IsCustom` |
| Save rules | `uip tm perf-scenario http-recordings update-rules <SEL> --rules-file <RULES_PATH>` or `--template-id <TEMPLATE_ID>` | `HttpRecordingRulesUpdate`; `Status: Pending` |
| Generate script | `uip tm perf-scenario http-recordings generate-script <SEL>` | `HttpRecordingScriptGenerate`; `Status: ScriptReady`, `EntryCount`, `RuleCount`, `Warnings[]` |
| Validate | `uip tm perf-scenario http-recordings validate <SEL> --wait` | `HttpRecordingValidate`; `ValidationId`, `Status`, `Verdict`, `TotalRecorded`, `Matched`, `Mismatched`, `Missing`, `Extra` |
| Report | `uip tm perf-scenario http-recordings get-report <SEL>` | `HttpRecordingValidationReport`; summary, `IsStale`, `Report` (diff document or `null`) |
| Promote | `uip tm perf-scenario http-recordings promote <SEL>` | `HttpRecordingPromote`; `Status: Promoted` (idempotent) |

Pass `--har-file`, `--rules-file` as absolute paths. With both `--rules-file` and `--template-id`, the file's rules are saved and the template is only recorded on the recording. `list` and `correlation-templates list` accept `--limit` / `--offset` (row window over the whole list).

## Workflow

### Step 0 — Preflight

1. Probe the preview CLI (Critical Rule 1).
2. Authenticate and resolve the project (SKILL.md Rule 1, Quick Start step 2).
3. Run `http-recordings list --project-key <PROJECT_KEY> --output json`. A 404 means the tenant's Performance Service has HAR replay (`EnableHarReplay`) off: report it and stop. Existing rows show recordings the user may mean to reuse.

### Step 1 — Inputs

Ask once, together, only for what is missing:

- **HAR file.** "Downloads" = `~/Downloads`. Bare name → `ls -t ~/Downloads/<NAME>*.har`; one match → use it, several → ask. Confirm it is a HAR without printing content: `jq '.log.entries | length' <HAR_PATH>` returns a number > 0. Cap: 200 MB (`ls -l <HAR_PATH>`).
- **Folder.** User named one → `--folder-path` or `--folder-key` (lookup per SKILL.md Rule 6). None named → omit both: `create` uses the project's default folder and logs which one; tell the user. No default folder → ask.
- **Login.** Does the recording include login, or start already logged in? Which test user should the replay log in as (literal value in a parameter rule)?
- **Load profile** — only when the user wants a load group now: virtual users, ramp-up / peak / ramp-down / delay minutes, max response time ms, max error rate.

### Step 2 — Upload and read the HAR

1. `create` → keep `Data.Id`.
2. `get-har-info` → tell the user: total vs included entries, hosts, the request sequence (method + template + status), and `findings` (for example `ENTRY_ABORTED`). Identify the application's API host, the login request, responses that issue tokens or ids, and telemetry hosts to exclude.
3. Response bodies and headers are not exposed by the CLI; read their structure from the local HAR (next section).
4. Later calls carry no `Authorization`/cookie although login returns a token → the HAR export stripped them (sanitized export). Plan a correlation that adds an `Authorization` header and confirm its format during triage.

#### Inspect the local HAR (structure only)

`harIndex` = 0-based position in `log.entries`. These filters print names, paths, and indices — never values:

```bash
jq -r '.log.entries[<N>].response.headers[].name' <HAR_PATH>
jq -r '.log.entries[<N>].request.headers[].name' <HAR_PATH>
jq -r '.log.entries[<N>].response.content.text | fromjson? | paths(scalars) | map(tostring) | join(".")' <HAR_PATH>
jq -r '.log.entries[<N>].response.content.encoding // "plain"' <HAR_PATH>
```

Empty JSON-path output with `encoding: base64`, or a non-JSON body → say so; do not decode into the answer.

Find which later requests reuse a response value, printing only their indices:

```bash
V="$(jq -r '.log.entries[<N>].response.content.text | fromjson | <JQ_PATH>' <HAR_PATH>)"
jq -r --arg v "$V" 'select($v != "" and $v != "null") | .log.entries | to_entries[] | select((.value.request | tostring) | contains($v)) | .key' <HAR_PATH>
```

`<JQ_PATH>` is a jq path such as `.token` or `.data.id`.

### Step 3 — Rules and script

1. Pick a start: the current rules (`get` → write `ConfigRulesJson` to a file), a template (`correlation-templates list`; match by `Label` / `Description`), or a new file.
2. Write rules per [perf-http-recording-rules-guide.md](perf-http-recording-rules-guide.md). Most apps need `settings.hosts` = the API host plus a login-token correlation; a stateless app can replay with `"rules": []`.
3. Explain each rule in one line, get a yes (Critical Rule 5), run `update-rules`.
4. `generate-script` → report `EntryCount`, `RuleCount`, and each `Warnings[]` code with its fix from the rules guide. Generation error → the command fails, the recording is `Failed`; read `get` → `ErrorMessage`, fix the rules, repeat.

### Step 4 — Validate and iterate

1. Confirm (Critical Rule 4), naming the folder.
2. Run `validate <SEL> --wait` with a shell timeout above the wait (default `--timeout-sec` 1800). Shell limit shorter → pass `--timeout-sec` below it, or start without `--wait` and poll `get-report` every 30–60 s. A wait timeout (`Result: TimeoutError`) leaves the validation running: poll `get-report`, never start another `validate`.
3. Read the outcome:

   | Exit / `Data` | Meaning | Next |
   |---------------|---------|------|
   | `0`, `Verdict: Passed` | Faithful replay | Step 5 |
   | `0`, `Verdict: PassedWithWarnings` | Soft findings (304→200, extra or not-replayed requests) | List them; user accepts → Step 5, else iterate |
   | `1`, `HttpRecordingValidationFailed`, `Status: Completed` | `Verdict: Failed` | `get-report`, triage |
   | `1`, `HttpRecordingValidationFailed`, `Status: TimedOut` | Run timed out on the service | `validate` once more; second time → report, stop |
   | `1`, `HttpRecordingValidationFailed`, `Status: Failed` | Job or report failed before comparing (`ErrorMessage` in `Message`) | Report, stop — not a rules problem |

4. Triage: `get-report` → [rules guide § Triage](perf-http-recording-rules-guide.md#triage), first failing entry first. Propose the smallest rules change, get a yes, then `update-rules` → `generate-script` → `validate --wait` → `get-report`.
5. Report one line per iteration: `v2: 28/30 matched, 2 mismatched, 0 missing, 0 extra — Failed (401 from entry 14)`.
6. Stop after 6 iterations without improvement in `Matched` or `Verdict`; summarize the blocker and ask the user.
7. `IsStale: true` → the report predates the current script; validate again before relying on it.

### Step 5 — Promote and bind to a load group

1. `promote <SEL>` (needs `ScriptReady` or `Replayed`).
2. Scenario: reuse one (`perf-scenario list --project-key <PROJECT_KEY> --search <NAME> --output json`) or create one: `uip tm perf-scenario create --project-key <PROJECT_KEY> --name "<NAME>" --app-type web --output json` → `Data.ScenarioKey`.
3. New load group:

   ```bash
   uip tm perf-scenario load-groups add --scenario-key <SCENARIO_KEY> --recording-id <RECORDING_ID> --virtual-users <N> --ramp-up-minutes <N> --peak-minutes <N> --ramp-down-minutes <N> --output json
   ```

   Returns `Code: LoadGroupAdd` with `LoadGroupId`, `HttpRecordingId`, `RecordingName`. The group takes the recording's name and folder and replays on serverless robots. `--test-case-key`, `--test-case-id`, `--folder-key`, `--package-name`, `--package-version`, and `--robot-type` are refused alongside a recording (`cannot be used with`). Optional: `--delay-minutes`, `--max-response-time-ms` (≥ 100), `--max-error-rate` (≥ 0.0001).
4. Verify the stored profile: `perf-scenario get --scenario-key <SCENARIO_KEY> --output json`, find the group by `HttpRecordingId`. Profile differs from what was asked → `perf-scenario load-groups update --load-group-id <LOAD_GROUP_ID> --project-key <PROJECT_KEY> --virtual-users <N> … --output json`; the update keeps the recording link.
5. Switch an existing group to the recording: `uip tm perf-scenario load-groups update --load-group-id <LOAD_GROUP_ID> --project-key <PROJECT_KEY> --recording-id <RECORDING_ID> --output json`. Clears its test case and package, sets serverless, keeps the profile.
6. Serverless limit: delay + ramp-up + peak + ramp-down ≤ 60 minutes, or execution is refused.

### Step 6 — Run

Follow SKILL.md § Performance (load) testing steps 3–4: dry run, licence check, profile confirmation, full run, results. A scenario whose groups are all recordings fails `list-dry-run-reports` with `no test case carries an automationId`: use the Rule 10 (g) fallback. Tell the user each iteration repeats the recorded writes in the target application.

### Step 7 — Summary

Report: recording `Id` and `Status`, final rules file path, verdict trend per iteration, scenario key, `LoadGroupId` with its stored profile, execution ids and results. Remind the user that parameter literals (test credentials) are written into the generated script.

## Errors

| Symptom | Meaning | Action |
|---------|---------|--------|
| `unknown command 'http-recordings'` | Stable CLI build | Critical Rule 1 |
| HTTP 404 from every recording command | HAR replay (`EnableHarReplay`) off for the tenant | Report; stop |
| `No Orchestrator folder was given, and the project has no default folder.` | `create` without folder | Ask for the folder; pass `--folder-path` / `--folder-key` |
| `HAR exceeds the 200 MB limit.` (413) | HAR too large | Ask the user to record a shorter flow or export without static assets |
| `<N> HTTP recordings are named '<NAME>'` | Name ambiguous | Show the ids; ask; use `--recording-id` |
| `Recording cannot be validated while in status 'Pending'` (409) | No script | `generate-script`, then `validate` |
| 409 validation in progress / rules locked | `Replaying` | Wait; poll `get-report` |
| `Recording has no Orchestrator folder; re-upload the HAR to validate it.` | Legacy recording | `create` again from the HAR |
| HTTP 424 on `validate` | Orchestrator could not start the replay job (no serverless capacity in the folder, package unavailable to the folder's feed, or missing permission) | Report `Message`; stop |
| `get-report` → `Retry: RetryAfter30Seconds` | Validation still running | Retry after 30 s; not an error |
| `get-report` → `has never been validated` | No validation yet | Step 4 |
| `load-groups add` → `is <STATUS>, not Promoted` | Recording not promoted | Offer `promote` (needs a script) |
| Execution refused for total time | Serverless profile > 60 minutes | Shorten timings with `load-groups update` |

## Anti-patterns

- Do not paste HAR bodies, header values, digest entries, or extracted values into the answer — summarize.
- Do not run `validate` or `promote` after `update-rules` without `generate-script`.
- Do not start a second `validate` while one runs — poll `get-report`.
- Do not retry `HttpRecordingValidationFailed` unchanged; it is a verdict — triage and change the rules.
- Do not invent rule fields or add rules that bypass authentication; the schema is closed and the replay must log in as a real test user.
- Do not use `${env:<NAME>}` parameters for serverless replays; they send an empty value.
- Do not bind an unpromoted recording, or combine `--recording-*` with test-case or package flags.
- Do not use REST or edit the generated script directly; the CLI exposes neither, and rules are the supported fix.
