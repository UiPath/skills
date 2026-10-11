# Defects — raise, trace, and link bugs from failed results

A **defect** is a bug record raised from **one test case result** (a test case log) in an execution. Test Manager writes the defect's name (`<test case name> — <result>`) and description (start time, duration, step logs) from that result. If the project has a defect tracker connected (Jira, Azure DevOps, ServiceNow, Redmine, qTest, webhook), a background job then opens the matching issue there.

All commands take `--output json`. Every command needs `--project-key <KEY>` (or `--project-id`). Defects have **no key and no name search** — address them by UUID (`--defect-id`).

## Commands

| Goal | Command |
|---|---|
| Raise a defect from a result | `uip tm defects create --project-key <KEY> --execution-id <UUID> --test-case-id <UUID>`, or `--test-case-key <KEY:N>` in place of `--test-case-id` (exactly one). Optional: `--variation-id` for one variation of a data-driven case, `--detail-link <url>` to put a link to the result into the description |
| List defects | `uip tm defects list --project-key <KEY>` (optional `--changed-since <ISO-8601>`, `--sort-by "<Property> asc\|desc"`, `--limit 1-100`, `--offset`) |
| Get one | `uip tm defects get --project-key <KEY> --defect-id <UUID>` |
| Change status / priority / tracker link | `uip tm defects update --project-key <KEY> --defect-id <UUID>` with at least one of `--status <text>`, `--priority <text>`, `--external-reference <ISSUE-KEY>`, `--external-link <url>` |
| Delete | `uip tm defects delete --project-key <KEY> --defect-id <UUID> --yes` |
| Tracker issue it is synced to | `uip tm defects get-external-issue --project-key <KEY> --defect-id <UUID>` |
| Result it came from | `uip tm defects get-related --project-key <KEY> --defect-id <UUID> --object-type TestCaseLog` |
| Test case it came from | `uip tm defects get-related --project-key <KEY> --defect-id <UUID> --object-type TestCase` |
| Execution it came from | `uip tm defects get-related --project-key <KEY> --defect-id <UUID> --object-type TestExecution` |
| Requirements it puts at risk | `uip tm defects get-related --project-key <KEY> --defect-id <UUID> --object-type Requirement` (returns a list) |
| Evidence on it | `uip tm defects attachments list --project-key <KEY> --defect-id <UUID>` (each row's `Id` is the `--attachment-id`) |
| Save one piece of evidence | `uip tm defects attachments download --project-key <KEY> --defect-id <UUID> --attachment-id <ID> --result-path <DIR>` saves it under the server's file name inside `<DIR>`; `--output-file <PATH>` saves it to that exact path instead. Add `--overwrite` only to replace a file the user agreed to replace. The output gives `FileName`, `OutputPath` and `Size` |

## Finding the right IDs

- **To raise a defect**, get both IDs from the failed result: `uip tm executions testcaselogs list --execution-id <EXECUTION_ID> --project-key <KEY> --only-failed --output json`. Each row's `TestCaseId` is the `--test-case-id` (or pass its `TestCase.ObjKey`, such as `DEMO:7`, as `--test-case-key`); the execution you listed is the `--execution-id`. If the user already gave you the test case key, pass it with `--test-case-key` instead of looking up the id.
- **To find the defect already raised on a result**, read the same row's `DefectId`. An all-zero (`00000000-…`) or empty value means no defect yet. This beats `defects list`, which has no filter and returns every defect in the project.
- Use `defects list` only to browse, or with `--changed-since` for "recent defects". Never page through all of it to find one defect by name.

## Rules that save a failed call

1. **`update` and `delete` are slow — often 10–40 s each — so give every `defects` call a shell time limit of at least 120 s** (for example Codex `timeout_ms: 120000`, Claude Code Bash `timeout: 120000`). Many agent shells stop waiting after about 10 s by default; the call then looks like it returned nothing while Test Manager is still applying it. Run one `defects` call at a time and wait for its JSON before the next: a `get` sent while an `update` on the same defect is still running can fail with `HTTP 500`. If a call was still cut off, do not re-run it — wait 30 s, then run `defects get` once to see whether the change landed, and apply Critical Rule 10 to anything that still fails.
2. **One defect per result.** A second `create` on the same result fails with `A defect already exists against this test case log.` or `A defect creation is already in progress against this test case log.` That is not an error to retry — read the result's `DefectId` and work with that defect.
3. **`SyncStatus` tells you where the tracker sync is.** `InProgress` right after create is normal. `Success` means `Link`/`LinkLabel` hold the tracker issue. `Failed` means the tracker rejected it; running `create` again on the same result retries the sync.
4. **No tracker connected → the defect stays `InProgress` for good.** To link it to an issue the user filed by hand, run `defects update --external-reference <ISSUE-KEY> --external-link <url>`. That marks it `Success`.
5. **Two trackers connected → create fails** with `Unable to create defect when multiple connectors are configured for defects.` Stop and ask the user to fix the project's connector setup (Critical Rule 10).
6. **Only status, priority and the tracker link can change.** Name and description are fixed. Status and priority are free text with no allowed list, so reuse the values the user or tracker already uses. `update` changes Test Manager only and is not pushed to the tracker.
7. **Delete is permanent, and the tracker issue survives it.** It unlinks the result, so a new defect can be raised on it later. Confirm the exact defect first (Critical Rule 5).
8. **`get-related` takes exactly one `--object-type`** — `TestCase`, `TestExecution`, `TestCaseLog` or `Requirement`, case-sensitive. To answer several questions about one defect, run it once per type.
9. **`get-related` fails with not-found when no result is linked** to the defect any more. Report that; do not guess the origin.
10. **`attachments download` never replaces an existing file on its own.** If the target already exists it stops with `'<path>' already exists; nothing was downloaded.` and writes nothing. Ask the user before re-running with `--overwrite`, or pick another `--result-path` / `--output-file`. A target that is a folder is refused even with `--overwrite`.
11. **Unsafe server file names are saved under the attachment id.** A name that starts with a dot (`.npmrc`), a Windows device name (`CON`), or an empty name becomes the attachment id inside `--result-path`. Read the real path from `OutputPath`, never assume it from the attachment's `FileName`.
