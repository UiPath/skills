# Ship - Package, upload, publish, and deploy

Use this journey to package, upload, publish, or deploy a BPMN Process Orchestration project.
Shipping is the handoff from model-authored BPMN source to CLI-owned package metadata and cloud lifecycle.

> **Target rule:** if the user says "publish" without specifying a target, default to Studio Web upload.
> Use Orchestrator deployment only when the user explicitly asks for Orchestrator deployment or a deployed process.

## Pre-flight

Before upload, publish, deploy, or debug:

1. Confirm the user wants a cloud-side action and identify the target: Studio Web upload, package only,
   or Orchestrator deployment.
2. Confirm local Author validation has run for XML parse, diagram presence, entry points, bindings,
   and package consistency.
3. Confirm Integration Service enrichment is complete for executable connector elements.
   If enrichment tooling is unavailable, keep the project as a draft and do not operate it as executable.
4. Regenerate or refresh package metadata with the supported CLI path.
   Treat `bindings_v2.json`, `entry-points.json`, `operate.json`, and `package-descriptor.json` as derived unless a
   CLI contract says otherwise. Use
   [local-metadata-regeneration-guide.md](../../shared/local-metadata-regeneration-guide.md) for the local drift
   checks that connect BPMN source, entry points, bindings, and `Intsvc.*` payload enrichment.
5. Confirm login for cloud actions:

   ```bash
   uip login status --output json
   ```

6. Inspect generated files for public-safety issues before committing or sharing.
   Do not include tenant URLs, folder keys, connection IDs, user data, payloads, or local paths in docs or commits.

## Package only

Package when the user wants a local `.nupkg`, pre-deploy artifact, or package-shape verification:

```bash
uip maestro bpmn pack <project-path> <OutputDir> --output json
```

Use `--name` and `--version` only when the user provides a public-safe package identity.
Report the package path and package identity returned by the CLI.
If packing changes generated files, explain whether the change came from BPMN source, CLI enrichment,
or package generation.

## Studio Web upload

Use Studio Web upload when the user says publish without specifying Orchestrator deployment.
Studio Web upload lets the user inspect and edit the BPMN project in the browser.

```bash
uip solution upload <SolutionDir> --output json
```

If the solution has resource declarations, refresh them with the supported solution tooling in the local CLI.
Do not invent a `solution resource` command path; verify the installed CLI help before documenting a refresh step.

Report the Studio Web URL or solution ID when the CLI returns one.
If the upload succeeds but returns no URL, say `<not returned by CLI>` instead of omitting the field.

## Orchestrator deployment

Only deploy to Orchestrator when the user explicitly asks for deployment.
Confirm package identity, target folder/context, feed/package expectations, and runtime expectations before publishing.

Typical path:

```bash
uip maestro bpmn pack <project-path> <OutputDir> --output json
uip solution pack <SolutionDir> <OutputDir> --output json
uip solution publish <PackageZip> --output json
```

Deployment and activation are platform lifecycle concerns.
Use the platform workflow for `uip solution deploy ...` commands and keep this BPMN skill focused on the
BPMN project/package boundary.

## Import/package correlation

When Studio Web import or packaging fails, inspect the generated package files against
[shared/project-layout.md](../../shared/project-layout.md):

- `bindings_v2.json` for resource and connection binding declarations generated from BPMN/enrichment.
- `entry-points.json` for start-event entry points, schemas, and BPMN file references.
- `operate.json` for runtime/package metadata and the intended main BPMN file.
- `package-descriptor.json` for content manifest entries under `content/`.

If the mismatch comes from process modeling, fix `.bpmn` in Author.
If it comes from connector metadata or generated resources, rerun CLI enrichment/generation.
Do not hand-patch generated files as the primary fix.

## Failure handling

If package or upload fails:

- Capture the high-level error category.
- Check generated package files against [shared/project-layout.md](../../shared/project-layout.md).
- Correlate import errors to BPMN diagrams, start events, entry point IDs, bindings, and package descriptor entries.
- Return to Author for BPMN/source fixes.
- Rerun CLI enrichment/generation for CLI-owned Integration Service or generated-file issues.
- Use Diagnose only after a process has actually run or faulted in the runtime.

## Anti-patterns

- **Never deploy to Orchestrator just because the user said "publish."** Studio Web upload is the default.
- **Never upload an executable process with draft Integration Service intent.** Enrichment must resolve connector metadata,
  connection binding, dynamic schemas, and generated resources first.
- **Never fix a packaging error by editing generated JSON alone.** Fix BPMN source or rerun the CLI-owned
  generation/enrichment path.
- **Never include real tenant, folder, package feed, or connection values in examples or summaries.**
