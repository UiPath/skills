<!--skill-flavor:host-command-scope:start-->
> **Studio Web scope:** use the embedded static validator autonomously, registry and read-only `uip is` commands for discovery, and the consent-gated live `proxy-tools-Api` / `RunProject` operation for execution. Use freshly inspected host schemas for authentication, connection, resource, lifecycle, job, log, and trace diagnostics.

<!--skill-flavor:host-command-scope:end-->

<!--skill-flavor:designer-roundtrip-runtime-check:start-->
- **On-disk is authoritative — re-validate after every designer save.** Run `uip api-workflow validate Workflow.json --output json` from the exact project root after a designer roundtrip. When runtime inspection is still required, state side effects and ask for explicit consent. On approval, inspect `/skills/synthetic/proxy-tools-Api/SKILL.md`, invoke `RunProject` with exactly its live schema fields, inspect the host result, and re-apply the single-expression workaround when the file was corrupted.
<!--skill-flavor:designer-roundtrip-runtime-check:end-->

<!--skill-flavor:designer-roundtrip-run-comparison:start-->
These issues surface when a workflow is opened, saved, or executed in **Studio Web** (cloud.uipath.com). Validate the on-disk workflow after each designer roundtrip and use approved `RunProject` execution when runtime evidence is required.

### `ReferenceError: <literal> is not defined` after opening in Studio Web

- **Symptom:** workflow behavior is correct before the designer roundtrip. After opening and saving in Studio Web, `RunProject` reports `Worker operation failed: PASS is not defined` (or `FAIL`, `INVALID`, `done`, etc. — the literal string used by the workflow).
<!--skill-flavor:designer-roundtrip-run-comparison:end-->

<!--skill-flavor:response-roundtrip-symptom:start-->
- **Symptom:** Response initially returns the expected object (for example, `{ tier: "GOLD", count: 3 }`). After opening and saving in Studio Web, `RunProject` returns each field's value as the **literal text of its expression**; `tier` becomes the string `"${$context.variables.tier}"` while the expected value is `"GOLD"`. Studio Web's output-schema validator may also flag the mismatch.
<!--skill-flavor:response-roundtrip-symptom:end-->

<!--skill-flavor:assign-roundtrip-symptom:start-->
- **Symptom:** a multi-key Assign initially updates several variables. After a Studio Web designer roundtrip, `RunProject` updates one variable per iteration while the others retain their schema defaults. Loops can produce results such as `{sum: 10, count: 0, max: 0}` when all three values were expected.
<!--skill-flavor:assign-roundtrip-symptom:end-->

<!--skill-flavor:connection-401-symptom:start-->
- **Symptom:** `RunProject` reaches the real Integration Service proxy and returns 401 with `"Invalid Organization or User secret, or invalid Element token provided."` Diagnose the endpoint/connection pairing and active Studio Web connection state.
<!--skill-flavor:connection-401-symptom:end-->

<!--skill-flavor:workflow-input-runtime:start-->
### `$workflow.input.<name>` is undefined (or `$input.<name>` returns the wrong thing)
- **Symptom:** the value is `undefined` or is the previous task's output.
- **Cause:** the input is absent from `input.schema`, the freshly inspected `RunProject` schema lacks the needed field, a default is absent, or the workflow used `$input.<name>` where `$workflow.input.<name>` is required.
- **Fix:** use `$workflow.input.<name>` everywhere and confirm the declaration or default. Re-read `/skills/synthetic/proxy-tools-Api/SKILL.md` and supply the value through a field declared by the live `RunProject` schema. When that field is unavailable, report the exact capability gap and ask for the needed host input surface.
<!--skill-flavor:workflow-input-runtime:end-->

<!--skill-flavor:runtime-cli-heading:start-->
## Runtime Errors in Studio Web
<!--skill-flavor:runtime-cli-heading:end-->

<!--skill-flavor:runtime-file-not-found-context:start-->
### Target project or workflow is not found
- **Cause:** the embedded validation command used a different project working directory, or `RunProject` received a project name absent from the live host schema/workspace.
<!--skill-flavor:runtime-file-not-found-context:end-->

<!--skill-flavor:runtime-input-arguments:start-->
### Run input is rejected
- **Cause:** the invocation included a field or value absent from the live `RunProject` schema.
- **Fix:** re-read `/skills/synthetic/proxy-tools-Api/SKILL.md`, inspect `RunProject`, and retry with its schema-declared fields after renewed consent when the retry can cause side effects.
<!--skill-flavor:runtime-input-arguments:end-->

<!--skill-flavor:runtime-executor-failures:start-->
### `RunProject` reports a workflow failure
- **Cause:** a task threw during host execution, or a connection, expression, or logic fault surfaced at runtime.
- **Fix:** use the actual `RunProject` result, then triage **Structure > Expression > Activity Config > Logic**. Common checks: missing activity exports, invalid strict-mode expressions, stale connection IDs, wrong loop body shape, and unupdated DoWhile conditions. Re-run the embedded static validator after every edit; ask for explicit consent again before another host execution that can repeat side effects.
<!--skill-flavor:runtime-executor-failures:end-->

