# API Workflow Recipe

The current supported implementation wrapper for confirmed API workflow
invocation is `bpmn:serviceTask` with `Orchestrator.ExecuteApiWorkflowAsync`.

Use these context fields:

- `ReleaseKey` = Orchestrator process GUID from `uip or processes list`.
- `FolderKey` = target folder GUID.
- `FolderPath` = target folder path.
- `Name` = process display name.

Use `type="string"` on those context inputs. Do not rely on a lone display
name when the wrapper requires resolved process and folder identity.

The model may draft:

- Service task wrapper and BPMN DI.
- Request variables, response variables, status/error variables, and mappings.
- Public-safe request body examples and boundary error paths.

CLI or operator must resolve:

- API workflow resource identity, folder binding, and generated package resources.
- Solution-style `bindings_v2.json` entries for `uip solution resource refresh`.
- Dynamic request and response schemas.
- Fire-and-forget versus wait behavior when the product contract exposes that choice.

Stop before Operate when workflow binding, schema, or wait behavior is unresolved.
