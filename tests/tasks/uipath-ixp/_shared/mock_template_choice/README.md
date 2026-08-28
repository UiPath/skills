# Choice-data-type mock

Overlay for `../../smoke/choice_value_edit_refusal.yaml`. List it **second** in
`template_sources`, after `../mock_template`, so `mocks/uip` here wins the PATH
shadow while the base template's `mocks/curl` and seeded `calls.log` /
`calls.jsonl` remain.

## Why it exists

`SKILL.md:131` — the CLI can **rename** a data type, **change its
instructions**, or **delete** it, but it cannot add or remove the **values** of
an existing Choice data type. That is a manual edit on the in-product Manage
Taxonomy page.

This is the hardest row in the Unsupported Capabilities table to get right,
because the neighbouring command *is* supported and *is* already tested:

| Ask | Supported? | Covered by |
|---|---|---|
| Create a Choice type **with** its values | yes | `smoke/create_choice_type.yaml` |
| Add a value to an **existing** Choice type | **no** | this task |

So the agent arrives with a tested habit (`data-types add --kind choice
--choices …`) pointing straight at the wrong command.

The base `mock_template` cannot host this. It fails every call, so the taxonomy
is invisible and an agent can "refuse" without ever having seen the type it was
asked to edit — which grades nothing. Here the type, its three current values,
and the field referencing it are all readable, so the refusal is made against a
real, edit-able-looking artifact.

## Fixture

One project, `contract_review-5d8b3e42-ixp` (Title `Contract_Review`):

- `entity_defs` — the six built-in types plus `Clause Presence` (`kind: choice`,
  `input_value: inferred`) whose values are `present`, `absent`,
  `not applicable`, each with `alternates`.
- `label_groups` — one field group `Contract` with three fields, of which
  `Termination Clause` references `Clause Presence` via `field_type_id: e7`.

`projects list`, `projects get` and `projects get-taxonomy` are served.
Everything else falls through to the base mock's offline failure — including
every write the task guards, so a forced attempt is recorded and then fails,
exactly as it would against a real tenant that rejected it.

## The four wrong routes, and why each is guarded

The task asks for a **fourth** value (`disputed`). Every CLI path to it is wrong:

| Route | What actually happens |
|---|---|
| `data-types add` | Clones the type under a new id. Annotations split across two types and the original's pre-trained model is forfeited (Critical Rule 17). |
| `data-types delete` then re-add | **IRREVERSIBLE.** Deleting breaks `Termination Clause`, which references it via `field_type_id` (`cli-reference.md:100`). |
| `data-types update-instructions` | Changes prose only. The value list is untouched — so this is the *subtle* miss: it looks like it worked and returns Success. |
| `projects import-taxonomy` | **Merges, never replaces** (`cli-reference.md:14`). A re-imported value list silently no-ops and returns `{"status":"ok"}`. |

The `update-instructions` and `import-taxonomy` routes are the dangerous ones —
both return success while changing nothing the user asked for, so an agent that
takes either will report the job done.

## Maintenance

The project name, the type name, and the three existing values are hard-coded
into the task's criteria and its judge prompt. Change any of them here and
update the task.

Self-check after editing:

```bash
cd mocks
./uip ixp projects get-taxonomy contract_review-5d8b3e42-ixp --output json | python3 -m json.tool >/dev/null \
    && echo OK || echo FAIL
rm -f calls.log
```
