# 3c Gate Reply

The reply that ends a draft-mode run at the 3c gate. Read this file in full
before you write that reply; the 3c lookup rules are in
[phase-2-skeleton-guide.md](phase-2-skeleton-guide.md#iterating).

Reply in this shape, dropping lines that do not apply; the question and
its three options are fixed:

```text
<!--skill-flavor:gate-first-line:start-->
<Name>: outline ready<, uploaded> (draft mode). <One sentence if a lookup failed or you kept the user's online changes.>
<!--skill-flavor:gate-first-line:end-->
<!--skill-flavor:gate-path-line:start-->
<DesignerUrl as a link on its own line, or the local .bpmn path as plain text, never a link>
<!--skill-flavor:gate-path-line:end-->

- <box label exactly as in the .bpmn, [kind] included>: <resource and folder | which of two | none yet, create it or name one | not checked | no resource needed>

<!--skill-flavor:gate-question:start-->
Is this the process you want?
<!--skill-flavor:gate-question:end-->
1. **Build it**: make every step work.
2. **Change it**: tell me what to add, remove, or move.
3. **Keep it**: stop here with this outline.
```

This reply is your whole final message, and its first characters are the
process name: no sentence about which skill you are using, no diagram. When the lookup call returns, do not comment on its result:
your next words are the `<Name>:` line. Write nothing before that line:
not a status sentence ("Valid, zero errors", "Lookups complete", "No
matching processes found", "Presenting the gate"), not an introduction
("Here is the outline:"), not a `---` separator. What a lookup found goes
on the box lines, and why it failed goes in the first line's one
sentence; steps you ran or skipped are not reported at all. A progress
note belongs in a message before your last tool call; the message after
it holds the 3c reply and nothing else.

Give every task box its own line, in order, including a script step that
needs no resource (`no resource needed`): the box
lines are the outline, so a box left off is a step the user never sees.
List task boxes only, never the start event, a timer, a gateway, or the
end event. Copy each box's `name` from the `.bpmn` as written, including its
`[kind]`: do not reword it or append the branch condition that leads to it.
After the colon, write one of the template's statuses word for word: the
resource and its folder, the two candidates to choose between, `none yet,
create it or name one`, `not checked`, or `no resource needed`. Never reword
a fixed status ("no matching app", "choose the orders system"), and add
no element type ids, no
phase-4 plans, no alternatives for the kind. When a lookup failed, say why
once, in the one sentence the first line allows, not on the box lines.

Do not describe the shape in any other form. Send no `Flow:` or
`The shape:` line, no drawn diagram or code block, no line about a
gateway, its condition, or the variable it reads, no table, and no
heading. The canvas, or the box lines when there is no upload, already
show the shape, and Autopilot's chat panel is narrow: anything extra
pushes the question out of view.

Before you send it, compare the message with the template line by line
and delete every line the template does not have.

Send this reply as your final message and end the turn. Do not ask the
gate question with a pick-list or question tool: a pending question keeps
the turn open, and Studio Web locks the canvas while a turn runs, so the
user cannot review the shape they are asked to approve. Put any "which of
two" resource questions in the same message. The user answers in their
next message, with a number, an option name, or the change they want.
Never leave the outline only in your reasoning: a user who sees only the
question cannot judge the shape.
