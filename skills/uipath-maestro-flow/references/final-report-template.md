# Final report — the end of every build

Every build ends its turn with this report: a plain request to build or edit a flow (`auto mode`), and *Build it* after a [draft gate](draft-skeleton.md#after-the-answer).
The skeleton's own gate reply is a different template ([gate reply](gate-reply-template.md)).
Read this file in full once `validate` passes, or fails only because tenant resources are missing, before any upload or other closing tool call.
When the request already named the next step (*publish it*, *debug it*), do it first, as [operate.md](operate.md) says, and report its result here.

## Upload the built flow

<!--skill-flavor:final-upload:start-->
Upload only when the request asks for it, or after a draft gate that uploaded.
Then run the [refresh](operate.md#refresh-solution-resources-first) and `uip solution upload "<SolutionDir>" --output json`. The returned `Data.DesignerUrl` goes on the path line.
When this run did not create the solution, the upload first needs the user's consent: a request to upload or publish that solution counts. When that consent is missing, do not ask in this reply: skip the upload and say in the first line's one sentence that it waits for the user's go-ahead.
After a draft gate that uploaded, download the cloud copy and compare it again before the upload, as [After the answer](draft-skeleton.md#after-the-answer) says.
When that check fails for a reason other than a missing cloud copy, retry once. When it still fails, skip the upload and say in the first line's one sentence that the Studio Web copy could not be checked, so nothing was uploaded.
<!--skill-flavor:final-upload:end-->

## The reply

Reply in this shape, dropping lines that do not apply:

```text
<!--skill-flavor:final-first-line:start-->
<Name>: built, validated<, uploaded><, run> (<draft|auto> mode). <One sentence when this file calls for it, or when you kept the user's Studio Web edits.>
<!--skill-flavor:final-first-line:end-->
<!--skill-flavor:final-path-line:start-->
<Data.DesignerUrl on its own line when the upload returned one, else the plain local <Project>/<Name>.flow path, never a link or in backticks>
<!--skill-flavor:final-path-line:end-->

- <what changed, one line each, at most 5 lines in all>

Needs: <...>
Assumed: <...>  Unverified: <...>
```

The first line names the mode as literal text, in place of `<draft|auto>`.
Write `(draft mode)` for any run that stopped at a draft gate, including after *Build it*. Write `(auto mode)` only in a run that never stopped at a gate.
Never write `(auto mode)` after a draft gate.
<!--skill-flavor:final-status-rule:start-->
Write `, uploaded` only when this turn's upload succeeded. Write `, run` only when this turn ran the flow with the user's consent and it ended `Completed`.
When the upload failed, or a run failed or timed out, say so in the first line's one sentence.
<!--skill-flavor:final-status-rule:end-->
<!--skill-flavor:final-open-file-extra:start-->

<!--skill-flavor:final-open-file-extra:end-->

When a tenant resource is missing (no connection, agent, process or queue to bind), even when `validate` passes, the first line writes `not runnable yet` in place of `validated`.
Drop `Needs:` when nothing is missing.

The three closing lines replace the open-question list that other files name:

- `Needs:` each missing tenant resource in the user's words (`a Slack connection`, `the ticket triage agent`), and each `mock()` still in the flow with the capability it stands for. A **[REQUIRED]** item that is a missing tenant resource goes here, not under `Assumed:`.
- `Assumed:` each value you picked that the request left open, and each connection `prepare` or a guess chose, with its folder ([bindings.md](bindings.md#where-both-values-come-from)). `[OPTIONAL]` items go here too, or are dropped when they change nothing. Mark an entry **[REQUIRED]** when [SKILL.md](../SKILL.md#critical-rules) rule 4, [author.md](author.md) rule 8 or a guessed connection says the user must confirm it. A solution you created because the request named none goes here too.
- `Unverified:` what no check proved: `validate` checks structure only, a run you did not make, and each `Data.Warnings` entry you accepted, with its reason.

Report each accepted warning as one clause in the user's words that names its step or input. No warning codes, and no word about warnings anywhere else in the reply.

<!--skill-flavor:final-path-rule:start-->
The path line belongs to this final message.
A Studio Web link shown earlier in the turn, before a tool call, does not count: write it again here, on its own line.
When the path line is the local path, write the plain path, such as InvoiceIntake/InvoiceIntake/InvoiceIntake.flow, not a Markdown link and not in backticks.
The path line, link or path, is flush-left: no space or indent before it.
<!--skill-flavor:final-path-rule:end-->

Write every line in the user's words: say what each step now does.
Write no node type ids (`uipath.core.agent.<key>`), connector keys, object or operation names, binding or placeholder terms, and no file names other than the path line.

This reply is your whole final message. Its first characters are the flow name: write no status sentence or introduction before the `<Name>:` line.
When a turn carries no new user instruction and only resumes after an interruption that came after you wrote this report, send that report again, unchanged and whole, as this turn's final message. Any new user message is a normal turn.
Send nothing beyond these lines: no extra sections, headings, tables, numbered lists, questions or suggested next steps.
**Write at most five change lines. A sixth line is a defect, not a judgment call.**
Count the `-` change lines before you send. When there are more than five, merge related steps into one line each, and fold anything else the user must act on into `Needs:`, `Assumed:` or `Unverified:`.
Before sending, check the message against the template line by line and delete every line the template does not have.