<!--skill-flavor:resource-lookup-runtime:start-->
- **Well-known shortcuts.** Values such as `"inbox"`, `"sentitems"`, and `"drafts"` can work while the Studio Web picker lacks a friendly label. For an exact ID, inspect the relevant host resource ProxyTool and use its live schema-declared read/list operation. When a lookup capability is unavailable, explain the picker limitation and ask whether the shortcut is acceptable.
<!--skill-flavor:resource-lookup-runtime:end-->

<!--skill-flavor:runtime-content-defensive-form:start-->
- **Defensive form for JsInvoke:** normalize `.content` supplied as either a JSON string or a parsed value.
<!--skill-flavor:runtime-content-defensive-form:end-->

<!--skill-flavor:nested-connector-body-symptom:start-->
- **Symptom:** after a Studio Web save, a nested connector `message` block disappears from `bodyParameters`, while top-level fields such as `saveToSentItems` remain. The vendor receives a payload missing the message data.
<!--skill-flavor:nested-connector-body-symptom:end-->

<!--skill-flavor:connector-literal-roundtrip-symptom:start-->
- **Symptom:** after a Studio Web save, a connector literal wrapped as an Assign expression becomes empty or displays as an expression marker. Author connector parameter literals as bare values.
<!--skill-flavor:connector-literal-roundtrip-symptom:end-->

<!--skill-flavor:export-bucket-roundtrip-symptom:start-->
- **Symptom:** after a Studio Web save, downstream reads through a connector slot key return `undefined` and the generated export bucket uses a different key. Read `Data.ExportBucketKey` from the stub and use that exact key in downstream expressions.
<!--skill-flavor:export-bucket-roundtrip-symptom:end-->

<!--skill-flavor:required-field-runtime-symptom:start-->
- **Symptom:** an approved host run returns a vendor 4xx, or the Studio Web properties panel marks a field invalid, while the stub contains empty `queryParameters`, `pathParameters`, or `bodyParameters`. Cross-check the resource schema and populate every `required: true` field.
<!--skill-flavor:required-field-runtime-symptom:end-->

<!--skill-flavor:connection-remediation:start-->
- **Connection selection:** inspect filtered, unfiltered, and `--all-folders` listings plus `ping`, then use a UUID that reports healthy. When every candidate fails, ask the user to repair or create the connection through Studio Web.
<!--skill-flavor:connection-remediation:end-->

<!--skill-flavor:solution-resource-diagnostics:start-->
### Properties Panel Requests a Connection From the Resource Definition Page

- **Cause:** Studio Web cannot resolve the connection through its host-owned resource metadata, even when the connection ID in `Workflow.json` is valid.
- **Fix:** confirm the activity uses a UUID that succeeds under read-only `uip is connections ping`. Then inspect the relevant Studio Web resource ProxyTool and invoke its live schema-declared operation. When that capability is unavailable, report the gap and ask the user to configure the resource in Studio Web.
- **See also:** [connector-activity-discovery.md](connector-activity-discovery.md) for the Studio Web connector flow.
<!--skill-flavor:solution-resource-diagnostics:end-->

<!--skill-flavor:connection-auth-diagnostics:start-->
  - **Fix:** run the read-only `uip is connections ping <connection-uuid> --output json`. For `ConnectionNotEnabled`, ask the user to repair the connection through Studio Web. When ping succeeds and the cloud call still returns 401, report a likely Studio Web session, organization, or tenant mismatch for host-level investigation.
<!--skill-flavor:connection-auth-diagnostics:end-->

<!--skill-flavor:connection-health-prevention:start-->
- **Prevention:** complete the discovery flow's read-only `uip is connections ping` check before authoring, and select a UUID that reports healthy. When every candidate fails, ask the user to repair or create the connection through Studio Web.
<!--skill-flavor:connection-health-prevention:end-->

<!--skill-flavor:file-path-remediation:start-->
- **Fix:** Studio Web commands start at `/solution`. For an existing project, set `workingDirectory` to `CurrentProject.AbsolutePath`. After `CreateProjects`, verify the returned directory and use `/solution/<projectName>/Workflow.json` explicitly.
<!--skill-flavor:file-path-remediation:end-->

<!--skill-flavor:json-syntax-remediation:start-->
- **Fix:** keep JSON comment-free. Check syntax with the browser shell's built-in `jq`, then run the API Workflow static validator:
  ```bash
  jq empty Workflow.json
  uip api-workflow validate Workflow.json --output json
  ```
<!--skill-flavor:json-syntax-remediation:end-->

<!--skill-flavor:runtime-validation-pitfall:start-->
- **Fix:** ALWAYS run `uip api-workflow validate <Workflow.json>` after every edit; it is the autonomous offline schema and semantic check. When runtime validation is needed, state side effects, obtain explicit consent, inspect the live `RunProject` schema, and execute through that host operation.
<!--skill-flavor:runtime-validation-pitfall:end-->

