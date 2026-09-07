<!--skill-flavor:ixp-impl-discovery-note:start-->
Auth is host-provided (a 401/403 means the signed-in user lacks rights). Only models with a folder deployment on your tenant appear — publishing alone does not surface a model here (example `nodeType` in the response below).
<!--skill-flavor:ixp-impl-discovery-note:end-->

<!--skill-flavor:ixp-impl-listing-commands:start-->
```bash
uip maestro flow registry pull --force                      # auth is host-provided — no login step
uip maestro flow registry search "uipath.ixp" --output json
```
<!--skill-flavor:ixp-impl-listing-commands:end-->

<!--skill-flavor:ixp-impl-listing-rules:start-->
- **Do NOT scaffold a solution, run `uip maestro flow init`, or write a `.flow` file.** Listing is read-only Q&A.
- **Do NOT mock.** If `Data: []`, answer directly: no IxP models are published on this tenant. The `core.logic.mock` fallback is for build-time planning, not for listing-time Q&A.
- **Do NOT try to log in.** Auth is host-provided (`uip login` and `uip login status` are refused). An empty `Data: []` after `registry pull --force` means no model is deployed on the tenant, not that you are logged out; a 401/403 means the signed-in user lacks rights — report it and stop.
- **Do NOT search by `"runtime"`, `"document extractor"`, `"extractor"`, or `"IXP"` (uppercase).** These return empty results or agent-tool variants — not extraction nodes. Use `"uipath.ixp"` (lowercase) only.
- **Do NOT use `uip maestro flow process list` or any Orchestrator folder iteration.** `flow process list` enumerates *deployed flow process instances* (with `--folder-key`), not published models. Listing published IxP models always goes through `registry search "uipath.ixp"`.
- **Do NOT guess `uip maestro flow list-*` or `uip maestro ixp list-*` subcommands.** None exist. The CLI returns `unknown command 'list-...'` and there is no fallback path to pursue. <!-- uip-check-skip -->
<!--skill-flavor:ixp-impl-listing-rules:end-->

<!--skill-flavor:ixp-impl-fileref-runtime:start-->
At runtime the variable holds a `{ ID, FullName, MimeType, Metadata }` Attachment object — keys are case-sensitive; `ID` is uppercase, not `Id`. `uip flow debug` cannot upload a file for a `file` input in Studio Web (`--attachment` is ignored): keep the `type: "file"` + `triggerNodeId` declaration, validate with `flow validate`, and test with a sample document from the designer's Debug panel or an upstream node that yields the attachment. Do not declare the variable as `type: "object"`, do not reference it as `=js:$vars.<variableId>` directly without the trigger output path, and do not pass a bare GUID/URL/path/`.ID`/`.FullName`.
<!--skill-flavor:ixp-impl-fileref-runtime:end-->

<!--skill-flavor:ixp-impl-taxonomy-auth:start-->
The positional is a project name from `uip ixp projects list`, and `--version` is required — get it from `uip ixp projects list-models "<project-name>"`. `Data.Node.inputDefaults.modelName` is frequently NOT a project name; passing it returns 404 `ProjectNotFoundError`, which is an ordinary outcome, not a problem to debug. Auth is host-provided; the command uses the user Bearer to call the same DU-App route that Studio Web's "Schema definition" panel uses.
<!--skill-flavor:ixp-impl-taxonomy-auth:end-->

<!--skill-flavor:ixp-impl-mock-validate-step:start-->
6. Run `uip maestro flow validate /solution/<FlowProject>/new.flow --output json` once after all edits complete.
<!--skill-flavor:ixp-impl-mock-validate-step:end-->

<!--skill-flavor:ixp-impl-debug-table:start-->
| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Model not folder-deployed, or registry cache stale | Run `uip maestro flow registry pull --force` (auth is host-provided; a 401/403 means missing rights) |
| `model.context` rejected by runtime | `folderKey` or `modelName` missing from `inputs` (the context array is built from these) | Confirm `inputs.modelName` and `inputs.folderKey` are populated. |
| Empty `$vars.{nodeId}.output` | Model's taxonomy doesn't match the document, or extraction silently returned no fields | Inspect the raw API response via `$vars.{nodeId}.error` first; if no error, run the extraction against the same document on the IxP product UI to compare |
| `fileRef` not resolving | Expression references an upstream variable that isn't wired, or the upstream node didn't produce a file output | Verify the upstream node exports a file reference and that the `=js:$vars.{upstreamId}.output.<field>` expression matches |
| `[430002] Invalid input on document extraction operation` at debug | `fileRef` bound to the attachment's `.ID` (or another scalar) instead of the attachment object — `flow validate` does not catch this | Bind the whole object: `=js:$vars.<upstream>.output.<attachment>` — drop the `.ID` |
| `[430002] Invalid input on document extraction operation` at debug, backend detail `'downloadedFileOutput' is missing the required 'ID' field` | The `fileRef` expression is correct, but the source flow input is declared `"type": "object"` instead of `"type": "file"` — the attachment has nowhere to bind, so the variable holds a plain JSON object | Declare the input `type: "file"`. See [Wiring `fileRef`](#wiring-fileref--file-variable-bound-to-the-trigger). |
| Extraction failed | Underlying IxP model errored (unsupported MIME type, corrupted file, service-side failure) | Check `$vars.{nodeId}.error.detail` for the IxP service response |
| `uip maestro flow node configure` rejects with "not a connector type node" | Expected — IxP is not a connector. | Edit `inputs.*` in the `.flow` JSON directly. |
| Studio Web: "Cannot destructure property 'modelName' of 't' as it is undefined" when clicking the node | `inputs.model` blob missing/undefined | Copy `inputDefaults.model` verbatim into `inputs.model` (Authoring rule #1, [JSON Structure](#json-structure)). |
| `flow validate` error `inputs.model must be an object with non-empty string modelName and folderKey` | `inputDefaults.model.modelName` was `null` and copied verbatim | Set `inputs.model.modelName` from `inputDefaults.model.modelDisplayName` (Authoring rule #1); if `folderKey` empty too, take flat `inputDefaults.folderKey`. |
<!--skill-flavor:ixp-impl-debug-table:end-->

<!--skill-flavor:ixp-impl-taxonomy-fallback:start-->
If the command fails (no matching project, a 401/403 because the signed-in user lacks rights, deployment not yet published, transient failure), fall back to defensive `find`-by-`FieldName` patterns with assumed field names and surface the assumptions to the user under **Open Questions**. **One attempt** — a 404 or validation error will not resolve by reissuing the lookup under another spelling of the name, so do not iterate on name variants. Do NOT substitute a one-off extraction or IxP-product-UI inspection in the agent loop — `get-taxonomy` is the agent-loop path.
<!--skill-flavor:ixp-impl-taxonomy-fallback:end-->
