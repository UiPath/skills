# Final report — the end of every build

Every build ends its turn with this report: a plain request to build or edit a process, and *Build it* after a [draft gate](draft-skeleton.md#after-the-answer).
The skeleton's own gate reply is a different template ([gate reply](draft-skeleton.md#show-the-shape-and-stop)).

## Upload the built process

<!--skill-flavor:final-upload:start-->
When the built process validates, upload it unless the request forbids upload or the project has no solution (the project is not registered in a `.uipx` in its directory or a parent: `init` ran with `--skip-solution-registration`, or with `--path` outside any solution).
Run the [pre-flight](operate.md#pre-flight-before-any-cloud-action) first, with the Studio Web upload as its target; then `uip solution upload <SolutionDir> --output json` returns the `Data.DesignerUrl`.
Do not ask first when this run's `init` scaffolded the solution: the request to build the process authorizes the upload that shows it ([Studio Web upload](operate.md#studio-web-upload)).
Upload when the solution already existed or an existing project was edited in place only if the user confirmed an upload earlier in this run, such as before the skeleton's upload; ask once per run.
An explicit request in this run to upload or publish to Studio Web counts as that confirmation, once the cloud-copy check before the edit succeeded or returned a 404 (no cloud copy yet).
When no confirmation was given in this run (none was asked for, none was requested, or the user declined), do not stop to ask: skip the upload, write the local path, and say in the first line's one sentence that the upload waits for the user's go-ahead, and that it would replace the Studio Web copy when the check found one.
When a cloud-copy check applied, it ran before the edit ([Check the cloud copy](operate.md#check-the-cloud-copy-before-editing)); do not compare it with the built file before uploading, because the two always differ.
When that check failed for a reason other than a 404 and the user has not said to replace the Studio Web copy, do not upload: write the local path, and say in the first line's one sentence that nothing was uploaded because the Studio Web copy could not be checked.
Do not upload a process that is not ready: when a connector's enrichment or a binding is still unresolved, do not upload ([Operate](operate.md#anti-patterns)).
When you skip the upload because there is no solution, do not create one to show the process.
<!--skill-flavor:final-upload:end-->

## The reply

Reply in this shape, dropping lines that do not apply:

```text
<!--skill-flavor:final-first-line:start-->
<Name>: built, validated<, uploaded><, run> (<draft|auto> mode). <One sentence when a rule in this file calls for it.>
<!--skill-flavor:final-first-line:end-->
<!--skill-flavor:final-path-line:start-->
<the Studio Web link (Data.DesignerUrl) on its own line when it uploaded, else the local <Project>/<Name>.bpmn path as plain text, never a link>
<!--skill-flavor:final-path-line:end-->

- <what changed, one line each, at most 5 lines in all>

Needs: <...>
Assumed: <...>  Unverified: <...>
```

The first line names the mode as literal text, in place of `<draft|auto>`.
Write `(draft mode)` for any run that stopped at a draft gate, including after *Build it*, and write `(auto mode)` only in a run that never stopped at a gate.
Never write `(auto mode)` after a draft gate.
Write `, uploaded` only when this turn's upload succeeded, and `, run` only when this turn ran the process with the user's consent.
When the pre-flight or the upload fails, write the local path on the path line and say in the first line's one sentence that the process is not in Studio Web yet.
When the upload succeeds but returns no `Data.DesignerUrl`, write the local path on the path line and say in that sentence that Studio Web returned no link.
When you kept the user's Studio Web edits, say so in that sentence; when more than one of these applies, say them all in that one sentence.
Never write `validated` for a process that did not validate.

When validation fails only because tenant resources are missing (no connection, agent, process or queue to bind), the first line reads `<Name>: built, not runnable yet (<draft|auto> mode).` and `Needs:` names each missing resource in the user's words, such as `a Slack connection` or `the ticket triage agent`.
When validation still fails for another reason, the first line reads `<Name>: built, not valid yet (<draft|auto> mode).` and `Needs:` names what still fails, in the user's words.
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
