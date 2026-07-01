# Replace Text Failure - Headers / Footers / Text Boxes Skipped

This scenario reproduces a `Replace Text` silent miss where the
`[CompanyName]` placeholder in the document **header/footer** is left
unchanged while the **body** copy is replaced, because the project pins an
older `UiPath.Word.Activities` (1.6.0) that scans only body text. The job
completes **Successfully**.

## What this scenario uncovers

**Root Cause:** Older `UiPath.Word.Activities` iterates only the primary
body story range; headers, footers, and floating text boxes are skipped. The
body `[CompanyName]` is replaced (log: "Replaced 1 occurrence in the document
body") while the header copy survives. The body match proves the Search
value and template are correct — the gap is the package version.

This maps to:
`references/activity-packages/word-activities/playbooks/replace-text-headers-textboxes-skipped.md`

The correct agent behavior is to recognize a **Successful job with the
header unreplaced** as a silent failure, tie it to the old package version /
non-body story range (via the "in the document body" log + `project.json`
pin), and recommend updating `UiPath.Word.Activities` — not blaming the
template/Search value or dismissing the green job.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project pinning `UiPath.Word.Activities [1.6.0]`; `Replace Text` on `[CompanyName]` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** No faulted job (State=Successful) and no error logs;
> the trace explicitly says the replacement happened "in the document body",
> and `project.json` pins the old `[1.6.0]` package. The agent diagnoses from
> the body-only log + the version pin + the user's header symptom.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `replace-text-headers-textboxes-skipped.md`
- Agent identified the older `UiPath.Word.Activities` scanning only body text
  as the cause and recommended updating the package (or addressing the header
  range explicitly / in code) — without treating the green job as healthy or
  blaming the template/Search value
