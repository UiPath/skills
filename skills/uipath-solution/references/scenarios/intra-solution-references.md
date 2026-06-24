# Cross-reference inside the same solution

A coordinator agent (or flow, or process) needs to invoke another agent in the **same solution**. Both projects ship together, neither exists in cloud yet at refresh time.

## Setup

Solution has `Coordinator/` (agent) and `Worker/` (agent). Coordinator's `agent.json` declares a tool whose `referenceKey` should resolve to Worker — but Worker isn't on cloud, so its cloud key doesn't exist.

```
MySolution/
├── MySolution.uipx
├── Coordinator/
│   ├── agent.json
│   ├── resources/WorkerTool/resource.json
│   └── bindings_v2.json
├── Worker/
│   └── agent.json
└── resources/solution_folder/
    ├── process/agent/Coordinator.json    (auto on add)
    └── process/agent/Worker.json         (auto on add)
```

The right `referenceKey` for the Worker tool is the **solution-resource key** of `Worker.json` (read from `uip solution resources list --kind Process --source local --output json`), **not** the `projectId` from `.uipx`.

```jsonc
// Coordinator/resources/WorkerTool/resource.json
{
  "$resourceType": "tool",
  "name": "WorkerTool",
  "type": "agent",
  "location": "solution",                              // ← intra-solution, not "external"
  "referenceKey": "<solution-resource-key-of-Worker>", // from `resource list --kind Process --source local`
  "properties": {
    "processName": "Worker",
    "folderPath": "solution_folder"
  }
}
```

## What happens at refresh + pack

- `solution project add` writes `Worker.json` and `Coordinator.json` under `resources/solution_folder/process/agent/` with stable solution-resource keys (UUIDs minted by the SDK at add time).
- `resource refresh` doesn't re-mint those keys — they're stable for the life of the solution.
- At pack, the Coordinator's `runtimeDependencies` entry for the Worker tool carries the same solution-resource key as `referenceKey`. Orchestrator's deploy pipeline resolves intra-solution links by matching this key to a sibling resource in the deployment.

## Gotchas

- **Don't put the cloud key of a different (already-published) Worker** if you intend to ship Worker as part of this solution. `referenceKey` to a cloud key skips the intra-solution link and points the runtime at the cloud copy — which may or may not exist in the target tenant at deploy time.
- **The solution-resource key is stable across refreshes within an instance** but **regenerates if you delete and re-create the solution** (`solution init` → mint fresh UUIDs). Hard-coding the key in `resource.json` survives normal refresh cycles but breaks if anyone wipes-and-recreates. If that's a risk, rebuild the file from `resource list --kind Process --source local` output as part of CI.
- **`location` must be `"solution"`, not `"external"`** for intra-solution tools. SW UI shows external-tool dialogs differently and won't render the link state correctly.
- **Worker → Coordinator cycles**: nothing prevents you from declaring a tool in Worker that points back at Coordinator. The runtime supports it; if the agent prompts loop, that's an authoring issue, not a deploy one.

## Verify

```bash
uip solution resources list --kind Process --source local --output json
```

The keys you see here are what `referenceKey` should be in any `location: "solution"` tool resource file.

> See: [develop-solution.md — Step 6: List Resources](../develop-solution.md#step-6-list-resources).
