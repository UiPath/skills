<!--skill-flavor:phase3-output-surface:start-->
> **What Phase 3 does NOT produce:** an Implementation Plan section or a task list for implementation work. The genome `author` writes from the `ready` SDD is the implementation input. The SDD's `## Next Steps` section marks that boundary, and that is the entire `design` output surface.
<!--skill-flavor:phase3-output-surface:end-->

<!--skill-flavor:design-deliverable:start-->
The SDD is the deliverable of `design`. **Do not generate an Implementation Plan section inside the SDD. Do not derive implementation tasks during `design`. Do not start executing.**
<!--skill-flavor:design-deliverable:end-->

<!--skill-flavor:turn-boundary:start-->
> **The SDD write is a turn boundary — do not begin the genome or the build in the same turn as `design`.** Once the SDD is on disk, the superset check has passed, and the Step 2 item 9 summary is emitted, that is the end of the current turn. Continue on the **next** turn with the sequence below. Rationale: `design` (read PDD + guides, author §1–§18), `author` (read the SDD, write and self-review the genome) and the build (`uipath-genome`: configuration questions, then every component through its owning skill) are each heavy; stacking two of them in one unbroken autonomous turn is what pushes wall-clock past the per-turn watchdog and loses the whole run. Yielding after each durable write keeps each turn bounded and guarantees the SDD is graded before any further work. This is a turn checkpoint, **not** an `AskUserQuestion` — do not prompt the user; simply let the turn end after the summary.
<!--skill-flavor:turn-boundary:end-->

<!--skill-flavor:build-handoff-row:start-->
3. **The write does not end the turn and gets no genome:** after the `ready` flip, the caller's build starts in this conversation (`uipath-maestro-case`: its Phase 1 directly — the open Studio Web solution already exists and project creation happens at Step 6.0), verifying the identities the SDD resolved instead of re-discovering them.
<!--skill-flavor:build-handoff-row:end-->

<!--skill-flavor:client-word-read-row:start-->
<!--skill-flavor:client-word-read-row:end-->

<!--skill-flavor:client-word-document:start-->
Not available in Studio Web: the shell has no pandoc, and its `node` is a QuickJS sandbox that cannot run the converter. Say so in one line when the user asks for a Word SDD / ASDD, and point them to the markdown SDD.
<!--skill-flavor:client-word-document:end-->
