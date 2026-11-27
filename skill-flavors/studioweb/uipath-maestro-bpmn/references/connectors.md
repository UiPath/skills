<!--skill-flavor:field-reference:start-->
Studio Web has no `markdownPath` file to read. Get the operation's field reference with `uip maestro registry describe <nodeType> --output plain` (add `--object <OBJECT>` for a generic operation such as `get-record`) rather than guessing input names.
<!--skill-flavor:field-reference:end-->

<!--skill-flavor:library-pull:start-->
In Studio Web on cloud the library of the session is always loaded: `uip maestro registry pull` has no effect.
With no session library (Automation Suite), `check` and `compile` fetch a missing operation through `uip` themselves, so re-run `check`.
<!--skill-flavor:library-pull:end-->

<!--skill-flavor:package-metadata-row:start-->
| package metadata | `entry-points.json`, `operate.json`, `package-descriptor.json` | the same `refresh`. Studio Web has no `uip solution resources refresh`: add each connection with `uip solution resources add` ([Validation loop](../SKILL.md#validation-loop)) |
<!--skill-flavor:package-metadata-row:end-->

<!--skill-flavor:prepare-live:start-->
**`prepare` is a live call.** It reads through a real connection, so it needs a connection on the tenant (you are already signed in). Run it when `check` asks for it, not speculatively.
<!--skill-flavor:prepare-live:end-->

<!--skill-flavor:sdk-event-entity:start-->
  Studio Web ships its own SDK: unless the user confirms it runs <NEXT_SDK_VERSION> or later, use the `entity` form for a folder entity. When `check` reports `TS2353` or `BPMN_UNKNOWN_OPTION` on `entity`, write the `parameters` form above instead and compile: the trigger's `folderEntityName` then reads `=bindings.<id>` when this build writes the picker. When it holds the object itself instead, this build predates both forms: run `uip maestro bpmn registry get Intsvc.EventTrigger --object-name EntityTriggers_V3 --operation <OPERATION> --connection-id <CONNECTION_ID> --input-details '{"queryParameters":{"entityScope":"folder","folderEntityName":"<ENTITY_NAME>"}}' --solution-folder <SOLUTION_DIR> --output json`, then author `.activity(<ID>, 'Intsvc.EventTrigger', { contextRows, inputs, outputRows, contextVerbatim: true })` from the `<uipath:context>`, input and output rows of `Data.V2.ElementXml`, and one `.binding(<BINDING_ID>, { resource, propertyAttribute, resourceKey, value })` per `Data.V2.RootBindings` row. Follow `Data.V2.Instructions` for the `{{VAR_ID}}` tokens. `examples/InvoiceApproval.bpmn.ts` (`Event_CiykXe`) shows only the `.activity()` wrapper; the rows come from `Data.V2`. `<OPERATION>` is `UPDATED_V3` or `CREATED_V3`. If `registry get` fails too, tell the user that this build cannot write the picker. Never the literal `filter`.
<!--skill-flavor:sdk-event-entity:end-->
