# Upload Safety: Do Not Auto-Run `uip solution upload`

The eval run requires the Flow solution to exist in Studio Web. The temptation, when an eval run errors with a missing-solution or missing-IDs error, is to "fix" it with `uip solution upload`. **Don't.**

## The Rule

**The skill must NEVER run `uip solution upload` automatically as part of an evaluation workflow. Always ask the user first.**

This applies regardless of whether:

- The local project was created via `uip maestro flow init` and never uploaded.
- The local project was downloaded from Studio Web via `uip agent pull` and edited locally.
- The user is working in a VS Code-authored solution / personal workspace and the project may not match what is on Studio Web.
- The CLI errors with `solution-id could not be resolved` or any variant.

## Why

`uip solution upload` is a write operation against Studio Web. It either creates a new solution or **overwrites** the existing one matched by `SolutionId` from the local working tree. Three concrete failure modes if the skill auto-uploads:

1. **The user is iterating locally** in VS Code or the filesystem and intended to test something **before** publishing. Auto-upload pushes work-in-progress to Studio Web where teammates and triggers may pick it up.
2. **The user pulled the solution from Studio Web** to edit a small piece. Auto-upload sends the partial local state back, potentially **overwriting** changes another user made on Studio Web in the meantime.
3. **The local solution diverged from Studio Web** (e.g., a teammate edited the solution on Studio Web while the dev was working locally). Auto-upload silently discards the remote-side changes — they are not merged.

In all three cases the user loses work or surprises a teammate. The cost of pausing to ask is one prompt; the cost of an unwanted upload can be hours of recovery.

## What To Do Instead

When `eval run start` cannot resolve the solution:

1. **Stop and ask the user.** Use plain language: "Your Flow solution doesn't appear to be in Studio Web (or its IDs aren't resolvable from the local working tree). I can't run an eval until it is. How do you want to proceed?"
2. **Offer the options explicitly:**
   - **Upload now** — the user runs (or asks the skill to run) `uip solution upload <SolutionDir> --output json`. They acknowledge that this will write to Studio Web.
   - **Pass IDs explicitly** — the user provides `--solution-id` and `--project-id` for an existing Studio Web solution. The skill plumbs them through to `eval run start`.
   - **Cancel** — they meant to test something else (e.g., `flow debug`).
3. **Wait for an explicit decision.** Do not infer one from context, prior commands, or comments in the project.

## How to Detect "Local Workspace or VS Code"

There is no single CLI flag that says "this project is local-only." The signals to weigh, in priority order:

1. **`SolutionStorage.json` is missing or has no `SolutionId`.** The local working tree has not been linked to a Studio Web solution. `uip solution upload` would CREATE a new solution; the user might not want a new tenant entry.
2. **`.vscode/` directory exists in the solution root.** Strong signal that the dev is authoring in VS Code; assume they are iterating locally.
3. **The directory is under a workspace path the user has indicated they edit locally** (`~/Code/...`, `~/dev/...`, etc., or any path that is not the default Studio Web download location). Treat as local-first.
4. **`uip solution upload` has never been recorded** in the recent shell history or in the conversation. If the skill cannot point to a prior explicit upload, do not assume the project is in Studio Web.

If ANY of these signals is true, skip auto-upload entirely and ask.

## How to Detect "Solution Already in Studio Web"

The cheapest check is to attempt a read-only run command before doing anything else:

```bash
uip maestro flow eval run list --set "<set_name>" --path <flow_project> --output json
```

If this returns successfully (even with zero past runs), the solution is in Studio Web. If it errors with a missing-solution or auth error, treat the solution as not-yet-uploaded — and follow the rule above.

Alternatively, `eval run start` itself will fail fast with a clear error. Either way: **read-only probe first; ask before upload.**

## When the User Explicitly Asks to Upload

If the user tells the skill to upload (e.g., "go ahead and upload the solution"), the skill is allowed to run:

```bash
uip solution upload <SolutionDir> --output json
```

In that response:

1. Echo the command back so the user can see exactly what is being run.
2. Run it and report the `SolutionId` and `DesignerUrl` from the output.
3. Then proceed with the eval run.

Even with explicit consent, do not chain `solution upload` automatically into the next step — surface the result first.

## Anti-patterns

- **Don't run `uip solution upload` as part of "fixing" an eval-run error.** Ask first.
- **Don't infer consent from a vague instruction like "make the eval work."** That is not consent to upload; it is a request to diagnose.
- **Don't auto-retry an eval run after a failed solution-resolution by attempting `uip solution upload` and re-running.** That doubles down on the wrong action.
- **Don't run `uip solution upload` while another user might be editing the solution on Studio Web.** Even with explicit consent, warn the user that overwriting concurrent edits is a possible outcome.
- **Don't combine `flow debug` and `eval run` in the same session against the same solution.** Each carries its own Studio Web debug session; mixing them confuses run IDs and may trigger unexpected uploads.
