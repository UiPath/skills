# Project-state read mock

Overlay for `../../smoke/report_model_config.yaml` and
`../../smoke/describe_project.yaml`. List it **second** in `template_sources`,
after `../mock_template`, so `mocks/uip` here wins the PATH shadow while the base
template's `mocks/curl` and seeded `calls.log` / `calls.jsonl` remain.

## Why it exists

The base `mock_template` fails every call, so a task on it can grade only that
the agent typed the right command. For a **write** that is the whole deliverable
— `configure-model --model gemini_2_5_pro` either has the right flag or it does
not. For a **read whose answer is derived**, it grades nothing that matters.

Two such reads exist; `query_model_and_preprocessing.yaml` grades only the command shape:

| Question | Skill | What the agent must derive |
|---|---|---|
| "which model / pre-processing?" | `SKILL.md:88`, `cli-reference.md:36-47` | invert `_model_config.input_config` through a 4-row table |
| "describe this project" | `SKILL.md:103` | three calls, fixed report order, and **don't** page `documents list` |

Neither has a command that returns the answer. `configure-model` only writes
(and is a read-modify-write, so probing with it rewrites the project), and there
is no `get-model-config` at all. This fixture serves the raw artifacts so the
derivation itself can be graded.

## Fixture

Four projects, one per documented `input_config` state — the four rows invert
differently, and one of them is a trap:

| Project | `_model_config.input_config` | Correct pre-processing answer | `model_version` |
|---|---|---|---|
| `ap_invoices-3c1d9b70-ixp` | `null` | **"not configured"** — *not* `none` | `gemini_2_5_flash` |
| `id_scans-6b4e2f18-ixp` | `{"mode":"image_only"}` | `none` | `gemini_2_5_flash` |
| `vendor_bills-9a7c5d24-ixp` | `text_plus_image` + `uipath_cv_table_only` | `table_mini` | `gemini_2_5_flash` |
| `settlement_notes-2e8f6a91-ixp` | `text_plus_image` + `gemini_table_only` | `table` | `gemini_2_5_pro` |

`projects get`, `projects get-taxonomy`, `projects list-models` and
`documents list` are served for all four; `projects list` returns all four.
Everything else falls through to the base mock's offline failure.

`vendor_bills` additionally carries the full describe-a-project shape: 2 field
groups (`Invoice Header`, `Line Items`), 7 fields, `Total: 128` documents, and a
published version 12 tagged `live` alongside an older version 9.

## Three deliberate traps

**`null` is not `none`.** `cli-reference.md:40` is explicit: a `null`
`input_config` means never configured, and must be reported as such rather than
as the `none` token. They are different states — `none` is a choice someone made,
`null` is the absence of one — and collapsing them is the most likely wrong
answer, so `ap_invoices` exists to catch it.

**`ModelName` disagrees with `model_version`.** `list-models` reports the trained
labeller *family* (`gemini_ixp`, `gemini_pro_ixp`), which is never a `--model`
value and carries no pre-processing information (`cli-reference.md:34`). The two
fields are worded so they cannot be confused for each other: an answer sourced
from `ModelName` says `gemini_ixp`, which is visibly not one of the three
selectable models. Without that mismatch an agent reading the wrong field could
be accidentally right.

**`documents list` looks truncated.** `Total: 128` against the default
`Limit: 50` makes the first page look partial, which invites `--offset` paging.
`SKILL.md:103` says to read `Total` for a count and not to page — so the task
guards `--offset` negatively. A fixture with `Total` under 50 would remove the
temptation and the assertion would pass vacuously.

## Maintenance

Fixture values are hard-coded into both tasks' criteria and judge prompts.
Change a project name, an `input_config`, the group/field names, or the
document `Total` here and update both tasks.

Self-check after editing (every response must be valid JSON and the four states
must still invert distinctly):

```bash
cd mocks
for p in ap_invoices id_scans vendor_bills settlement_notes; do
    ./uip ixp projects get-taxonomy "$p-x-ixp" --output json | python3 -m json.tool >/dev/null \
        && echo "OK $p" || echo "FAIL $p"
done
rm -f calls.log
```
