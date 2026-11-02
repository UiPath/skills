# Defects — raise, trace, and link bugs from failed results

A **defect** is a bug raised from **one test case result** (a test case log); a connected tracker (Jira, Azure DevOps, …) opens the matching issue in the background. Every command takes `--project-key <KEY> --output json`; defects are addressed only by `--defect-id <UUID>`. Each verb's `--help` and error messages explain its own constraints (one defect per result, `SyncStatus`, hand-linking with no tracker, what `update` can change, `get-related` object types, download overwrite). This guide covers only what they do not.

## Commands

| Goal | `uip tm defects …` |
|---|---|
| Raise from a result | `create --execution-id <UUID>` plus `--test-case-id <UUID>` or `--test-case-key <KEY:N>` |
| List / get | `list` (`--changed-since <ISO-8601>`, `--sort-by`, `--limit`, `--offset`); `get --defect-id <UUID>` |
| Change status / priority / tracker link | `update --defect-id <UUID>` with `--status`, `--priority`, `--external-reference <ISSUE-KEY>`, `--external-link <url>` |
| Delete | `delete --defect-id <UUID> --yes` |
| Trace | `get-external-issue --defect-id <UUID>`; `get-related --defect-id <UUID> --object-type <TestCase\|TestExecution\|TestCaseLog\|Requirement>` |
| Evidence | `attachments list --defect-id <UUID>`; `attachments download --defect-id <UUID> --attachment-id <ID> --result-path <DIR>` |

## Scenario: triage a failed run into defects

The usual request — "file bugs for what failed in last night's run" — for a manual, automated or Playwright run:

1. Find the run's failures: `uip tm executions testcaselogs list --execution-id <EXECUTION_ID> --project-key <KEY> --only-failed --output json`.
2. For each failed row, read `DefectId`. All-zero or empty means no defect yet; anything else is the existing defect — reuse it, never page through `defects list` (it has no filter) to find one.
3. Triage the failure first ([failure-triage-guide.md](failure-triage-guide.md)): a flaky or environment failure usually needs a rerun, not a defect. Ask the user when the verdict is unclear.
4. Raise each real failure: `defects create --execution-id <EXECUTION_ID> --test-case-id <TestCaseId>` (or `--test-case-key` with the row's `TestCase.ObjKey`).
5. Apply what the user asked for in one `update`: status, priority, and — when they filed the issue by hand — `--external-reference`/`--external-link`.
6. Report each defect with its test case, the requirements it puts at risk (`get-related --object-type Requirement`), its tracker link, and its evidence (`attachments list`).

## Rules the CLI does not tell you

1. **`update` and `delete` often take 10–40 s, so give every `defects` call a shell time limit of at least 120 s** (Codex `timeout_ms: 120000`, Claude Code Bash `timeout: 120000`). Many shells stop waiting after about 10 s, and the call then looks empty while Test Manager is still applying it. Run one `defects` call at a time: a `get` sent while an `update` on the same defect is running can fail with `HTTP 500`. If a call was still cut off, do not re-run it — wait 30 s, run `defects get` once to see whether the change landed, and apply Critical Rule 10 to anything that still fails.
2. **`attachments list` returning `[]` means "no evidence", not an error.** It lists step attachments and robot screenshots taken from the result; a file uploaded to the result itself (`uip tm attachment upload --object-type testCaseLog`) does not appear. Report "no evidence" and continue.
3. **Status and priority are free text with no allowed list.** Reuse the exact values the user or their tracker already uses (for example `High`, not `P1`) so defects stay filterable.
