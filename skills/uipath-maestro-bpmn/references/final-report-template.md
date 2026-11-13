# Final report — the end of every build

Every build ends its turn with this report: a plain request to build or edit a process, and *Build it* after a [draft gate](draft-skeleton.md#after-the-answer).
The skeleton's own gate reply is a different template ([gate reply](draft-skeleton.md#show-the-shape-and-stop)).

## Upload the built process

<!--skill-flavor:final-upload:start-->
When the built process validates, the request allows an upload and the project has a solution (`.uipx`), run the [pre-flight](operate.md#pre-flight-before-any-cloud-action), which also stops the upload while a connector's enrichment is unresolved, then `uip solution upload <SolutionDir> --output json` returns the `Data.DesignerUrl`.
When this run did not create the solution (neither its `uip solution init` nor its `bpmn init` made it), the upload first needs the user's confirmation and the [cloud-copy check](operate.md#check-the-cloud-copy-before-editing).
When the confirmation is missing, do not ask in this reply: skip the upload and say in the first line's one sentence that it waits for the user's go-ahead.
When the cloud-copy check fails for a reason other than a missing cloud copy (offline, not logged in, a timeout), retry the download before the upload.
When it still fails, skip the upload even if the user already allowed it, and say in the first line's one sentence that the Studio Web copy could not be checked, so nothing was uploaded, and that uploading would replace it unseen.
When the confirmation is also missing, this sentence replaces the go-ahead one: the go-ahead the user gives after it is also the consent to replace the copy.
Only a go-ahead given after the user was told the check failed allows that replacement; consent to upload given before does not.
When the request forbids upload, or there is no solution, skip it.
<!--skill-flavor:final-upload:end-->

## The reply

Reply in this shape, dropping lines that do not apply:

```text
<!--skill-flavor:final-first-line:start-->
<Name>: built, validated<, uploaded><, run> (<draft|auto> mode). <One sentence when this file calls for it, or when you kept the user's Studio Web edits.>
<!--skill-flavor:final-first-line:end-->
<!--skill-flavor:final-path-line:start-->
<the Studio Web link (Data.DesignerUrl) on its own line when the upload returned one, else the local <Project>/<Name>.bpmn path as plain text, never a link>
<!--skill-flavor:final-path-line:end-->

- <what changed, one line each, at most 5 lines in all>

Needs: <...>
Assumed: <...>  Unverified: <...>
```

The first line names the mode as literal text, in place of `<draft|auto>`.
Write `(draft mode)` for any run that stopped at a draft gate, including after *Build it*, and write `(auto mode)` only in a run that never stopped at a gate.
Never write `(auto mode)` after a draft gate.
Write `, uploaded` only when this turn's upload succeeded, and `, run` only when this turn ran the process with the user's consent.
When the upload failed, say so in the first line's one sentence.

When validation fails only because tenant resources are missing (no connection, agent, process or queue to bind), the first line reads `<Name>: built, not runnable yet (<draft|auto> mode).` and `Needs:` names each missing resource in the user's words, such as `a Slack connection` or `the ticket triage agent`.
Drop `Needs:` when nothing is missing.

The path line belongs to this final message.
A Studio Web link shown earlier in the turn, before a tool call, does not count: write it again here, on its own line.
When the path line is the local path, write the plain path, such as `InvoiceIntake/InvoiceIntake.bpmn`, not a Markdown link with the file name as its text.

Write every line in the user's words: say what each step now does.
No element type ids (`Orchestrator.StartAgentJob`), connector keys, object or operation names, payload, binding or placeholder terms, and no file names other than the path line.

This reply is your whole final message, and its first characters are the process name: write no status sentence or introduction before the `<Name>:` line.
Send nothing beyond these lines: no extra sections, headings, tables, numbered lists, questions or suggested next steps.
**Write at most five change lines. A sixth line is a defect, not a judgment call.**
Count the `-` change lines before you send: when there are more than five, merge related steps into one line each, and fold anything else the user must act on into `Needs`, `Assumed` or `Unverified`.
Before sending, check the message against the template line by line and delete every line the template does not have.
