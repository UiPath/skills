<!--skill-flavor:connector-impl-bindings-intro:start-->
`uip maestro flow node configure` authors top-level `bindings[]` and `inputs.detail`, and writes `bindings_v2.json` in the project directory from `bindings[]`; the host debug reads the saved project directly. Never hand-edit `bindings_v2.json`.
<!--skill-flavor:connector-impl-bindings-intro:end-->

<!--skill-flavor:connector-impl-registry-get-flags:start-->
Every connector node requires an Integration Service connection in top-level `bindings[]`. Run `registry get` with `--connection-id`; otherwise custom fields, dynamic enums, and reference metadata are absent. `registry get` accepts only `--connection-id` (and `--local`, which needs a `.uipx` and fails in Studio Web) — no `--activity-version` (it reads the node's own `configuration.version` and self-routes `4.0.0` activities; anything else fails `error: unknown option`). For `4.0.0` nodes `--connection-id` adds nothing (metadata not connection-scoped — see [§ 4.0.0 Activities](#400-activities)).
<!--skill-flavor:connector-impl-registry-get-flags:end-->

<!--skill-flavor:connector-impl-configure-step:start-->
4. **Configure** — `uip maestro flow node configure /solution/<FlowProject>/new.flow <NODE_ID> --detail "$(cat /tmp/detail.json)" --output json` (Step 6b).
<!--skill-flavor:connector-impl-configure-step:end-->

<!--skill-flavor:connector-impl-bindings-file:start-->
Bindings belong in flow top-level `bindings[]`, alongside `nodes`, `edges`, and `definitions`. `node configure` writes `/solution/<FlowProject>/bindings_v2.json` from them and the host debug reads the saved project directly; never edit that generated file.
<!--skill-flavor:connector-impl-bindings-file:end-->
