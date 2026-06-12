# Agent Memory Spaces

Use this when a low-code agent needs an attached UiPath memory space for dynamic few-shot retrieval or seeded memory items.

## Critical Rules

1. **Use `uip agent memory` for memory features.** Do not hand-author `features/{Name}/feature.json` unless recovering from a broken project. The CLI updates the feature file; run `uip agent refresh` afterwards to regenerate derived files.
2. **`uip agent memory add` attaches an existing memory space; it does not create the platform memory space.** Always attempt `uip solution resources list --kind MemorySpace` discovery before attaching, even when the user supplied an exact memory space name and folder. Treat provided values as search inputs and fallback values only if discovery is blocked by auth or connectivity.
3. **Use folder paths, not folder keys.** `--folder-path` must be the literal folder path where the memory space exists, such as `Shared` or `Shared/Sales`.
4. **Refresh, validate, and solution-refresh after memory changes.** Memory bindings are generated during `uip agent refresh`; do not edit `bindings_v2.json` directly. In a solution, always attempt `uip solution resources refresh --output json` from the solution root after refresh so the generated `memorySpace` binding is imported into solution resources.
5. **Seed only non-sensitive examples.** Memory items become agent project configuration. Do not store secrets, credentials, or raw PII as seed items.

## Workflow

### 1. Discover the memory space

Always attempt discovery first, even when the user already provided the memory space name and folder. Use the provided name as the search term:

```bash
uip solution resources list --source remote --kind MemorySpace --search "<MEMORY_SPACE_NAME>" --output json
```

Use the row's `Name` as `--memory-space` and `Folder` as `--folder-path`. If discovery fails because the local session is not authenticated or the network is unavailable, continue only when the user already provided both the memory space name and folder path; use those provided values and report that discovery was attempted.

If the space is external to the solution and should be tracked as a solution resource:

```bash
uip solution resources add \
  --source remote \
  --kind MemorySpace \
  --name "<MEMORY_SPACE_NAME>" \
  --folder-path "<FOLDER_PATH>" \
  --output json
```

If no memory space exists, stop and ask the user to create or provide one. Do not invent a memory space name and continue silently.

### 2. Attach the memory space to the agent

```bash
uip agent memory add SupportRecall \
  --memory-space "<MEMORY_SPACE_NAME>" \
  --folder-path "<FOLDER_PATH>" \
  --threshold 0.25 \
  --result-count 5 \
  --search-mode hybrid \
  --field userQuestion=1 \
  --path "<AGENT_PROJECT_DIR>" \
  --output json
```

`SupportRecall` is the feature name inside the agent. Choose a short PascalCase or kebab-free name that describes how the agent will use the memory.

Options:

| Option | Meaning |
|---|---|
| `--memory-space` | Tenant memory space name to attach |
| `--folder-path` | Folder path containing the memory space |
| `--reference-key` | Optional solution resource key, if already known |
| `--description` | Human-readable feature description |
| `--threshold` | Retrieval score threshold; default `0` |
| `--result-count` | Number of memory results; default `3` |
| `--search-mode` | `hybrid` or `semantic`; default `hybrid` |
| `--field name=weight` | Input field weighting; repeat for multiple fields |
| `--disable-dynamic-few-shot` | Attach the memory space without runtime retrieval |
| `--path` | Agent project directory; default `.` |

### 3. Seed optional memory items

Add items only when the user explicitly wants seed examples or defaults in the agent project.

```bash
uip agent memory item add SupportRecall customer-tier gold \
  --memory-type episodic \
  --feedback-id "<FEEDBACK_ID>" \
  --metadata '{"source":"seed"}' \
  --path "<AGENT_PROJECT_DIR>" \
  --output json
```

Valid memory item types are:

| Value | Numeric | Use |
|---|---:|---|
| `episodic` | `0` | General recall examples |
| `escalation` | `1` | Escalation-related memory |

Episodic memory items require `--feedback-id`; use the feedback ID for the conversation, trace, or support example the seed item came from. `--metadata` must be a JSON object, not an array or scalar. Adding an item with an existing key updates that item.

### 4. Verify

```bash
uip agent memory list --path "<AGENT_PROJECT_DIR>" --output json
uip agent memory item list SupportRecall --path "<AGENT_PROJECT_DIR>" --output json
uip agent refresh "<AGENT_PROJECT_DIR>" --output json
uip agent validate "<AGENT_PROJECT_DIR>" --output json
uip solution resources refresh --output json
```

After refresh, inspect `<AGENT_PROJECT_DIR>/bindings_v2.json` only to verify that a `memorySpace` binding exists. Do not edit it. Run `uip solution resources refresh` from the solution root so the solution resource catalogue sees the memory binding. Do not skip refresh because the memory space name/folder were provided, because `bindings_v2.json` looks correct, or because publish/deploy is out of scope. If refresh fails due authentication, leave the generated files intact and report the failed refresh command.

## Remove

Remove a feature by feature name or ID:

```bash
uip agent memory remove SupportRecall --path "<AGENT_PROJECT_DIR>" --output json
```

Remove by memory space name only when you also pass the folder path:

```bash
uip agent memory remove "<MEMORY_SPACE_NAME>" \
  --folder-path "<FOLDER_PATH>" \
  --path "<AGENT_PROJECT_DIR>" \
  --output json
```

Remove a seed item by key or ID:

```bash
uip agent memory item remove SupportRecall customer-tier \
  --path "<AGENT_PROJECT_DIR>" \
  --output json
```

## Generated Shape

The CLI writes a feature file at:

```text
<AGENT_PROJECT_DIR>/features/SupportRecall/feature.json
```

Expected shape, for review only:

```json
{
  "$featureType": "memorySpace",
  "id": "<uuid>",
  "referenceKey": null,
  "folderPath": "Shared",
  "name": "SupportRecall",
  "memorySpaceName": "support-memory",
  "description": null,
  "isEnabled": true,
  "dynamicFewShotSettings": {
    "isEnabled": true,
    "threshold": 0.25,
    "resultCount": 5,
    "searchMode": "hybrid",
    "fieldSettings": [
      {
        "id": "<uuid>",
        "name": "userQuestion",
        "weight": 1
      }
    ]
  },
  "items": [
    {
      "id": "<uuid>",
      "key": "customer-tier",
      "value": "gold",
      "memoryType": 0,
      "feedbackId": "<feedback-id>",
      "description": null,
      "metadata": {
        "source": "seed"
      }
    }
  ]
}
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `required option '--memory-type <type>'` | `item add` always requires a memory type | Add `--memory-type episodic` or `--memory-type escalation` |
| `required option '--feedback-id <feedbackId>'` | Episodic `item add` requires a source feedback ID | Pass `--feedback-id "<FEEDBACK_ID>"` with `--memory-type episodic` |
| `Invalid memory-type value` | Unsupported type | Use `episodic`, `escalation`, `0`, or `1` |
| `Invalid metadata JSON` | Metadata is malformed or not an object | Pass a valid JSON object, e.g. `'{"source":"seed"}'` |
| `Memory space "<name>" matches by memory space name` | More than one feature references the same memory space name | Pass `--folder-path`, use the feature name, or use the feature ID |
| No `memorySpace` binding after refresh | Refresh was not run after the memory edit | Run `uip agent refresh "<AGENT_PROJECT_DIR>" --output json` |
