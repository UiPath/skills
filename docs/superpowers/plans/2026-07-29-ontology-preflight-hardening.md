# Ontology Preflight Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make ontology creation and deployment catch artifact incompatibilities before any UiPath upload, while allowing missing mappings to be generated from the available model and entity metadata.

**Architecture:** Keep `uipath-ontologies`, `uipath-ontology-authoring`, and `uipath-ontology-modeler` as independent sibling skills. Add a neutral, executable ontology preflight utility that both authoring and modeler can invoke; neither skill imports the other’s files. Authoring remains responsible for deployment sequencing, while modeler remains responsible for artifact generation.

**Tech Stack:** Python 3 standard library, Markdown skill instructions, unittest fixtures, UiPath `uip ont` CLI.

## Global Constraints

- Missing mapping is a supported generation path, not an automatic failure.
- No structural file/import dependency between the three skills.
- Mapping upload remains the final deployment trigger.
- No upload occurs until local gates and backend `Data.valid` checks pass.
- Existing ontology CRUD behavior remains unchanged.

---

### Task 1: Define failing preflight scenarios

**Files:**
- Create: `tests/scripts/test_ontology_preflight.py`
- Create: `tests/tasks/uipath-ontology-modeler/_shared/fixtures/preflight/`

**Interfaces:**
- Tests consume artifact directories and assert deterministic preflight diagnostics.
- Later tasks implement the validator and skill contracts required by these tests.

- [ ] Add fixtures for: old IRI in one artifact, mapping term absent from schema, FK mapping without an object property, action without `fno:returns`, non-global `shape:` prefix, and a missing mapping with sufficient schema/entity metadata.
- [ ] Add tests asserting the first five cases fail with named gate IDs.
- [ ] Add a test asserting missing mapping is classified as `GENERATE_MAPPING`, not `INVALID_INPUT`, when class/entity metadata is complete.
- [ ] Run `python3 -m unittest -v tests/scripts/test_ontology_preflight.py`; confirm the new tests fail because the validator does not yet exist.

### Task 2: Implement the neutral ontology preflight utility

**Files:**
- Create: `tools/ontology_preflight.py`
- Modify: `tests/scripts/test_ontology_preflight.py`

**Interfaces:**
- Command: `python3 tools/ontology_preflight.py --workdir <dir> --ontology-name <slug> --mapping-mode auto|required`
- Exit `0` only when all available artifacts pass and any missing mapping is safely generatable.
- JSON output fields: `status`, `gate_results`, `mapping_status`, `errors`, `warnings`.

- [ ] Implement artifact discovery by type without assuming that every function/action file has a fixed filename.
- [ ] Implement IRI consistency checking across OFN, constraints, functions, actions, and mapping.
- [ ] Implement cross-file term checking for mapping, constraints, function bodies, and action bodies against the OFN schema.
- [ ] Implement relationship checking: FK-shaped mapping joins require a declared OWL object property unless explicitly exempted.
- [ ] Implement action contract checking: every action has an output declaration and matching `fno:returns` metadata.
- [ ] Implement namespace checks, including the global `https://ontology.uipath.com/shapes#` prefix.
- [ ] Implement mapping classification: `PRESENT_VALID`, `PRESENT_INVALID`, `GENERATE_MAPPING`, or `BLOCKED_AMBIGUITY`; after generation creates a mapping file, report `PRESENT_VALID`.
- [ ] Add tests for every gate, then run the focused unittest suite until green.

### Task 3: Make mapping generation an explicit modeler contract

**Files:**
- Modify: `skills/uipath-ontology-modeler/SKILL.md`
- Modify: `skills/uipath-ontology-authoring/SKILL.md`
- Modify: `tests/tasks/activation/uipath-ontology-modeler.jsonl`
- Modify: `tests/tasks/activation/uipath-ontology-authoring.jsonl`

**Interfaces:**
- Modeler accepts `MAPPING_STATUS: supplied|generate` and, for generation, requires `CLASS_MAP`, OFN classes/properties, entity IDs, folder ID, and field metadata.
- Modeler returns `MAPPING_PATH`, `MAPPING_STATUS`, `MAPPING_GATE`, and unresolved ambiguities.
- Authoring consumes that result and never uploads a mapping marked invalid or incomplete.

- [ ] Replace the hard requirement for a pre-existing mapping with the supplied-or-generated rule.
- [ ] Define the minimum metadata needed to infer a mapping and the exact ambiguity conditions that require stopping.
- [ ] Require generated mappings to use the supplied ontology IRI, folder key, entity IDs, and schema terms.
- [ ] State that mapping generation is modeler work in both standalone and delegated modes; authoring still owns the final upload.
- [ ] Add activation cases for plain-domain generation, delegated generation with no mapping, and partial-input ambiguity.

### Task 4: Enforce preflight before backend calls and deployment

**Files:**
- Modify: `skills/uipath-ontology-authoring/SKILL.md`
- Modify: `skills/uipath-ontology-modeler/SKILL.md`
- Modify: `skills/uipath-ontologies/SKILL.md`
- Modify: `tests/scripts/test_ontology_skill_structure.py`

**Interfaces:**
- Authoring invokes the neutral preflight utility before `uip ont artifact validate` and again after any repair.
- Modeler invokes the same utility before returning artifacts or uploading tier-2 artifacts.
- Ontologies skill remains CRUD-only and continues routing creation/deployment to authoring/modeler.

- [ ] Add a mandatory “preflight exact upload set” step before ontology creation or artifact upload.
- [ ] Require repair of all failed gates, not merely reporting them.
- [ ] Require backend validation `Data.valid: true` for every artifact after local preflight.
- [ ] Preserve upload order: schema, constraints/functions/actions, mapping last.
- [ ] Require final `uip ont get` state verification and artifact inventory verification.
- [ ] Add structural tests for the new command, mapping states, upload order, and no sibling-file links.

### Task 5: Verify against the P2P process-printer case

**Files:**
- Modify: `tests/tasks/uipath-ontology-modeler/_shared/fixtures/` only if a reusable sanitized fixture is needed.

- [ ] Run the preflight utility against the P2P artifact workdir with the mapping removed; confirm it requests generation rather than failing immediately.
- [ ] Generate the mapping from the schema/class map/entity metadata.
- [ ] Re-run all local gates and backend validations.
- [ ] Confirm deployment sequencing produces `DEPLOYED` only after mapping upload.
- [ ] Run the full ontology structure and activation test suites.
- [ ] Run `git diff --check` and verify no broken sibling-file links.

## Verification Commands

```bash
python3 -m unittest -v tests/scripts/test_ontology_preflight.py
python3 -m unittest -v tests/scripts/test_ontology_skill_structure.py
python3 tools/ontology_preflight.py --workdir <workdir> --ontology-name <name> --mapping-mode auto
git diff --check
```

Plan complete and saved to `docs/superpowers/plans/2026-07-29-ontology-preflight-hardening.md`.
