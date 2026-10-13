# Requirement AI — generate test cases, evaluate, find obsolete test cases

Test Manager's AI reads a requirement (its description and any attachments you name) and does one of three jobs:

| Command | What the AI does | Changes anything? |
|---|---|---|
| `uip tm requirements generate-testcases` | Proposes new test cases, each with steps | Only with `--create`: creates them, links them to the requirement, labels them `autopilot-generated` |
| `uip tm requirements evaluate` | Reviews the requirement's quality and suggests improvements | Never. Apply a suggestion yourself with `uip tm requirements update` |
| `uip tm requirements find-obsolete-testcases` | Flags test cases linked to the requirement that no longer match it | Only with `--unlink` (removes the link, keeps the test case) or `--delete --yes` (deletes the test case) |

Each command runs as a **background job** on the server. A job has an **activity id** (`ActivityId`). You start a job once, then follow it by that id with the same command. A job usually takes 1–5 min, and a generate job can propose dozens of test cases. **Every start creates a new job and spends the tenant's AI units**; reading a job by its id costs nothing.

All commands take `--output json` and `--project-key <KEY>` (or `--project-id`). Name the requirement with `--requirement-id <UUID>` or `--requirement-key <KEY:N>` (exactly one). Find either with `uip tm requirements list --project-key <KEY> --filter <NAME> --output json` (`Id`, `ObjKey`).

The AI commands need a **user** login. Test Manager runs each job for the user who started it, so an app (client-credentials) login fails with a server error. If `uip login status --output json` shows `"IdentityType": "Application"`, stop and ask the user to sign in as a user with `uip login`.

## Starting and following a job

| Goal | Command |
|---|---|
| Start a job and return at once | `<command> --project-key <KEY> --requirement-id <UUID>` → `Data.ActivityId` |
| Start a job and wait for its result | add `--wait --timeout 540` |
| Check a job once (no waiting) | `<command> --project-key <KEY> --activity-id <ACTIVITY_ID>` → `Data.Status`, plus the result once the job has finished |
| Wait for a job that is already running | `<command> --project-key <KEY> --activity-id <ACTIVITY_ID> --wait --timeout 540` |

`<command>` is the same verb that started the job: an `evaluate` id only works with `evaluate`. With `--activity-id`, the requirement comes from the job, so leave out `--requirement-id`/`--requirement-key`, `--instructions` and `--attachment-ids` (the CLI rejects the last two). Pass the same project the job ran in: an id from another project fails with `not_found`.

Optional inputs on a start: `--instructions "<TEXT>"` (extra guidance, such as "focus on negative paths") and `--attachment-ids <UUID...>` (space-separated). The attachment ids must belong to the requirement: get them with `uip tm attachment list --project-key <KEY> --object-type requirement --object-ids <REQUIREMENT_ID> --output json` (the ids are in `Data[].AttachmentIds`). The CLI checks them before it starts a job, so a wrong id costs no AI units.

Job statuses: `InProgress` and other non-final values mean "still running". `Processed` is a result. `CannotGenerateAdditionalAIArtifacts` is also a result: the AI worked and found nothing (see rule 5). `Failed`, `Expired`, `RateLimitReached`, `TokenLimitReached` and `TooManyImages` are failures (see rule 6).

## Per command

### generate-testcases

