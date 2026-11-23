<!--skill-flavor:author-scope:start-->
Everything that happens before a flow runs: choose each node, write its source
in `.flow-sdk/`, and run the loop in
[SKILL.md — Lifecycle](../SKILL.md#lifecycle) until the target `.flow`
validates. A new flow in a project whose `new.flow` has no steps is built in
that file, from `.flow-sdk/new.flow.ts`, never in a second file named after the
flow. Authoring ends
at a valid artifact; publishing, running and debugging are
[`operate.md`](operate.md), and a failed run is [`diagnose.md`](diagnose.md).
<!--skill-flavor:author-scope:end-->

<!--skill-flavor:source-not-artifact:start-->
4. **Edit the source, not the artifact.** A new flow: `decompile` the project's
   `new.flow` into `.flow-sdk/new.flow.ts`, add your steps to that source, and
   `compile` it `-o new.flow`. Never write a source or a `.flow` named after the
   flow beside a `new.flow` that has no steps; a second flow in the project gets
   its own file ([SKILL.md — Project layout](../SKILL.md#project-layout), rule 4).
   A `.flow` that already has steps is
   re-emitted by decompile and merge ([`brownfield.md`](brownfield.md)).
<!--skill-flavor:source-not-artifact:end-->

<!--skill-flavor:solution-lookup:start-->
10. **Work in the open solution and the open flow.** Studio Web has exactly
    one solution open at `/solution`; never create another. Edit the `.flow`
    that the context of the turn names, as
    [SKILL.md — Project layout](../SKILL.md#project-layout) says.
<!--skill-flavor:solution-lookup:end-->

<!--skill-flavor:completion-next:start-->
7. **What's next** — when the request did not already say, ask with rule 9:
   debug the flow, publish the solution, or "Something else". Each hands off
   to [`operate.md`](operate.md). A request that already named the next step
   ("publish it", "debug it") is the selection; act on it. When you wrote a
   new `<Name>.flow` that is not the open file, tell the user to open it in
   the Explorer.
<!--skill-flavor:completion-next:end-->
