<!--skill-flavor:host-command-scope:start-->
> **Studio Web scope:** use the embedded static validator autonomously. After explicit consent, execute only through the live, schema-inspected `proxy-tools-Api` / `RunProject` host operation. Registry and read-only `uip is` discovery are allowed. Do not use the embedded runner, login, connection-edit, local lifecycle, binding-sync, resource-refresh, Orchestrator/trace CLI, or solution-metadata edits as troubleshooting fallbacks.
<!--skill-flavor:host-command-scope:end-->

<!--skill-flavor:designer-roundtrip-runtime-check:start-->
- **On-disk is authoritative — re-validate after every designer save.** Run `uip api-workflow validate Workflow.json --output json` from the exact project root after a designer roundtrip. If runtime inspection is still required, state side effects and ask for explicit consent. On "yes," inspect `/skills/synthetic/proxy-tools-Api/SKILL.md`, invoke `RunProject` with exactly its live schema fields, inspect the host result, and re-apply the single-expression workaround if the file was corrupted.
<!--skill-flavor:designer-roundtrip-runtime-check:end-->

<!--skill-flavor:workflow-input-runtime:start-->
### `$workflow.input.<name>` is undefined (or `$input.<name>` returns the wrong thing)
- **Symptom:** the value is `undefined` or is the previous task's output.
- **Cause:** the input is absent from `input.schema`, the freshly inspected `RunProject` schema did not receive/expose it, no default exists, or the workflow used `$input.<name>` instead of `$workflow.input.<name>`.
- **Fix:** use `$workflow.input.<name>` everywhere; confirm the declaration or default; then re-read `/skills/synthetic/proxy-tools-Api/SKILL.md` and supply the value only through a field declared by the live `RunProject` schema. If the schema exposes no such field, report the capability gap instead of guessing a parameter.
<!--skill-flavor:workflow-input-runtime:end-->

<!--skill-flavor:runtime-cli-heading:start-->
## Runtime Errors in Studio Web
<!--skill-flavor:runtime-cli-heading:end-->

<!--skill-flavor:runtime-file-not-found-context:start-->
### Target project or workflow is not found
- **Cause:** the embedded validation command used the wrong project working directory, or `RunProject` targeted a project name not present in the live host schema/workspace.
<!--skill-flavor:runtime-file-not-found-context:end-->

<!--skill-flavor:runtime-input-arguments:start-->
### Run input is rejected
- **Cause:** the invocation included a field or value not declared by the live `RunProject` schema.
- **Fix:** re-read `/skills/synthetic/proxy-tools-Api/SKILL.md`, inspect `RunProject`, and retry only with schema-declared fields after renewed consent when the retry can cause side effects. Do not translate desktop CLI flags into guessed tool parameters.
<!--skill-flavor:runtime-input-arguments:end-->

<!--skill-flavor:runtime-executor-failures:start-->
### `RunProject` reports a workflow failure
- **Cause:** a task threw during host execution, or a connection/expression/logic fault surfaced only at runtime.
- **Fix:** require the actual `RunProject` result, then triage **Structure > Expression > Activity Config > Logic**. Common checks: missing activity exports, invalid strict-mode expressions, stale connection IDs, wrong loop body shape, and unupdated DoWhile conditions. Re-run the embedded static validator after every edit; ask for explicit consent again before another host execution that can repeat side effects.
<!--skill-flavor:runtime-executor-failures:end-->

<!--skill-flavor:resource-lookup-runtime:start-->
- **Well-known shortcuts.** Values such as `"inbox"`, `"sentitems"`, and `"drafts"` can work while the Studio Web picker still lacks a friendly label. For an exact ID, inspect a relevant host resource ProxyTool and use only a live schema-declared read/list operation. Do not invoke a generic embedded resource runner. If no lookup capability is exposed, explain the picker limitation and ask whether the shortcut is acceptable.
<!--skill-flavor:resource-lookup-runtime:end-->

<!--skill-flavor:connection-remediation:start-->
- **What NOT to do:** do not proceed with a failing UUID or infer that no connection exists before checking filtered, unfiltered, and `--all-folders` listings plus `ping`. If none yields a healthy UUID, ask the user to repair or create the connection through Studio Web. Do not run the state-changing `uip is connections edit` command.
<!--skill-flavor:connection-remediation:end-->

<!--skill-flavor:solution-resource-diagnostics:start-->
### Properties Panel Requests a Connection From the Resource Definition Page