| Goal | Command |
|---|---|
| See the proposed test cases | `uip tm requirements generate-testcases --project-key <KEY> --requirement-id <UUID> --wait --timeout 540 --output json` → `Data.TestCases[]` ([fields](#what-the-result-fields-mean)) |
| Create all of them, linked to the requirement | `uip tm requirements generate-testcases --project-key <KEY> --requirement-id <UUID> --create --timeout 540 --output json` → `Data.Created` |
| Create some of them from a job you already ran | `uip tm requirements generate-testcases --project-key <KEY> --activity-id <ACTIVITY_ID> --create --select <N> [<N> ...] --output json` → `Data.Created`, `Data.Selected` |

`--create` waits on its own. `--select` takes the `Number`s from `Data.TestCases` and needs `--create`. Test cases the web app already created from the job are skipped and listed under `Data.Skipped`.

### evaluate

| Goal | Command |
|---|---|
| Get suggestions | `uip tm requirements evaluate --project-key <KEY> --requirement-id <UUID> --wait --timeout 540 --output json` → `Data.Suggestions[]` ([fields](#what-the-result-fields-mean)) |
| Get more suggestions on top of a finished evaluation | `uip tm requirements evaluate --project-key <KEY> --activity-id <ACTIVITY_ID> --more-suggestions --wait --timeout 540 --output json` → the earlier suggestions plus new ones; `Data.Added` counts the new ones |
| Apply a suggestion | Read the current description with `uip tm requirements get --project-key <KEY> --requirement-id <UUID> --output json`, then `uip tm requirements update --project-key <KEY> --requirement-id <UUID> --description "<CURRENT_DESCRIPTION_WITH_THE_CHANGE>" --output json` |

`--more-suggestions` re-runs the same job with the same inputs (it spends AI units) and keeps the same `ActivityId`. It is refused while that job is still running: wait for it first. `update --description` replaces the whole description, so build the new text from the current one.

### find-obsolete-testcases

| Goal | Command |
|---|---|
| See which linked test cases look obsolete | `uip tm requirements find-obsolete-testcases --project-key <KEY> --requirement-id <UUID> --wait --timeout 540 --output json` → `Data.ObsoleteTestCases[]` ([fields](#what-the-result-fields-mean)) |
| Unlink flagged test cases (keep them) | `uip tm requirements find-obsolete-testcases --project-key <KEY> --activity-id <ACTIVITY_ID> --unlink [--select <N> ...] --output json` → `Data.Unlinked` (the `Number`s unlinked) |
| Delete flagged test cases | `uip tm requirements find-obsolete-testcases --project-key <KEY> --activity-id <ACTIVITY_ID> --delete --yes [--select <N> ...] --output json` → `Data.Deleted`, `Data.AlreadyDeleted`, and on a partial failure `Data.Failed` |

`--unlink` and `--delete` wait on their own and are mutually exclusive. `--select` takes the `Number`s from `Data.ObsoleteTestCases`. You can also pass `--unlink` or `--delete --yes` on a start (`--requirement-id …`) to search and act in one call, but only when the user asked to act on whatever the AI flags without seeing it first.

## What the result fields mean

Explain these to the user in plain words when you show a result. Do not present `Score` or `ConfidenceLevel` as a probability.

**Proposed test cases (`Data.TestCases[]`, generate-testcases)**

| Field | Meaning |
|---|---|
| `Number` | Position in the job's list, starting at 1. Stable for that job; `--select` takes it |
| `Title`, `Description` | Become the new test case's name and description |
| `Steps[]` | Manual steps, each an `Action` and its expected `Result` |
| `Precondition`, `Postcondition` | State before and after the test |
| `Labels` | Labels the AI suggests. `--create` applies them and adds `autopilot-generated` to every test case it creates |
| `Properties` | Custom-field values the AI filled in, by field name; `--create` writes them to the new test case |
| `IsTestCaseCreated` | `true` once the web app created this test case from the job. `--create` skips it (`Data.Skipped`). The CLI does not set it |

**Suggestions (`Data.Suggestions[]`, evaluate)**

| Field | Meaning |
|---|---|
| `Title` | The improvement in a few words |
| `SuggestiveDescription` | What the requirement lacks, usually with an example |
| `ActionableDescription` | The concrete change to make; the text to add when you apply the suggestion |
| `State` | Where the user is in the web app: `TODO` (new), `INWORK` (being worked on), `DONE`. The CLI only reads it |

**Flagged test cases (`Data.ObsoleteTestCases[]`, find-obsolete-testcases)**

| Field | Meaning |
|---|---|
| `Number` | Position in the list, starting at 1; `--select` takes it. The list is sorted by `ConfidenceLevel`, `High` first, so `1` is the most certain flag, not always the highest `Score` |
| `TestCaseId`, `TestCaseKey`, `Name` | The flagged test case |
| `Score` | How obsolete the test case looks, 0–100, higher is more obsolete. The AI adds points per problem found: unrelated to the requirement 40, only partly relevant 15, technical errors or gaps up to 20, weak business value up to 15, weak coverage or efficiency up to 15, hard to maintain up to 10, duplicated by another test case up to 10 |
| `ConfidenceLevel` | How sure the AI is that the flag is right: `High` (clear evidence, the test case contradicts the requirement), `Medium` (good evidence that needed some interpretation), `Low` (weak evidence or an unclear requirement; review before acting) |
| `Criteria` | The problems found, named after the scoring categories, for example `Completely Unrelated`, `Partially Relevant`, `Technical Inconsistencies`, `Complete Subset` |
| `Summary` | The AI's reason and recommended action in 2–3 sentences; for a duplicate it names the covering test case as `Name (ObjKey)` |
| `IsDeleted` | `true` once the test case was deleted through the web app from this job's result. `--unlink`/`--delete` skip it (`Data.Skipped`). A delete through the CLI does not set it |

`Score` and `ConfidenceLevel` are separate: a low score can come with `High` confidence and the reverse. When the user asks for "the clear ones", select by `ConfidenceLevel`; when they ask for "the most obsolete", select by `Score`. Say which you used.

## Rules that save AI units and data

1. **Start each job once. To see, wait for, or act on its result again, reuse its `--activity-id`.** Never run a second start for the same request, not even to "retry" a slow or cut-off call. Every start creates a new job and spends AI units, and its results differ from the first job's. Keep every `ActivityId` the CLI prints.
2. **Bound every waiting call to fit inside your shell's time limit.** `--wait`, `--create`, `--unlink`, `--delete` and `--more-suggestions --wait` block until the job ends, by default for up to 600 s. Pass `--timeout 540` and give the shell call a time limit of at least 600 s (for example Claude Code Bash `timeout: 600000`, Codex `timeout_ms: 600000`). If your shell cannot wait that long, start without `--wait`, then check the job with `--activity-id <ACTIVITY_ID>` (no `--wait`) about every 30 s, at most 20 times.
3. **A timeout is not a failure of the job. Resume it, do not restart it.** When the wait runs out, the CLI exits with code 2, `ErrorCode` `timeout`, a `Message` that ends `The job may still finish.`, and `Instructions` naming the command with `--activity-id <ACTIVITY_ID> --wait`. Run that command; it reads the same job. Do the same when a waiting call was cut off by your shell: rerun it with `--activity-id`, never as a new start.
4. **Show the proposed result before you act on it, unless the user already told you what to act on.** Run with `--wait` first, show the numbered list, and then act on the same job with `--activity-id <ACTIVITY_ID>` plus `--create`, `--unlink` or `--delete --yes`, adding `--select` for the numbers the user chose. When the user asks for only some items ("the first two", "the High-confidence ones"), pick them by `Number` from the list and pass `--select`.
5. **`CannotGenerateAdditionalAIArtifacts` means "nothing found", and it is a success.** The output has `Result: Success`, an empty list and an `Instructions` note (for generate: the existing test cases already cover the requirement; for find-obsolete: no test case looks obsolete). Report that to the user. Do not start the job again with the same inputs; only a change to `--instructions`, `--attachment-ids` or the requirement can give a different answer.
6. **A failed job's `Retry` field decides what to do next.** (A timeout is not a failed job; it follows rule 3.) `RetryWillNotFix` (for example `TokenLimitReached`, `TooManyImages`): running it again with the same inputs fails the same way; tell the user to shorten the description or pass fewer attachments. `RetryLater` (for example `RateLimitReached`, `Expired`): tell the user and wait before one new start; do not loop. Any other failure stops under Critical Rule 10.
7. **A start that fails with HTTP 400 started no job. Fix the cause or ask; do not retry it.**
   - `Unable to generate tests as neither requirement description nor supporting documents are provided` (and the `evaluate`/`find obsolete` equivalents): the requirement has no description and you passed no attachments. If it has attachments, pass their ids with `--attachment-ids`. Otherwise ask the user for a description; do not write one yourself.
   - `Unable to find obsolete tests as no test cases are linked to the requirement`: there is nothing to review. Tell the user; do not link test cases just to make the search run.
8. **Delete only with the user's explicit go-ahead, and always with `--yes`.** `--delete` without `--yes` exits before any job starts. Deleted test cases cannot be restored. When the user only wants the test cases off the requirement, use `--unlink`: it keeps them.
9. **Never run `--create` twice on the same job.** The CLI cannot mark a job as used, so a second `--create` on the same `ActivityId` creates every test case again. Before creating, check whether an earlier run already did: its output has `Data.Created`, or the requirement's linked test cases (`uip tm requirements list-testcase-ids --project-key <KEY> --requirement-id <UUID> --output json`) already include them. To add a test case you skipped, run `--create --select` with only that `Number`.
10. **The CLI acts only on flagged test cases that are still linked to the requirement.** The AI's reply names the test cases, so before `--unlink` or `--delete` the CLI checks them against the requirement's current links. A flagged test case that is no longer linked is left alone, listed under `Data.NotLinked`, with a `Warning`. Report it; do not delete it some other way. `Data.Skipped` lists flagged test cases already marked deleted, and `Data.AlreadyDeleted` lists ones that were gone when the CLI tried to delete them. Both are done; neither needs a retry.
11. **On a partial delete failure, retry only the failed numbers.** `Data.Deleted` lists what is gone and `Data.Failed` what is not; the `Instructions` name the command with `--select` set to the failed numbers. Run that once. If it fails again, stop under Critical Rule 10.
12. **The AI's wording changes between runs.** Do not promise the user specific test cases or suggestions before the job finishes, and do not compare two runs' lists by title.
