# Defects — raise, trace, and link bugs from failed results

A **defect** is a bug raised from **one test case result** (a test case log). Test Manager writes its name (`<test case name> — <result>`) and description from that result; a connected tracker (Jira, Azure DevOps, ServiceNow, Redmine, qTest, webhook) then opens the matching issue in the background.

Every command below takes `--project-key <KEY> --output json`. Defects have no key or name search; address them by `--defect-id <UUID>`.

## Commands

| Goal | `uip tm defects …` |
|---|---|
| Raise from a result | `create --execution-id <UUID>` plus `--test-case-id <UUID>` or `--test-case-key <KEY:N>` (exactly one); optional `--variation-id`, `--detail-link <url>` |
| List / get | `list` (optional `--changed-since <ISO-8601>`, `--sort-by "<Property> asc\|desc"`, `--limit 1-100`, `--offset`); `get --defect-id <UUID>` |
| Change | `update --defect-id <UUID>` with any of `--status`, `--priority`, `--external-reference <ISSUE-KEY>`, `--external-link <url>` |
| Delete | `delete --defect-id <UUID> --yes` |
| Tracker issue | `get-external-issue --defect-id <UUID>` |
| Origin / impact | `get-related --defect-id <UUID> --object-type <TestCase\|TestExecution\|TestCaseLog\|Requirement>` (`Requirement` returns a list) |
| Evidence | `attachments list --defect-id <UUID>` (row `Id` = `--attachment-id`); `attachments download --defect-id <UUID> --attachment-id <ID>` with `--result-path <DIR>` or `--output-file <PATH>`; output gives `FileName`, `OutputPath`, `Size` |

## Finding the right IDs

- **Raise:** run `uip tm executions testcaselogs list --execution-id <EXECUTION_ID> --project-key <KEY> --only-failed --output json`. A row's `TestCaseId` (or `TestCase.ObjKey` as `--test-case-key`) plus the listed execution are the two ids. If the user gave the test case key, pass it directly.
- **Existing defect on a result:** read that row's `DefectId`; all-zero or empty means none. Never page through `defects list` (no filter) to find one; use it only to browse or with `--changed-since`.

## Rules that save a failed call

1. **`update` and `delete` often take 10–40 s, so give every `defects` call a shell time limit of at least 120 s** (Codex `timeout_ms: 120000`, Claude Code Bash `timeout: 120000`). Many shells stop waiting after about 10 s, and the call then looks empty while Test Manager is still applying it. Run one `defects` call at a time: a `get` sent while an `update` on the same defect is running can fail with `HTTP 500`. If a call was still cut off, do not re-run it — wait 30 s, run `defects get` once to see whether the change landed, and apply Critical Rule 10 to anything that still fails.
2. **One defect per result.** A second `create` fails with `A defect already exists against this test case log.` or `A defect creation is already in progress against this test case log.` Do not retry it; read the result's `DefectId` and work with that defect.
3. **`SyncStatus` is the tracker sync state.** `InProgress` right after create is normal; `Success` means `Link`/`LinkLabel` hold the issue; `Failed` means the tracker rejected it, and running `create` again on the same result retries the sync.
4. **No tracker connected → the defect stays `InProgress`.** To link an issue the user filed by hand, run `update --external-reference <ISSUE-KEY> --external-link <url>`; that marks it `Success`.
5. **Two trackers connected → `create` fails** with `Unable to create defect when multiple connectors are configured for defects.` Stop and ask the user to fix the connector setup (Critical Rule 10).
6. **Only status, priority and the tracker link can change.** Status and priority are free text; reuse the values the user or tracker already uses. `update` changes Test Manager only and is not pushed to the tracker.
7. **Delete is permanent; the tracker issue survives it.** It unlinks the result, so a new defect can be raised on it. Confirm the exact defect first (Critical Rule 5).
8. **`get-related` takes exactly one case-sensitive `--object-type`;** run it once per question. It fails with not-found when no result is linked to the defect any more — report that, do not guess the origin.
9. **`attachments list` returning `[]` means "no evidence", not an error.** It lists step attachments and robot screenshots taken from the result; a file uploaded to the result itself (`uip tm attachment upload --object-type testCaseLog`) does not appear. Report "no evidence" and continue.
10. **`attachments download` never overwrites on its own.** An existing target stops it with `'<path>' already exists; nothing was downloaded.` Ask the user before re-running with `--overwrite`, or pick another path; a folder target is refused even with `--overwrite`. A server file name starting with a dot, a Windows device name, or an empty name is saved under the attachment id, so read the real path from `OutputPath`.