<!--skill-flavor:post-edit-validation:start-->
- **Fix:** always read the file before editing. After the edit, run static validation. Start the workflow after explicit user consent.
<!--skill-flavor:post-edit-validation:end-->

<!--skill-flavor:runtime-debugging-strategy:start-->
1. **Keep static validation machine-readable** with `--output json` and fix until `Data.Status` is `Valid`.
2. **For runtime evidence, obtain explicit consent, inspect `/skills/synthetic/proxy-tools-Api/SKILL.md`, and invoke the live `RunProject` schema.**
3. **Reduce to a minimal repro** by temporarily removing downstream tasks, preserving user work and restoring it after isolation.
4. **Read the host tool result first** and map its error to Structure, Expression, Activity Config, or Logic.
5. **Re-consent before retries with possible side effects.** A diagnostic rerun may repeat vendor actions.
<!--skill-flavor:runtime-debugging-strategy:end-->

<!--skill-flavor:cloud-run-diagnostics:start-->
### Failed Cloud Run After Publish

Inspect the live Studio Web diagnostic or published-workflow tool schema and use the actual tool result as evidence. Use read-only `uip is connections ping` to confirm connection health. When job, log, or trace capabilities are unavailable, report the exact host gap and hand off the deeper platform investigation.
<!--skill-flavor:cloud-run-diagnostics:end-->

<!--skill-flavor:local-packaging-errors:start-->
## Packaging Errors in Studio Web

Host-intercepted publication starts Unified Build packaging in the background. A successful `uip solution publish` response means the request was accepted. Inspect Studio Web's Publish history for the final packaging or publication error. Use the host-generated project tree and `CreateProjects` result as project evidence.
<!--skill-flavor:local-packaging-errors:end-->

<!--skill-flavor:local-publish-errors:start-->
## Publish Errors in Studio Web

First distinguish bridge rejection from background failure:

- An unknown-flag error names the rejected flag and lists the supported ones; the destination flag is `--location`. Nothing was published.
- A multiple-destinations listing is not an error: nothing was published — ask the user which destination to use and rerun `uip solution publish --location "<key or name>"` (or `--personal-workspace`).
- Immediate command failure is a request, flag, or authorization problem; report the exact host result.
- Immediate success means request accepted. Check Studio Web's Publish history for the terminal packaging and publication status and diagnose from that entry.
<!--skill-flavor:local-publish-errors:end-->

<!--skill-flavor:outbound-ip-symptom:start-->
- **Symptom:** An HTTP Request or connector call to a customer/vendor endpoint fails from the deployed workflow — connection refused, or a hang ending in a timeout — while the same URL and payload succeed from other clients.
<!--skill-flavor:outbound-ip-symptom:end-->

<!--skill-flavor:outbound-ip-heading:start-->
### Outbound call to a third-party API is refused or times out from the deployed workflow
<!--skill-flavor:outbound-ip-heading:end-->

<!--skill-flavor:outbound-ip-cause-open:start-->
- **Cause:** The deployed workflow egresses from UiPath infrastructure, not from any address the endpoint owner is likely to have allowlisted, and **which** addresses depends on how the call is made.
<!--skill-flavor:outbound-ip-cause-open:end-->

<!--skill-flavor:script-budget-symptom:start-->
- **Symptom:** A Script activity that works on small inputs fails on larger ones with a script timeout reported by the `RunProject` host operation. The workflow validates; only execution fails.
<!--skill-flavor:script-budget-symptom:end-->

<!--skill-flavor:script-budget-cause:start-->
- **Cause:** the Script activity exceeded the host's execution budget. UiPath documents the cap as *"JavaScript code execution has a timeout of 30 seconds"* — [Script activity, Known limitations](https://docs.uipath.com/studio-web/automation-cloud/latest/user-guide/script). Treat 30s as the ceiling for a single Script activity, and remember a script that finishes quickly on sample data can exceed it on production volumes.
<!--skill-flavor:script-budget-cause:end-->

<!--skill-flavor:allowlist-versioning:start-->
- **Cause:** the authorable set is closed and mirrors the Studio Web palette. It also changes between releases, so **read the valid list out of the error message itself — that is the authoritative set for the host you are on.**
<!--skill-flavor:allowlist-versioning:end-->

<!--skill-flavor:allowlist-run-proof:start-->
  Some task types the runtime can execute are still not authorable, so **an activity that appears to work is not proof it can be published.** The validator is the gate.
<!--skill-flavor:allowlist-run-proof:end-->

<!--skill-flavor:file-base64-cli-pitfalls:start-->
### File to Base64 / Base64 to File fail in a run
- **Symptom:** a `RunProject` run fails inside a File to Base64 or Base64 to File task with a storage or authentication error
- **Cause:** `$helpers.file.*` reads and writes Orchestrator blob storage through the active Studio Web session
- **Fix:** report the exact host result as an authentication or capability blocker and retry after the relevant host state changes; static validation with `uip api-workflow validate` stays available meanwhile
<!--skill-flavor:file-base64-cli-pitfalls:end-->

<!--skill-flavor:file-base64-cli-folder:start-->
<!--skill-flavor:file-base64-cli-folder:end-->
