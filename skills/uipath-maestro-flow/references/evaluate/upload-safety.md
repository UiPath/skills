<!--skill-flavor:upload-safety-content:start-->
# Upload Safety: Do Not Auto-Run `uip solution upload`

Never run `uip solution upload` automatically during an evaluation workflow. Always ask the user first. This applies to locally created, Studio Web-downloaded, VS Code-authored, or otherwise divergent solutions, including when the CLI reports `solution-id could not be resolved` or a similar error.

`uip solution upload` creates or overwrites the solution matched by the local `SolutionId` in Studio Web. Automatic upload can publish work in progress, overwrite concurrent Studio Web changes, or silently discard remote changes because local and remote state is not merged.

## Read-Only Resolution Check

Before other action, run:

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