# Migration Trace Guide — source-to-target links written during execution

Read this guide whole when executing an extracted genome with its source export. A trace records **where the author claims each source behavior was implemented**, not whether that implementation is correct. It is required for migrations and refactors regardless of the Source fidelity answer: changing names, grouping, project boundaries or implementation language does not remove provenance.

## Scope and ownership

Keep `migration/trace/` outside every deliverable project. It contains one source inventory, one solution-level index (`trace.json`) and per-part fragments (`parts/<part>.json`). A standalone migration uses the same layout. No change to the genome's Source Map, source export, target display names or native target IDs is required.

Before authoring, derive the inventory from the original export with its framework reader (for a UiPath source, the inventory procedure of [uipath-source-guide.md](uipath-source-guide.md)), retaining native identities and raw locations. A run-specific normalizer may convert that reader's output to the format below; it must not infer the inventory from the generated target, the genome's summarized steps, or the mappings. Include operations, conditions, routes, calls, argument bindings, variable initialization and exception constructs. Include disabled, unsupported and structural items too; classify them rather than silently discard them. Record export scope and reconcile the inventory with the reader's object/page/node counts and the Source Map's covered and not-covered objects. Do not invent a deployed call order where the source lacks one.

Framework-specific enumeration stays in the framework pack, or in the UiPath source guide for UiPath sources. This checker does **not** prove that a normalizer enumerated every source item, that a caller chose every target project, or that a native identity label describes its raw location. The project owner checks those against the original source, reader output and solution inventory before accepting the trace. If the reader cannot enumerate a construct, record the gap as unresolved; do not report complete source coverage.

Use the native identity scoped to its owning object/page, not a display name or a short human alias. A repeated stage ID in two containers denotes two items. XML attribute guards retain native IDs where the export has them; JSON locations and code spans retain their owning scope in `identity`. Paths identify files relative to the relevant root, never personal absolute paths.

Each part updates its fragment as it authors the corresponding code. Forks write disjoint fragments; the project owner owns the index and reconciles source-item ownership before accepting a part. A split or merge is one record with sets of source and target references, not duplicate records for one source item. Refresh final target locations and file hashes **after** handoff wiring, Object Repository linking and the last save. Any later deliverable edit requires another trace check against updated references; do not merely refresh hashes over stale locations.

## Version 1 format

All files are UTF-8 JSON objects with `version: 1`. Unknown fields and duplicate keys are errors. The examples below use symbolic hash placeholders; replace them with lowercase SHA-256 hex digests of the exact file bytes.

### Source inventory

`source-inventory.json`:

```json
{
  "version": 1,
  "framework": "<framework>",
  "scope": "<export identity, selected entry points and explicit exclusions>",
  "artifacts": [{"path": "release.xml", "sha256": "<file hash>"}],
  "items": [{
    "id": "s1",
    "identity": ["<container native ID>", "<page native ID>", "<stage native ID>"],
    "artifact": "release.xml",
    "kind": "behavior",
    "locator": {"kind": "xml", "path": [0, 2], "tag": "stage", "attributes": {"stageid": "<stage native ID>"}}
  }]
}
```

`id` is the trace-local unique reference used by fragments; `identity` is the nonempty array of scoped native identity segments. `kind` is `behavior` or `structure` (for comments, labels and other nonexecuting constructs). Every source artifact under `--source-root` must be listed exactly once with its hash; keep this root limited to original exports or their immutable unpacked contents, not generated catalogs. For an unpacked export, retain the original archive identity and extraction provenance in the scope record's working evidence. An unresolved external dependency remains explicit; it is not an excuse to remove its call from the inventory.

### Solution index

`trace.json`:

```json
{
  "version": 1,
  "sourceInventorySha256": "<hash of source-inventory.json>",
  "targetArtifacts": [
    {"path": "Worker/project.json", "sha256": "<file hash>"},
    {"path": "Worker/Main.xaml", "sha256": "<file hash>"}
  ],
  "fragments": ["parts/worker-1.json"]
}
```

Target paths are relative to `--target-root`; fragment paths are relative to the index. List all deliverable files in the selected projects, including manifests, configuration, Object Repository definitions and packaged data, not only mapped workflows. Include solution-level manifests/resource definitions outside the projects in this same array and pass each through `--solution-file`. The checker compares this file set with disk. Its only target directory exclusions are `.git`, `.local`, `.vs`, `bin`, `obj`, `node_modules` and `.venv`; behavior-bearing files must not live there. Source directories have no such exclusions. An added or removed file, including an unmapped helper, invalidates the index. The orchestrator separately verifies every built project and library is passed through `--project` and all solution-level inputs through `--solution-file`.

### Part fragment

```json
{
  "version": 1,
  "records": [{
    "sources": ["s1"],
    "targets": [{
      "artifact": "Worker/Main.xaml",
      "role": "decision",
      "locator": {"kind": "xml", "path": [0, 0], "tag": "{http://schemas.microsoft.com/netfx/2009/xaml/activities}If", "attributes": {}}
    }],
    "status": "mapped",
    "relation": "direct",
    "reason": "This branch consumes the connection probe result."
  }]
}
```

Every record requires `sources`, `targets`, `status` and a nonempty `reason`. Each inventoried source item occurs exactly once across all fragments. Sources and targets can be grouped many-to-many. A target may appear in several records when behavior is shared; that is not evidence that every caller uses it correctly.

