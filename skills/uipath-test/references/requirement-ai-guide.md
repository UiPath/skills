# Requirement AI — generate test cases, evaluate, find obsolete ones

Test Manager's AI reads a requirement's description (and any attachments passed with `--attachment-ids`) and runs one of three **background jobs**: `uip tm requirements generate-testcases`, `evaluate`, or `find-obsolete-testcases`. Flags: `--help`.

Every job has an `ActivityId`. The same verb with `--activity-id <ACTIVITY_ID>` reads that job, waits for it (`--wait`), or acts on it. **Each start spends the tenant's AI units and takes 1–5 min; reading a job by id is free.** The commands need a user login: if `uip login status --output json` shows `"IdentityType": "Application"`, stop and ask the user to run `uip login`.

## Scenario 1 — "Write test cases for this requirement"

1. Resolve the requirement: `uip tm requirements list --project-key <KEY> --filter <NAME> --output json` (`Id`).
2. Start and wait once: `generate-testcases --project-key <KEY> --requirement-id <ID> --wait --timeout 540 --output json`. Pass the user's focus as `--instructions "<TEXT>"`.
3. Show the numbered `Data.TestCases` (titles and steps) and ask which to keep, unless the user already said ("the first two", "all of them").
4. Create from **the same job**: `generate-testcases --project-key <KEY> --activity-id <ACTIVITY_ID> --create [--select <N> ...] --output json`. They are linked to the requirement and labelled `autopilot-generated`.

## Scenario 2 — "Is this requirement good enough?"

1. `evaluate --project-key <KEY> --requirement-id <ID> --wait --timeout 540 --output json` → `Data.Suggestions`. For each: `SuggestiveDescription` says what is missing, `ActionableDescription` is the text to add.
2. "More suggestions" re-runs **the same job**: `evaluate --project-key <KEY> --activity-id <ACTIVITY_ID> --more-suggestions --wait --timeout 540 --output json`. New ones are appended; `Data.Added` counts them.
3. `evaluate` changes nothing. To apply a suggestion, read the description with `requirements get`, then write the whole new text with `requirements update --requirement-id <ID> --description "<CURRENT_TEXT_PLUS_CHANGE>"`: `--description` replaces, it does not append.

## Scenario 3 — "Clean up test cases that no longer match"

1. `find-obsolete-testcases --project-key <KEY> --requirement-id <ID> --wait --timeout 540 --output json` → `Data.ObsoleteTestCases`.
2. Show each flag in plain words. Neither number is a probability:
   - `Score` 0–100: how obsolete. The AI adds points per problem: unrelated 40, partly relevant 15, technical errors up to 20, weak business value or coverage up to 15 each, hard to maintain or duplicated up to 10 each.
   - `ConfidenceLevel`: `High` = clear contradiction with the requirement; `Medium` = needed interpretation; `Low` = weak evidence, have the user review it.
   - The list is sorted by `ConfidenceLevel`, so `Number` 1 is the surest flag, not always the highest `Score`. "The clear ones" → select by confidence; "the most obsolete" → by score. Say which you used.
3. Act on **the same job**: `--activity-id <ACTIVITY_ID> --unlink [--select <N> ...]` takes them off the requirement and keeps them. `--delete --yes [--select <N> ...]` deletes them, only with the user's explicit go-ahead. Use `--unlink` when the user only wants them off the requirement.

## Scenario 4 — "The run timed out" or "check on that job later"

A wait that runs out exits **2** with `ErrorCode: timeout` and a `Message` ending `The job may still finish.`. The job is still running. Run the command its `Instructions` name (`<verb> --activity-id <ACTIVITY_ID> --wait --timeout 540`). Never start a new job. To check without waiting, drop `--wait`: `Data.Status` stays non-final (`InProgress`) until the result arrives.

## Rules

1. **One start per request.** Re-showing, waiting, creating, unlinking and deleting all reuse `--activity-id`. Never start again to "retry" a slow or cut-off call: it spends units and gives a different list.
2. **Bound every wait to your shell.** `--wait`, `--create`, `--unlink` and `--delete` block up to 600 s by default. Pass `--timeout 540` with a shell time limit of at least 600 s (Claude Code Bash `timeout: 600000`). If the shell cannot wait that long, start without `--wait` and check by id every ~30 s, at most 20 times.
3. **`CannotGenerateAdditionalAIArtifacts` is a result, not a failure.** `Result: Success`, an empty list, and a note: the existing test cases already cover the requirement, or nothing looks obsolete. Report it. Only new `--instructions`, `--attachment-ids` or requirement text can change it.
4. **A failed job's `Retry` decides.** `RetryWillNotFix` (`TokenLimitReached`, `TooManyImages`): the input is too large; ask the user to shorten the description or pass fewer attachments. `RetryLater` (`RateLimitReached`, `Expired`): tell the user and wait before one new start.
5. **An HTTP 400 at start means no job was started. Do not retry it, and do not follow its hint blindly.** `neither requirement description nor supporting documents are provided`: if the requirement has attachments (`uip tm attachment list --object-type requirement --object-ids <ID>`, ids in `Data[].AttachmentIds`), pass them with `--attachment-ids`; otherwise ask the user for a description. Never write one yourself. `no test cases are linked to the requirement`: tell the user; never link test cases just to make the search run.
6. **Never `--create` twice on one job.** The CLI cannot mark a job as used, so a second `--create` duplicates every test case. If an earlier output has `Data.Created`, it is done; to add one more, `--create --select` only that `Number`.
7. **The CLI only acts on flagged test cases still linked to the requirement.** Others are left alone under `Data.NotLinked` with a `Warning`. Report them; do not delete them another way. `Data.Skipped` and `Data.AlreadyDeleted` are already done. On a partial delete, retry only `Data.Failed`, once, with the command `Instructions` names.
8. **A 403 (`permission_denied`) on one AI verb is a tenant setting, not a login problem.** Each AI command has its own feature flag, licence check, AI Trust Layer policy and project permission (`find-obsolete-testcases` also needs Test Case edit rights), so a tenant can allow `evaluate` and refuse `find-obsolete-testcases`. Do not retry and do not re-login. Tell the user that this AI feature is not enabled for them on this tenant.
