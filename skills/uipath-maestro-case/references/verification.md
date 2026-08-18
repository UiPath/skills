# Verification gates

Use these gates after the direct structural/detail passes and after every
brownfield edit. They complement—never replace—`uip maestro case validate`.

## Gate order

1. Sidecar and resolved-resource checks
2. Deterministic Case JSON checks
3. Deterministic SDD parity checks for greenfield/rebuild work
4. Full CLI validation

Stop at the first failing gate, repair the named path, then re-run that gate.

## 1. Sidecar and resource invariants

Verify mechanically:

- Every `entry-points.json` entry projects all declared In/Out arguments with
  matching names, types, and required arrays.
- `bindings_v2.json` matches top-level `caseplan.json.bindings` for every
  resource; no binding is present on only one side.
- Every selected non-connector resource remains a concrete task with
  `data.name` and `data.folderPath` bound through complete root bindings.
- Each non-connector binding pair has a `resourceKey` derived from its own
  name/folder defaults—not a copied tenant UUID.
- Every resolved connector activity, event trigger, and connector-bound rule
  carries the spliced `caseShape.context` and required Connection/Folder root
  bindings. A `typeId` + `connectionId`-only shape is incomplete.
- Every generated task output ID is globally unique.
- Formal argument slot IDs are synthetic IDs, distinct from readable
  companion names.
- No unresolved `$xref` marker survives.
- Every `=vars.<id>` reference resolves.
- Every declared Out argument has a producer, default, or explicit open item.

Regenerate a sidecar once when its source Case JSON is authoritative. Halt if
parity remains divergent after regeneration.

## 2. Deterministic Case JSON

Run:

```bash
python3 <skill-dir>/scripts/check_case_contract.py check-caseplan \
  --caseplan <caseplan.json> --output json
```

The checker currently enforces high-confidence source invariants including:

- `edges: []` and top-level `layout`
- global ID uniqueness
- unique stage/task display names
- closed task-type enum
- stage reachability
- root case-completion rule

Treat every `severity: error` finding as blocking. The `code` and `path` are
stable automation interfaces; human wording may become clearer over time.

## 3. Deterministic SDD parity

Greenfield and rebuild work must run:

```bash
python3 <skill-dir>/scripts/check_case_contract.py check-parity \
  --sdd <sdd.md> --caseplan <caseplan.json> --output json
```

The parity checker compares normalized semantics, not IDs, formatting, or
array serialization. It checks:

- Case name, description, identifier, Case App, and output-passing mode
- variable/argument presence, category, type, and explicit defaults
- exact stage and task inventory
- exact trigger inventory, semantic names, and trigger service types
- stage kind and required behavior
- stage/task rule types and completing/exit pairing
- task type, required, run-once, and task-entry behavior
- parallel task-set grouping for tasks with identical entry behavior
- case-exit behavior

Missing and extra declarations are errors. A CLI-valid task with the wrong
type, grouping behavior, required flag, or run-once flag is still a parity
failure.

IDs are intentionally excluded from parity because they are implementation
identities. Resource tenant IDs are checked against resolution evidence and
bindings, while portable resource names remain authoritative in the SDD.

## 4. Full CLI validation

After deterministic gates pass:

```bash
uip maestro case validate <project-or-caseplan-path> --output json
```

Never run validate twice without an intervening edit. A legal repair loop is:

```text
validate -> inspect finding -> targeted edit -> deterministic re-check -> validate
```

Allow three failed repair cycles. On the third failure, show the remaining
findings and ask:

- Retry with fix
- Pause for manual edit
- Abort

Do not reset the counter after the user selects retry.

## Completion evidence

Before reporting completion, retain:

- checker summaries and zero findings
- full CLI validation success payload
- unresolved placeholder/resource list
- open-item count from `build-issues.md`
- paths to `sdd.md`, `caseplan.json`, and sidecars

Do not claim parity from inspection alone or validation from an earlier run.

<!-- END: verification.md -->