| Status | Required interpretation |
|---|---|
| `mapped` | Target locations provided; no correctness claim |
| `changed` | Target locations plus `decision`: a reference to the user ruling or explicitly permitted genome/source-defect decision; not merely the author's preference |
| `omitted` | Not implemented; no target locations; reason is an outstanding gap, not a pass |
| `excluded` | Outside selected scope; no target locations; reason cites the scope decision, not an automatic waiver |
| `unresolved` | Cannot yet establish a counterpart or interpret the source; no target locations; blocks the check's successful exit |
| `structural` | Only source items inventoried as `structure`; targets optional; explains what became of the construct |
| `added` | No sources; target locations and reason for added behavior |

`mapped`, `changed` and `added` also require `relation`: `direct`, `split`, `merge`, `rewrite`, `moved`, `shared` or `group`. These describe author intent, not inferred equivalence. `omitted`, `excluded` and `unresolved` must not claim target locations. An unfinished migration can publish a clearly partial report; it must not manufacture mappings to obtain a passing trace.

Target `role` describes what the location does (for example `decision`, `probe`, `configuration`, `call-site` or `implementation`). Point at the consuming branch for a decision, not just the probe that produces its input. A source choice implemented by several `If` activities points at the group, not an adjacent assignment. An inlined operation points at its actual expression, not its containing file alone.

For a shared helper, use relation `shared`, include targets with both `call-site` and `implementation` roles and record `bindings`, an array of `{ "source": "<source expression/reference>", "target": "<target parameter/expression>", "direction": "in|out|inout|return" }`. An empty array explicitly means no arguments or return binding. Keep distinct call occurrences separate; include guards, output assignments and side effects in the mapped region as needed. The checker validates binding shape, not dataflow or helper equivalence. A reviewer still reads the actual call and callee.

### Raw locations

Every source item and target reference uses one locator:

- **XML**: `{ "kind": "xml", "path": [0, 2], "tag": "<expanded XML tag>", "attributes": {"<expanded attribute name>": "<value>"} }`. Zero-based child indexes from the document element, counting all element children including property elements; comments and processing instructions are ignored. An empty path identifies the document element. Use expanded `{namespace}name` tags/attributes where namespaced. Include native ID attributes when present; never choose the first stage with a matching ID across containers.
- **JSON**: `{ "kind": "json", "pointer": "/nodes/0" }`. RFC 6901 pointer into the exact hashed JSON artifact; empty string identifies its root. Include the item's native owning identity in the source inventory.
- **Text/code**: `{ "kind": "text", "start": 0, "end": 42, "sha256": "<range hash>", "symbol": "<optional qualified signature>" }`. Half-open byte offsets in the exact file, with a hash of the selected bytes. `symbol` is a label, not a symbol-resolution or semantic check. Use a precise statement/method region, not an entire project. Coded target references do not establish that an independent reviewer supports the language's behavior.

No locator may escape its root or traverse a symlink. Hashes bind locations to the final bytes; they do not prove a claimed role or source identity is true. Keep the trace local with the migration evidence. It can contain customer logic and sensitive binding expressions: omit secret values, use credential references and apply the run's secret scrub to labels/reasons/bindings. Never scrub structural paths, IDs or hashes into ambiguous placeholders, never copy raw code into trace text, and never send a trace to a provider without the same authorization and filtering as the underlying project.

## Check and report

Run after each accepted part and once after the solution's final mutations:

```bash
python3 "<SKILL_DIR>/scripts/check-migration-trace.py" \
  --inventory "<WORKING_DIR>/trace/source-inventory.json" \
  --trace "<WORKING_DIR>/trace/trace.json" \
  --source-root "<ORIGINAL_EXPORT_DIR>" \
  --target-root "<SOLUTION_DIR>" \
  --project "Worker" --project "SharedLibrary" \
  --solution-file "Automation.uipx" --output json
```

Use `python` on Windows. For a standalone project use its directory as `--target-root` and `--project .`, with the trace folder outside it. At a part boundary, check the run's cumulative fragments and the current files, not just the last part; unfinished source items remain `unresolved`, so the nonzero exit is expected and recorded. The owner checks an accepted part's items have no unresolved records. Never delete future work from the source inventory to make an intermediate check pass.

The checker reads data only. It rejects stale/missing artifacts, mismatched file sets, broken raw locations, duplicate source identities or accounting, missing dispositions, malformed records and unsupported formats. It makes no network calls and loads no project code. Bounds are 20,000 files, 512 MiB aggregate read bytes, 64 MiB per file, 16 MiB per parsed artifact/JSON document, and 100,000 entries/nodes or directory entries per traversal. Exhaustion is an error, not a partial success; report it and decide whether to partition the selected source with independently reconciled scope or revise the bounds.

Report separately:

1. **Inventory scope reviewed**: original-export/reader reconciliation, selected projects and any unsupported constructs or missing dependencies; not established by this checker.
2. **Trace integrity**: checker result and counts of source items per disposition (`added` counts target-only records); unresolved items keep exit status nonzero. Hashes must still match when the report is handed over.
3. **Migration gaps**: changed, omitted, excluded and unresolved items with their reasons/decision references. Accounting for an omission does not implement it.
4. **Build/runtime gates and acceptance verdicts**: the existing execution report, unchanged by a valid trace.
5. **Independent behavior review**: performed with evidence, or not run. The trace is input to such a review, never fidelity credit by itself.

An optional human differences table can be generated from the fragments. It is not the source of truth and never replaces unchanged-step records. Older builds without a trace remain untraced until audited; do not backfill uncertain matches as facts.
