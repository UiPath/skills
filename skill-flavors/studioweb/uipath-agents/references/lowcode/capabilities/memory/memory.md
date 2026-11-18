<!--skill-flavor:memory-solution-refresh-rule:start-->
4. **Refresh, validate, then add the memory space to the solution.** Memory bindings are generated during `uip agent refresh`; do not edit `bindings_v2.json` directly. `uip solution resources refresh` fails in Studio Web, so declare the memory space yourself: `uip solution resources add --source remote --kind MemorySpace --name "<MemorySpaceName>" --folder-path "<Folder>" --output json` (see [critical-rules.md](../../critical-rules/critical-rules.md) Anti-pattern 7).
<!--skill-flavor:memory-solution-refresh-rule:end-->

<!--skill-flavor:memory-verify-solution-refresh:start-->
```bash
uip agent memory list --path "<AGENT_PROJECT_DIR>" --output json
uip agent memory item list SupportRecall --path "<AGENT_PROJECT_DIR>" --output json
uip agent refresh "<AGENT_PROJECT_DIR>" --output json
uip agent validate "<AGENT_PROJECT_DIR>" --output json
uip solution resources add --source remote --kind MemorySpace --name "<MemorySpaceName>" --folder-path "<Folder>" --output json
uip solution resources list --source local --output json
```

After refresh, inspect `<AGENT_PROJECT_DIR>/bindings_v2.json` only to verify that a `memorySpace` binding exists. Do not edit it. Do not run `uip solution resources refresh`: it fails in Studio Web. Add the memory space with `uip solution resources add` instead, and confirm the local list shows it. Do not skip this because the memory space name and folder were provided, because `bindings_v2.json` looks correct, or because publish or deploy is out of scope.
<!--skill-flavor:memory-verify-solution-refresh:end-->
