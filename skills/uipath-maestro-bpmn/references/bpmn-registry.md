# BPMN registry extension types

Registry discovery and `.activity()` for types without a typed method; split from [bpmn-runtime.md](bpmn-runtime.md).

## Registry extension types

<!-- RULE:bpmn.activity.escape-hatch -->
- Use `.activity(id, 'Type.Name', opts)` for registry extension types without typed methods; prefer typed methods when available.

<!-- RULE:bpmn.activity.discover-type -->
- Find types with `uip maestro bpmn registry search <term> --output json`, then inspect with `registry get <Type.Name> --output json`. Typed methods cover only the committed snapshot; ask the registry before concluding a type cannot be authored.

<!-- RULE:bpmn.activity.discovery-only -->
- **Discovery only:** when asked to discover/save evidence or not author, run no `init`, write no `.bpmn.ts`, and read no other reference. Save raw JSON one file per command in named `<EVIDENCE_DIR>`, otherwise `registry-evidence/` outside `<Project>` (Studio Web: `/tmp/registry-evidence/`).
  ```bash
  E=<EVIDENCE_DIR>
  mkdir -p "$E"
  uip maestro bpmn registry pull --output json > "$E/pull.json"
  uip maestro bpmn registry list --limit -1 --output json > "$E/list.json"
  uip maestro bpmn registry search <TERM> --output json > "$E/search-<TERM>.json"
  uip maestro bpmn registry get <TYPE_NAME> --output json > "$E/get-<TYPE_NAME>.json"
  ```
  Run `get` for every needed type, then stop and report found names. Preserve a response with `"Result": "Failure"` exactly and report it; never fabricate JSON.

<!-- RULE:bpmn.activity.two-registries -->
- `uip maestro bpmn registry` serves `uipath:*` extension types; `uip maestro registry` serves Integration Service operations. A connector key passed to the first correctly yields `Extension type not found`; caches are separate. See [`connectors.md`](connectors.md).

<!-- RULE:bpmn.activity.registry-freshness -->
- Registry search/get use a non-self-refreshing cache. Run `uip maestro bpmn registry pull --force` before checking newer or apparently missing types.

<!-- RULE:bpmn.activity.inline-spec -->
- If `registry get` says `Extension type not found`, emit with `.activity(id, 'Type.Name', { spec, context, inputs })`, where `spec` is a `RegistryTypeSpec` containing BPMN element/tag, typed/default context fields, `inputPattern`, and output row. `decompile` supplies specs for imported unknown nodes; leave those specs as decompile wrote them, beside explicit `contextRows`/`inputRows`/`outputRows`. Editing a row's value is fine; the row is written exactly as it reads. New nodes need the full spec.
<!--skill-flavor:sdk-inline-spec:start-->
  Needs `@uipath/maestro-builder-sdk` 6.85.7 or later; upgrade with `npm install -g @uipath/maestro-builder-sdk@latest` when older decompile reports `BPMN_TYPE_UNKNOWN`.
<!--skill-flavor:sdk-inline-spec:end-->

<!-- RULE:bpmn.activity.offsnapshot-resolve -->
- A type outside the SDK snapshot may resolve from the registry at compile time. Report that a tenant and snapshot refresh were needed; until refreshed, offline compilation is unavailable.
