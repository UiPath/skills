<!--skill-flavor:upload-safety-content:start-->
# Upload Safety: Do Not Auto-Run `uip solution upload`

Never run `uip solution upload` automatically during an evaluation workflow. Always ask the user first. This applies to locally created, Studio Web-downloaded, VS Code-authored, or otherwise divergent solutions, including when the CLI reports `solution-id could not be resolved` or a similar error.

`uip solution upload` creates or overwrites the solution matched by the local `SolutionId` in Studio Web. Automatic upload can publish work in progress, overwrite concurrent Studio Web changes, or silently discard remote changes because local and remote state is not merged.

## Read-Only Resolution Check

This applies regardless of whether:

- The local project was created via `uip maestro flow init` and never uploaded.
- The local project was downloaded from Studio Web via `uip solution download` and edited locally.
- The user is working in a VS Code-authored solution / personal workspace and the project may not match what is on Studio Web.
- The CLI errors with `solution-id could not be resolved` or any variant.

## Why

`uip solution upload` is a write operation against Studio Web. It either creates a new solution or **overwrites** the existing one matched by the `SolutionId` in the local `.uipx` (bundling generates `SolutionStorage.json` from it; that file is read back only for a direct `.uis` upload) — the overwrite needs no flag and raises no prompt. The replaced contents are recorded as a restorable version (skipped entirely with `--no-snapshot`), but recovery is browser-only, after the fact, by the user — and it does not undo failure mode 1 below. None of this is a reason to skip asking. Three concrete failure modes if the skill auto-uploads:

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

1. **The `.uipx` carries an id Studio Web has never seen** (a fresh `solution init`, never uploaded). The upload would CREATE a new solution; the user might not want a new tenant entry.
2. **`.vscode/` directory exists in the solution root.** Strong signal that the dev is authoring in VS Code; assume they are iterating locally.
3. **The directory is under a workspace path the user has indicated they edit locally** (`~/Code/...`, `~/dev/...`, etc., or any path that is not the default Studio Web download location). Treat as local-first.
4. **`uip solution upload` has never been recorded** in the recent shell history or in the conversation. If the skill cannot point to a prior explicit upload, do not assume the project is in Studio Web.

If ANY of these signals is true, skip auto-upload entirely and ask.

None of these signals separates a first import from an overwrite of a live solution: an id from a downloaded or copied project names a solution the upload would replace, and the local tree alone cannot tell the two apart. Treat both as writes to ask about.

## How to Detect "Solution Already in Studio Web"

The cheapest check is to attempt a read-only run command before doing anything else:

```bash
uip maestro flow eval run list --set "<set_name>" --path <flow_project> --output json
```

A successful response, including zero past runs, indicates that the solution is in Studio Web. A missing-solution or auth error means it is not uploaded for this workflow; ask before uploading. If `eval run start` fails with a resolution error, never auto-upload or retry by uploading.

## If Evaluation Cannot Resolve the Solution

1. Stop and ask: "Your Flow solution doesn't appear to be in Studio Web (or its IDs aren't resolvable from the local working tree). I can't run an eval until it is. How do you want to proceed?"
2. Offer:
   - **Upload now** — the user runs, or explicitly asks the skill to run, `uip solution upload <SolutionDir> --output json`; state that this writes to Studio Web.
   - **Pass IDs explicitly** — the user provides `--solution-id` and `--project-id` for an existing Studio Web solution; pass them through to `eval run start`.
   - **Cancel** — they intended to test something else, such as `flow debug`.
3. Wait for an explicit decision. Never infer consent from context, prior commands, or project comments.

## Local-Workspace Signals

Treat the project as local-first and skip auto-upload if any signal is present:

1. `SolutionStorage.json` is missing or has no `SolutionId`; upload would create a new solution.
2. A `.vscode/` directory exists in the solution root.
3. The directory is under a user-indicated local workspace path, such as `~/Code/...` or `~/dev/...`, rather than the default Studio Web download location.
4. No prior `uip solution upload` appears in recent shell history or the conversation; without a recorded explicit upload, do not assume the project is in Studio Web.

## Explicit Upload Consent

When the user explicitly asks to upload, you may run:

```bash
uip solution upload <SolutionDir> --output json
```

Before running it, echo the exact command and warn that concurrent Studio Web edits may be overwritten. Afterward, report `SolutionId` and `DesignerUrl` from the output, surface the result, and only then proceed with the eval run. Do not silently chain the upload into the next step.

## Anti-Patterns

- Do not run `uip solution upload` to fix an eval-run error.
- Do not treat "make the eval work" as upload consent.
- Do not auto-retry an eval after solution resolution fails by uploading and rerunning.
- Do not upload while another user may be editing the solution on Studio Web without warning about possible overwrites, even with consent.
- Do not combine `flow debug` and `eval run` in one session against the same solution; each has its own Studio Web debug session, and mixing them can confuse run IDs and trigger unexpected uploads.
<!--skill-flavor:upload-safety-content:end-->