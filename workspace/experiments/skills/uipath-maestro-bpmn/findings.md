# Findings — uipath-maestro-bpmn

Three codifiable procedures identified and scripted. The existing `validator/validate-bpmn.mjs` (all 19 PO.Frontend rules) is excluded — already a skill script.

---

## 1. Diagram generation — BUILD-MODEL

**Source:** `references/structural-bpmn.md §Diagram interchange`

**Procedure:** Given a BPMN file with a `bpmn:process` but no `bpmndi:BPMNDiagram`, parse all flow nodes and sequence flows, assign left-to-right positions (BFS from start events), emit one `BPMNShape` per node and one `BPMNEdge` per flow. Fixed dimensions: tasks 100×80, events 36×36, gateways 50×50. Nodes at the same BFS level are sorted by id and stacked vertically (30px gap). Deterministic for any process graph.

**Script:** `scripts/generate_diagram.py`

```bash
python3 scripts/generate_diagram.py --bpmn <file.bpmn> [--out <output.bpmn>]
```

- `--bpmn`   Source .bpmn file (bpmn:process required; existing BPMNDiagram replaced)
- `--out`    Output path (default: overwrite `--bpmn` in place)

Example:
```bash
python3 scripts/generate_diagram.py --bpmn MyFlow/MyFlow.bpmn
# stdout: Generated: 5 shapes, 4 edges → MyFlow/MyFlow.bpmn
```

**Turn savings:** The agent normally calculates x/y coordinates for every node across multiple turns. This script handles the full layout in one call.

**Your judgment:** The script places shapes in BFS topological order. For processes with parallel branches or large levels, manually adjust positions with `Edit` afterward if the Studio Web canvas overlap is unacceptable. Always run `validator/validate-bpmn.mjs` after.

**Tests:** `script-tests/generate_diagram/`

---

## 2. Package metadata scaffolding — FORMAT-CONVERT / BUILD-MODEL

**Source:** `references/shared/local-metadata-regeneration-guide.md §Minimal Local Metadata Shape`, `§Entry Point Rules`, `§Binding Rules`

**Procedure:** Given a BPMN source file, derive all five package metadata files by reading root start events with `uipath:entryPointId`, scoping variables to entry points via `elementId`, and applying the documented JSON shapes. For projects with connector dependencies, this script generates the placeholder-safe shape; the full resource metadata requires CLI enrichment.

**Script:** `scripts/scaffold_metadata.py`

```bash
python3 scripts/scaffold_metadata.py --bpmn <file.bpmn> --out-dir <dir>
```

- `--bpmn`      Source .bpmn file
- `--out-dir`   Directory to write the five JSON files

Example:
```bash
python3 scripts/scaffold_metadata.py --bpmn InvoiceTriage/InvoiceTriage.bpmn --out-dir InvoiceTriage/
# writes: project.uiproj, operate.json, entry-points.json, bindings_v2.json, package-descriptor.json
```

Entry point schema derivation:
- `inputSchema` — variables with `elementId` matching the start event id
- `outputSchema` — variables with no `elementId` (global output scope)

**Your judgment:** For projects with `Intsvc.*` connector nodes, the generated `bindings_v2.json` will have an empty `resources` array. Do not run `uip solution upload` or `uip maestro bpmn pack` until enrichment has populated the resource entries. Use `scripts/check_metadata_drift.py` to verify consistency before packing.

**Tests:** `script-tests/scaffold_metadata/`

---

## 3. Package metadata drift check — VALIDATE

**Source:** `references/shared/local-metadata-regeneration-guide.md §Drift Handling`, `§Entry Point Rules`, `§Binding Rules`

**Procedure:** Compare the five package metadata files against the BPMN source. Exits 1 with labeled `DRIFT:` findings if anything diverges. Checks:
- Each root start event's `uipath:entryPointId` has a matching `entry-points.json` entry with correct `id` and `filePath` (`/content/<bpmn>#<startEventId>`)
- `bindings_v2.json` has `"version": "2.0"` and a `resources` array
- `operate.json` `main` matches the BPMN filename
- `package-descriptor.json` `content` lists `content/<bpmn>` and the three generated JSON files

**Script:** `scripts/check_metadata_drift.py`

```bash
python3 scripts/check_metadata_drift.py --bpmn <file.bpmn> --project-dir <dir>
```

- `--bpmn`          Source .bpmn file
- `--project-dir`   Directory containing the five metadata JSON files

Example:
```bash
python3 scripts/check_metadata_drift.py \
  --bpmn InvoiceTriage/InvoiceTriage.bpmn \
  --project-dir InvoiceTriage/
# OK: 5 checks passed, no drift detected
# or: DRIFT: entry-points.json: missing entry for entryPointId='Entry_ManualStart'
```

**Turn savings:** Replaces 2–3 turns of manual file comparison before each pack or upload.

**Tests:** `script-tests/check_metadata_drift/`

---

## Excluded (already scripted)

- **BPMN validation** — `validator/validate-bpmn.mjs` runs all 19 PO.Frontend rules. See `validator/README.md`.
