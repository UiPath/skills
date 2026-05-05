# IXP / Document Extraction Node — Implementation

## Node Type

`uipath.ixp.<modelName>.shared-<modelName>` — tenant-specific. One node type per published IXP extraction model. Find via `uip maestro flow registry search ixp`.

## Registry Validation

```bash
uip maestro flow registry get "<nodeType>" --output json
```

Confirm: input port `input`, output ports `success` + `error`, required input `fileRef`.

## Adding the Node

```bash
uip maestro flow node add <flow.flow> "<nodeType>" \
    --input '{"fileRef":"=js:$vars.<upstream-node-id>.output"}'
```

You only need to provide:

- **`fileRef`** (required) — JS expression pointing at an upstream node's file output, e.g. `"=js:$vars.downloadFile1.output"`. The upstream node id is the `id` field (not display label, not nodeType).
- **`pageRange`** (optional) — e.g. `"1-5"`.

Everything else (model name, folder, project, etc.) is auto-filled from the registry. Don't pass them via `--input`.

`node add` does NOT auto-wire edges — connect with `uip maestro flow edge add` (use `--source-port success`).

## Output

Output schema is defined in the manifest's `outputDefinition` — read it via `registry get` to see the exact shape (varies by model taxonomy).

- `$vars.{nodeId}.output` — extraction result.
- `$vars.{nodeId}.error` — populated on failure.