- **Cause:** Studio Web cannot resolve the connection through its host-owned resource metadata, even when the connection ID in `Workflow.json` is valid.
- **Fix:** Confirm the activity uses a UUID that succeeds under read-only `uip is connections ping`. Then inspect and use a relevant Studio Web resource ProxyTool only through its live schema. Do not inspect or edit `.uipx`, `bindings_v2.json`, `resources/`, or `userProfile/`, and do not run binding-sync/resource-refresh commands. If the host exposes no suitable resource capability, report the gap and ask the user to configure the resource in Studio Web.
- **See also:** [connector-activity-discovery.md](connector-activity-discovery.md) for the Studio Web connector flow.
<!--skill-flavor:solution-resource-diagnostics:end-->

<!--skill-flavor:connection-auth-diagnostics:start-->
  - **Fix:** Run the read-only `uip is connections ping <connection-uuid> --output json`. If it returns `ConnectionNotEnabled`, ask the user to repair the connection through Studio Web; do not run connection edit or login commands. If it succeeds but the cloud call still returns 401, report a likely Studio Web session/org/tenant capability mismatch for host-level investigation.
<!--skill-flavor:connection-auth-diagnostics:end-->

<!--skill-flavor:file-path-remediation:start-->
- **Fix:** Studio Web commands start at `/solution`, not inside the active designer project. For an existing project, set `workingDirectory` to `CurrentProject.AbsolutePath`. After `CreateProjects`, which does not switch projects, use `/solution/<projectName>/Workflow.json` explicitly and verify the directory first.
<!--skill-flavor:file-path-remediation:end-->

<!--skill-flavor:json-syntax-remediation:start-->
- **Fix:** Check syntax with the browser shell's built-in `jq`, then run the API Workflow static validator:
  ```bash
  jq empty Workflow.json
  uip api-workflow validate Workflow.json --output json
  ```
  JSON does not permit comments. Do not try to use Node or another unavailable local interpreter.
<!--skill-flavor:json-syntax-remediation:end-->

<!--skill-flavor:runtime-validation-pitfall:start-->
- **Fix:** ALWAYS run `uip api-workflow validate <Workflow.json>` after every edit; it is the autonomous offline schema + semantic check. When runtime validation is still needed, state side effects, obtain explicit consent, inspect the live `RunProject` schema, and execute through that host operation.
<!--skill-flavor:runtime-validation-pitfall:end-->

<!--skill-flavor:runtime-debugging-strategy:start-->
1. **Keep static validation machine-readable** with `--output json` and fix until `Data.Status` is `Valid`.
2. **For runtime evidence, obtain explicit consent, inspect `/skills/synthetic/proxy-tools-Api/SKILL.md`, and invoke the live `RunProject` schema.** Do not substitute the embedded runner.
3. **Reduce to a minimal repro** by temporarily removing downstream tasks, preserving user work and restoring it after isolation.
4. **Read the host tool result first** and map its error to Structure, Expression, Activity Config, or Logic.
5. **Re-consent before retries with possible side effects.** A diagnostic rerun may repeat vendor actions.
<!--skill-flavor:runtime-debugging-strategy:end-->

<!--skill-flavor:cloud-run-diagnostics:start-->
### Failed Cloud Run After Publish

Use a Studio Web diagnostic or published-workflow tool only after inspecting its live schema. Read-only `uip is connections ping` may confirm connection health, but do not substitute embedded `uip or`, trace, authentication, or local lifecycle commands. If Studio Web exposes no job/log/trace capability, report the missing capability and hand off the deeper investigation rather than switching environments.
<!--skill-flavor:cloud-run-diagnostics:end-->

<!--skill-flavor:local-packaging-errors:start-->
## Packaging Errors in Studio Web

Do not diagnose packaging by inspecting `.uipx`, editing generated project metadata, re-scaffolding with init, or running local pack commands. Host-intercepted publication starts Unified Build packaging in the background. A successful `uip solution publish` response means only that the request was accepted; inspect Studio Web's Publish history for the final packaging/publication error. The host-generated project tree and `CreateProjects` result remain authoritative.
<!--skill-flavor:local-packaging-errors:end-->

<!--skill-flavor:local-publish-errors:start-->
## Publish Errors in Studio Web

First distinguish bridge rejection from background failure:

- `uip solution publish --help` is read-only and can confirm the supported bridge flags.
- For an explicit approved publication, invoke `uip solution publish` on the active solution with no positional package path and only `--description`, `--release-notes`, `--version`, `--location`, `--location-name`, or `--personal-workspace`.
- Immediate command failure is a request/flag/authorization problem; report that host result without login or local remediation.
- Immediate success means request accepted, not publication complete. Check Studio Web's Publish history for the terminal packaging/publication status and diagnose from that entry.

Never run `uip solution pack`, pass a local `.zip`, or substitute deploy/login commands.
<!--skill-flavor:local-publish-errors:end-->
