# Contradicting-instructions mock

Overlay for `../../smoke/align_group_field_instructions.yaml`. List it **second**
in `template_sources`, after `../mock_template`, so `mocks/uip` here wins the PATH
shadow while the base template's `mocks/curl` and seeded `calls.log` /
`calls.jsonl` remain.

## Why it exists

`SKILL.md:112` (Common Pitfalls) and `improve-prompts-guide.md:29` — each field
group (label_def) has its **own** `instructions`, which the model sees alongside
the per-field ones. `fields update-prompts` edits only the per-field text. When
the two contradict, the model gets opposing signals, and rewriting the *field*
prompt cannot fix it: the group instruction keeps overriding.

`smoke/update_group_instructions.yaml` asserts `groups update-prompts --updates`
ran with the requested text — that grades the **write**, on a project with no
conflict, so it cannot grade whether the agent **noticed** one. This fixture
builds the conflict.

## Fixture

One project, `freight_bills-8e2a4c67-ixp` (Title `Freight_Bills`), with a
deliberate contradiction inside one field group:

| Level | Instruction |
|---|---|
| group `Freight Charges` | "Extract only the charges shown on the **FIRST** page of the freight bill. Ignore any continuation or summary pages that follow." |
| field `Fuel Surcharge` | "…listed in the accessorial summary table on the **LAST** page of the bill, after the line-item detail." |

The group forbids exactly where the field says to look.

`get-metrics` scores it accordingly:

| Field | F1 | Precision | Recall | Diagnosis |
|---|---|---|---|---|
| `Carrier Name` | 0.94 | 0.95 | 0.93 | healthy |
| `Base Freight` | 0.91 | 0.93 | 0.89 | healthy |
| `Fuel Surcharge` | **0.19** | 0.86 | **0.11** | Recall ≪ Precision → **RECALL** |

Recall-dominated failure is the guide's signal for "the model cannot find the
value" rather than "the model picks the wrong one" — which is exactly what a
location instruction the group excludes would produce. The two siblings are
healthy so the diagnosis lands on one field, and the taxonomy holds the only
available explanation.

`FieldId` values in `get-metrics` match `field_id` in the taxonomy, so the
name↔metric join the guide describes (`improve-prompts-guide.md:90`) actually
resolves. If you change an id, change both.

## The trap

An agent following the improve loop mechanically does this:

1. read metrics → `Fuel Surcharge` is low
2. Recall < Precision → classify as **RECALL**
3. the documented RECALL fix is "better describe WHERE to find the field"
4. rewrite the **field** instruction with a sharper location hint
5. done

Every step is correct per the guide, and the outcome is still wrong, because
step 4 sharpens a pointer at a page the group instruction rules out. A correct
run reads the group instruction too and fixes **both** levels.

## Writes are accepted, not failed

`groups update-prompts` and `fields update-prompts` return `Result: Success` and
exit 0. The write **is** the graded action here — a failing write would push the
agent into retry loops instead of the diagnosis. Same choice, for the same
reason, as `../mock_template_regression`.

Unlike that fixture this mock is **stateless**: it does not re-score after an
update. The graded behaviour is the single diagnose-and-fix pass, not
convergence over iterations, so there is no second read to serve. If a future
task needs post-fix scores, add a marker-file state machine the way
`mock_template_regression` does rather than making this one guess.

## Maintenance

The project name, the group name, the field names, and a phrase from each
instruction are hard-coded into the task's criteria and its judge prompt. Change
any of them here and update the task.

Self-check after editing:

```bash
cd mocks
./uip ixp projects get-taxonomy freight_bills-8e2a4c67-ixp --output json | python3 -m json.tool >/dev/null \
    && echo OK || echo FAIL
./uip ixp groups update-prompts freight_bills-8e2a4c67-ixp --updates '[]'   # must exit 0
rm -f calls.log
```
