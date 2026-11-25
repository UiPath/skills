# Draft Gate Reply

Read this file fully before writing the draft-mode approval-gate reply. The skeleton and loop are in [draft-skeleton.md](draft-skeleton.md), with resource lookup at [Find the resources](draft-skeleton.md#find-the-resources).

Use this exact shape and every line; only the first line's second sentence is optional, and the question and three options are fixed:

```text
<!--skill-flavor:gate-first-line:start-->
<Name>: outline ready<, uploaded> (draft mode). <One sentence if the upload or a lookup failed, the upload to an existing solution waits for the user's go-ahead, you kept the user's Studio Web edits, or you put the project in a new solution because the request named none, or the new solution took another name because its default was taken.>
<!--skill-flavor:gate-first-line:end-->
<!--skill-flavor:gate-path-line:start-->
<the Studio Web link (Data.DesignerUrl) on its own line when it uploaded, else the local <Project>/<Name>.bpmn path as plain text, never a link or in backticks>
<!--skill-flavor:gate-path-line:end-->

- <box label exactly as its .task() name spells it>: <resource and folder | which of two | none yet, create it or name one | not checked | no resource needed>

Is this the process you want?
1. **Build it**: make every step work.
2. **Change it**: tell me what to add, remove, or move.
3. **Keep it**: stop here with this outline.
```

<!--skill-flavor:gate-uploaded-rule:start-->
Write `, uploaded` only when this turn's upload succeeded.
<!--skill-flavor:gate-uploaded-rule:end-->

## Nothing before the first line

The final message begins immediately after the last tool call with `<Name>:` and contains only the gate reply. Write nothing before that line: not a status or validation sentence (`Valid`, `zero errors`, `Uploaded`, "Presenting the gate"), not an introduction ("Here is the outline:"), and not a `---` separator. When the request forbids upload, the one sentence never mentions the upload: no sentence that it was skipped, deferred or not performed. Include no progress; put lookup results on box lines and failures in the first line's sentence. Put progress before the last tool call; the next message contains only the gate reply.

## The path line

When the path line is the local path, write the plain path, such as InvoiceIntake/InvoiceIntake.bpmn, never a Markdown link, whatever its text, and never in backticks.

## The box lines

List every task box in order, including boxes needing no resource; exclude the start event, timer, gateway, and end event. Use each label exactly as its `.task()` name spells it, including any `→ variable` suffix; omit branch conditions, arm labels, and routes: `- Manager review [Action app]`, not `- Manager review [Action app] (amount 1000 or more)`. After `: ` write exactly one status: the resource name and folder; the two candidates plus the default *Build it* takes (`<A> in <folder> or <B> in <folder>, which one? Build it takes the first`, omitting ` in <folder>` when a row has no folder); or exactly `none yet, create it or name one`, `not checked`, or `no resource needed`. Keep each box to one short clause; omit element type ids, build-time plans, and alternatives for the kind.
<!--skill-flavor:gate-not-checked-rule:start-->
Write `not checked` only for a box whose lookup ran and failed, or when this run found no `uip login`; a box not looked up is not a reply line yet, so run its lookup first.
<!--skill-flavor:gate-not-checked-rule:end-->
Explain each lookup failure once, in the first line's sentence, never on its box line.

## Nothing else

Do not restate the shape. Send no `Flow:` or `The shape:` line, diagram, code block, gateway/condition/variable line, table, heading, or step log. Do not explain validation warnings or defaults except in the first line's sentence, ask no question of your own, and put decisions on *Change it*. Put each which-of-two resource question, including the default *Build it* choice, on its box line. Compare the reply line by line with the template and delete every non-template line.

## End the turn

Send this reply only when, in this or the resumed interrupted turn, `validate` reported `Status: Valid` on the target `.bpmn`, and the target contains `id="<id>"` for every box's `.task()` id, including any element the user retyped it to; `merge`'s counts cannot establish this. On a *Change it* round, also verify that each changed box's `name` attribute, decoded (`compile` writes `&` as `&amp;`) equals its new `.task()` name.
<!--skill-flavor:gate-retry:start-->
When a box is missing, run the [Steps](draft-skeleton.md#steps) loop into the target once more (upload again when this turn uploaded) and search again; when one is still missing, send no gate reply and tell the user in one sentence that the outline did not reach the process file.
<!--skill-flavor:gate-retry:end-->
Send this reply as the final message and end the turn. If a turn carries no new user instruction and only resumes after an interruption following this reply, resend that reply unchanged and whole as the final message; a new user message starts a normal turn. Ask the gate question in the message, not with a pick-list or question tool: the pending question keeps the turn open, and Studio Web locks the canvas while a turn runs, preventing review. The user answers next with a number, option name, or requested change. Never leave the outline only in reasoning; the user must see the shape and question.
