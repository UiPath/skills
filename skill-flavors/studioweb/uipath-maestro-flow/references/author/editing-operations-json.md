<!--skill-flavor:flow-project-location:start-->
1. **Locate the canonical `.flow` file.** The open project is `CurrentProject.AbsolutePath` (`/solution/<ProjectName>`); its entrypoint is `new.flow` beside `project.uiproj`. If several Flow projects exist under `/solution`, confirm which one the user means. Pin every `Edit` / `Write` call to that file. `uip maestro flow validate <PATH>.flow` checks whatever file you pass, so validation does not establish the target; the project directory does.
<!--skill-flavor:flow-project-location:end-->

<!--skill-flavor:json-colocation-antipattern:start-->
> **Anti-pattern:** editing a `.flow` outside the project directory (`/solution/<ProjectName>/`, beside `project.uiproj`). The designer and `uip flow debug` only see the project's own `new.flow`; `uip maestro flow validate <PATH>.flow` can still pass on a stray copy. Always edit the sibling `.flow`.
<!--skill-flavor:json-colocation-antipattern:end-->

<!--skill-flavor:json-edit-tooling-table:start-->
| Nested replacement, field insertion, idempotent splice | `Edit` / `Write`; a `jq` or `node` script only after explicit user approval (there is no `python` in Studio Web) | Prefer direct authoring; scripts bypass safeguards and require diff review. |
<!--skill-flavor:json-edit-tooling-table:end-->

<!--skill-flavor:json-scripted-rewrite:start-->
Use only after explicit approval. Studio Web has no `python`; the scripting runtimes are `jq` and `node` (QuickJS sandbox: `fs`, `fs/promises`, `path`, `process`, `buffer` only — no `crypto`, no npm). `/solution` accepts writes but rejects `rm`/`mv`, so write the result to `/tmp` and copy it back:

```bash
jq '(.nodes[] | select(.type == "<NODE_TYPE>") | .inputs["<FIELD>"]) = "<VALUE>"' \
  /solution/<ProjectName>/new.flow > /tmp/new.flow \
  && cp /tmp/new.flow /solution/<ProjectName>/new.flow \
  && uip maestro flow validate /solution/<ProjectName>/new.flow --output json
```

Preserve canonical 2-space indent (`jq`'s default). `flow format` normalizes layout but does not re-indent unrelated structure. Whole-file `Write` is lossy and risks clobbering CLI-owned `bindings[]` / `inputs.detail`, especially on files >500 lines or containing connector/managed-HTTP nodes; prefer `Edit` in place.
<!--skill-flavor:json-scripted-rewrite:end-->

<!--skill-flavor:json-output-filter-examples:start-->
uip maestro flow validate new.flow --output json --output-filter "Warnings"
uip maestro flow registry get <node-type> --output json --output-filter "Node"
<!--skill-flavor:json-output-filter-examples:end-->

<!--skill-flavor:json-output-filter-examples-2:start-->
Use `jq` (or `node` in the QuickJS sandbox) only when JMESPath cannot express multi-step joins, format conversion, or conditional output computed from multiple fields. On `list` commands, `--output-filter` requires an explicit `--limit <n>`.
<!--skill-flavor:json-output-filter-examples-2:end-->

<!--skill-flavor:json-add-node-format:start-->
Run `uip maestro flow format new.flow` after structural edits. It regenerates `variables.nodes[]`, arranges nodes horizontally, sets canvas sizes (inline agents 288×96, containers 560×320, others 96×96), and recurses into subflows. Do not calculate coordinates manually.
<!--skill-flavor:json-add-node-format:end-->

<!--skill-flavor:json-replace-mock-discovery:start-->
1. Check the open solution first with `uip solution resources list --kind Process --output json` (`solutionResources` lists the in-solution projects); then resolve the node type with `uip maestro flow registry get "<RESOURCE_NODE_TYPE>" --output json` on the tenant registry (`--local` needs a local solution manifest and is unavailable in Studio Web).
<!--skill-flavor:json-replace-mock-discovery:end-->

<!--skill-flavor:json-replace-mock-validate:start-->
7. Run `uip maestro flow validate new.flow --output json`.
<!--skill-flavor:json-replace-mock-validate:end-->

<!--skill-flavor:json-replace-trigger-validate:start-->
3. Run `uip maestro flow validate new.flow --output json`.
<!--skill-flavor:json-replace-trigger-validate:end-->

<!--skill-flavor:json-bindings-v2-fallback:start-->
Prefer `uip maestro flow node configure` — in Studio Web it is the path known to produce a binding the designer honours. If you must use the fallback, use `Edit` for the node configuration and treat the `bindings_v2.json` that `node configure` writes into the project directory as the CLI's shape shown below (`Edit` it in place; `Write` only when the file does not exist yet), then re-run `node configure` at the first opportunity.
<!--skill-flavor:json-bindings-v2-fallback:end-->
