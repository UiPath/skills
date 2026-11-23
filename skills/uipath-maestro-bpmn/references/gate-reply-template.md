# Draft Gate Reply

The reply that ends a draft-mode turn at the approval gate. Read this file in full before you write that reply; the skeleton and its loop are in [draft-skeleton.md](draft-skeleton.md), and the resource lookup in its [Find the resources](draft-skeleton.md#find-the-resources).

Reply in this shape and keep every line; only the first line's second sentence is optional, and the question and its three options are fixed:

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

This reply is your whole final message, and its first characters are the process name.
When your last tool call returns, do not comment on its result: your next words are the `<Name>:` line.
Write nothing before that line: not a status or validation sentence (`Valid`, `zero errors`, `Uploaded`, "Presenting the gate"), not an introduction ("Here is the outline:"), and not a `---` separator.
What a lookup found goes on the box lines, and why it failed goes in the first line's one sentence; steps you ran or skipped are not reported at all, except what the first line's one sentence carries.
When the request forbids upload, the one sentence never mentions the upload: no sentence that it was skipped, deferred or not performed.
A progress note belongs in a message before your last tool call; the message after it holds the gate reply and nothing else.

## The path line

When the path line is the local path, write the plain path, such as InvoiceIntake/InvoiceIntake.bpmn, never a Markdown link, whatever its text, and never in backticks.

## The box lines

List every task box, in order, including a box that needs no resource, and nothing else: not the start event, a timer, a gateway or the end event.
A box line is the box's label exactly as its `.task()` name spells it, `→ variable` suffix included, and never a branch condition, an arm label or a route: `- Manager review [Action app]`, not `- Manager review [Action app] (amount 1000 or more)`.
After the label, write `: ` and exactly one status: the resource's name with its folder, the two candidates and the default *Build it* takes (`<A> in <folder> or <B> in <folder>, which one? Build it takes the first`, leaving out ` in <folder>` for a row with no folder name), or one of the fixed phrases `none yet, create it or name one`, `not checked` and `no resource needed`, word for word.
Give each box one short clause (the which-of-two status is the one two-part form): no element type ids, no build-time plans, and no alternatives for the kind.
<!--skill-flavor:gate-not-checked-rule:start-->
Write `not checked` only for a box whose lookup ran and failed, or when this run found no `uip login`; a box you have not looked up is not a reply line yet, so run its lookup first.
<!--skill-flavor:gate-not-checked-rule:end-->
When a lookup failed, say why once, in the first line's one sentence, not on the box lines.

## Nothing else

Do not describe the shape in any other form.
Send no `Flow:` or `The shape:` line, no drawn diagram or code block, no line about a gateway, its condition or the variable it reads, no table, no heading and no step log.
The canvas, or the box lines when there is no upload, already shows the shape, and Autopilot's chat panel is narrow: anything extra pushes the question out of view.
That also rules out an explanation of a validation warning, a note about a default you chose (beyond the first line's one sentence), and a question of your own (a time zone, which app); anything the user should settle waits for *Change it*.
A which-of-two resource question, with the default *Build it* takes, is the exception: it goes on its box line, in this same message.

Before you send it, compare the message with the template line by line and delete every line the template does not have.

## End the turn

Send this reply only when, in this turn or the interrupted turn it resumes, `validate` reported `Status: Valid` on the target `.bpmn` and the target contains `id="<id>"` for every box's `.task()` id, on whatever element the user may have retyped it to; `merge`'s counts cannot show this.
On a *Change it* round, also check that each changed box's `name` attribute, decoded (`compile` writes `&` as `&amp;`), equals its new `.task()` name.
<!--skill-flavor:gate-retry:start-->
When a box is missing, run the [Steps](draft-skeleton.md#steps) loop into the target once more (upload again when this turn uploaded) and search again; when one is still missing, send no gate reply and tell the user in one sentence that the outline did not reach the process file.
<!--skill-flavor:gate-retry:end-->
Send this reply as your final message and end the turn.
When a turn carries no new user instruction and only resumes after an interruption that came after you wrote this reply, send that reply again, unchanged and whole, as this turn's final message; any new user message is a normal turn.
Ask the gate question in the message, not with a pick-list or question tool: a pending question keeps the turn open, and Studio Web locks the canvas while a turn runs, so the user could not review the shape they are asked to approve.
The user answers in their next message, with a number, an option name, or the change they want.
Never leave the outline only in your reasoning: a user who sees only the question cannot judge the shape.
