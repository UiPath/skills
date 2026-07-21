# uipath-maestro-case July 20 Coder-Eval Review

## Scope

This PR addresses the `uipath-maestro-case` coder-eval failures from the July 20/21 failure bundle. The fixes are contract-level guidance and eval prompt changes; they do not reintroduce validator graph edges or change checker semantics.

## Failure Summary

| Eval | Observed result | Root issue | PR fix |
|---|---|---|---|
| `skill-case-phase-0-loan-origination` | Turn timed out after 2400s before writing a draft | Phase 0 draft-only requests still allowed the agent to read large downstream docs and over-deliberate instead of writing `sdd.draft.md` | Added a draft-only fast path to the skill and the loan eval prompt: write `sdd.draft.md`, do not read implementation docs, and stop before finalization/build |
| `skill-case-aged-invoice-structural` | Timed out mid-build; partial checker failed because the event trigger lost `aged_invoice_cases` | Placeholder event triggers kept `data.uipath` minimal but did not preserve the authored source object anywhere visible | Event placeholder docs now require `source object: <object-name>` in description while keeping `data.uipath` limited to `serviceType` |
| `skill-case-athena-cm-event` | All checks passed, but the agent exhausted max turns after success | The eval prompt did not make validation the hard completion boundary | Athena prompt now says to stop immediately after validate passes and not enter Phase 5/6 |
| `skill-case-e2e-expense-runnable` | Timed out mid-build; partial checker found `bindings_v2.json` used alias `NameToAgeFixed2` instead of deployed name `API Workflow` | Registry handoff was explicit for `action` and `case-management`, but not all runnable non-connector task types | Planning and `bindings_v2` docs now make `registry-resolved.json.selected` authoritative for `process`, `agent`, `rpa`, `api-workflow`, `action`, and `case-management` |

## Review Map

| Area | Files |
|---|---|
| Phase 0 draft-only stop | `skills/uipath-maestro-case/SKILL.md`, `skills/uipath-maestro-case/references/phase-0-interview.md`, `tests/tasks/uipath-maestro-case/phase_0_to_case/loan_origination/loan_origination.yaml` |
| Event trigger placeholder identity | `skills/uipath-maestro-case/references/plugins/triggers/event/planning.md`, `skills/uipath-maestro-case/references/plugins/triggers/event/impl-json.md`, `skills/uipath-maestro-case/references/placeholder-tasks.md`, `skills/uipath-maestro-case/SKILL.md` |
| Registry-selected binding names | `skills/uipath-maestro-case/references/planning.md`, `skills/uipath-maestro-case/references/bindings-v2-sync.md`, `tests/tasks/uipath-maestro-case/e2e_expense_runnable/expense_runnable_e2e.yaml` |
| Eval stop boundaries | `tests/tasks/uipath-maestro-case/aged_invoice_structural/aged_invoice_structural.yaml`, `tests/tasks/uipath-maestro-case/athena_cm_event/athena_cm_event.yaml`, `tests/tasks/uipath-maestro-case/e2e_expense_runnable/expense_runnable_e2e.yaml` |
| Regression coverage | `tests/tasks/uipath-maestro-case/test_eval_contracts.py` |

## Reviewer Checklist

- Confirm the Phase 0 wording applies only to explicit draft-only runs and does not weaken the normal Phase 0 approve-to-`sdd.md` path.
- Confirm event trigger placeholders still keep `data.uipath` to `{ "serviceType": "Intsvc.EventTrigger" }` only.
- Confirm the authored event source is preserved outside `data.uipath`, so unresolved trigger nodes remain inspectable and deterministic checkers can verify intent.
- Confirm all non-connector resource task types use the selected registry object for `name`, `folder-path`, and `taskTypeId`.
- Confirm the eval prompts stop after validation and do not accidentally ask the agent to run debug/publish inside the harness.

## Validation

Red check:

```bash
python3 tests/tasks/uipath-maestro-case/test_eval_contracts.py
```

This failed on `origin/main` with missing draft-only, event-placeholder, registry-handoff, and post-validate stop contracts.

Green checks:

```bash
python3 tests/tasks/uipath-maestro-case/test_eval_contracts.py
PYTHONPATH=<pytest-target> python3 -m pytest \
  tests/tasks/uipath-maestro-case/test_eval_contracts.py \
  tests/tasks/uipath-maestro-case/athena_cm_event/test_checkers.py \
  tests/tasks/uipath-maestro-case/e2e_expense_runnable/test_check_expense_runnable_structure.py \
  tests/tasks/uipath-maestro-case/_shared/test_sdd_check.py \
  tests/tasks/uipath-maestro-case/_shared/test_case_check.py
```

Result: `28 passed`.

YAML parse check:

```bash
python3 - <<'PY'
import yaml
for path in [
    "tests/tasks/uipath-maestro-case/phase_0_to_case/loan_origination/loan_origination.yaml",
    "tests/tasks/uipath-maestro-case/aged_invoice_structural/aged_invoice_structural.yaml",
    "tests/tasks/uipath-maestro-case/athena_cm_event/athena_cm_event.yaml",
    "tests/tasks/uipath-maestro-case/e2e_expense_runnable/expense_runnable_e2e.yaml",
]:
    with open(path, encoding="utf-8") as f:
        yaml.safe_load(f)
PY
```

All four changed eval YAML files parsed successfully.

Coder-eval dry-run:

```bash
cd tests
.venv/bin/coder-eval plan \
  tasks/uipath-maestro-case/phase_0_to_case/loan_origination/loan_origination.yaml \
  tasks/uipath-maestro-case/aged_invoice_structural/aged_invoice_structural.yaml \
  tasks/uipath-maestro-case/athena_cm_event/athena_cm_event.yaml \
  tasks/uipath-maestro-case/e2e_expense_runnable/expense_runnable_e2e.yaml \
  -e experiments/default.yaml
```

Result: all four task files are valid. The dry-run warned that `ANTHROPIC_API_KEY` was unset, but LLM Gateway was configured and validation succeeded.

## Not Changed

- No graph-edge or transition model changes; v23 edge-retired behavior remains intact.
- No checker loosening.
- No publish/debug behavior added to eval tasks.
