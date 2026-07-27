---
confidence: medium
---

# Could Not Retrieve Result — Output Too Large / Malformed Output Arguments

## Context

A job runs to the end of its workflow but faults at the very last step because the executor cannot return its result to Orchestrator: the `OutputArguments` payload is too large (or non-serializable) for the result message channel. The work often completed — only the hand-back failed.

What this looks like:
- `Could not retrieve the result of the job execution. This might be because a message was too large to process.`
- Job state Faulted, but `jobs traces` shows every activity Succeeded and the workflow reached its end
- `OutputArguments` on `jobs get` is empty, truncated, or malformed
- More likely on processes that return bulk data (DataTables, byte arrays, large strings/JSON) as output arguments

What can cause it:
- A large `DataTable`, `List`, byte[]/file content, or big string/JSON returned as an **OutputArgument** — the result message exceeds the channel limit
- A non-serializable or cyclic object set as an output argument
- (Also a Robot defect on some older versions that was later fixed — version-sensitive)

What to look for:
- The process's declared output arguments (`project.json` `entryPoints[].output`, or the Main workflow's `Out_*` arguments) — is any of them a bulk type?
- `jobs traces`: did the workflow actually finish? (If yes, the failure is result hand-back, not workflow logic.)
- Whether the same process succeeds when its output payload is small (few rows) and fails when large

## Investigation

1. Get the failing job and read `Info` + `OutputArguments`:
   `uip or jobs get <job-key> --output json` — the `Info` names the result-retrieval failure; `OutputArguments` is empty/truncated.
2. Confirm the workflow actually completed (distinguishes hand-back failure from a mid-run fault):
   `uip or jobs traces <job-key> --output json` — all activities Succeeded, execution reached the end.
3. Read logs for the point of failure:
   `uip or jobs logs <job-key> --level Error --output json` — work-complete logs followed by the result-retrieval error.
4. Inspect the process output-argument definition in the project source: `project.json` `entryPoints[].output` (or the Main `.xaml` `Out_*` arguments). Identify the bulk output argument.

## Resolution

- **Move bulk data out of output arguments.** Do not return large DataTables, collections, files, or big JSON/strings as `OutputArguments`. Instead write the payload to a **Storage Bucket**, **Queue**, or **Data Fabric** entity inside the workflow and return only a small **reference** (bucket key, file path, queue reference, or record ID) as the output argument. The parent/caller reads the payload from that reference.
- **Trim or paginate** the returned data if a reference pattern is not viable — return only the fields/rows the caller needs.
- **Ensure output types are serializable** — replace non-serializable/cyclic objects with plain DTOs or a serialized reference.
- **Update the Robot** to a current version if the payload is genuinely small (rules in the version-specific known-issue path), then rerun.
- **Rerun** the job after applying the fix.

Prevention:
- Treat `OutputArguments` as a control channel, not a data channel — pass references, not payloads.
- Cap output-argument size in design review; route bulk results through storage/queues.
