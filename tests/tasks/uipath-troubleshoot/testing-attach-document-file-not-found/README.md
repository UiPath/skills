# Attach Document Failure - FilePath Points at a Missing File

This scenario replays a **real faulted Orchestrator job** where the
`Attach Document` activity (`UiPath.Testing.Activities.AttachDocument`) threw
`System.IO.FileNotFoundException` because its `FilePath` input pointed at a
file that does not exist at runtime. The exception **message is the bare file
path** (`C:\TestData\evidence\run-report.pdf`), and the fault is raised by the
activity's own `File.Exists` check **before** any Orchestrator / test-case
call — so the stack shows `AttachDocumentService.AttachDocument` with no
test-case frames.

- Real job key: `e192429e-1248-4872-863a-24ad8f6e88fe`
- Process / ReleaseName: `EvidenceArchival`
- Folder: `Shared` (key `defb8e05-e36b-4c36-bf11-0b4d08ce6cd1`)

## What this scenario uncovers

**Root Cause:** The `Attach Document` activity in `Main.xaml` has
`FilePath="C:\TestData\evidence\run-report.pdf"`. That file does not exist at
runtime, so the activity's pre-attach `File.Exists` check faults synchronously
with `System.IO.FileNotFoundException` whose message is the path. The job
faults the moment the activity runs (~3.5s after start), before any
Orchestrator / test-case interaction.

This maps to:
`references/activity-packages/testing-activities/playbooks/attach-document-file-not-found.md`

The correct agent behavior is to read the `FilePath` from `Main.xaml`, match
the playbook, and recommend correcting / validating the path (ensure the file
exists at that path, fix the path, or guard with a `File.Exists` check before
`Attach Document`).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | snapshot of the failing UiPath project: a single `Attach Document` activity with `FilePath="C:\TestData\evidence\run-report.pdf"` (`x:Class` retargeted to `Main`) |
| `fixtures/mocks/responses/*.json` | **real captured** `uip` responses (scrubbed) for `or folders list`, `or jobs list`, `or jobs get`, `or jobs history`, `or jobs logs` |
| `fixtures/mocks/responses/manifest.json` | dispatch table (quoted + unquoted variants, first-match) |

> **Provenance / scrub note.** Fixtures were captured from a real failing job
> via the `uip` CLI, then scrubbed: host `UIP-PW06WJSK` -> `MOCK-HOST`;
> `LocalSystemAccount UIPATH\DAN.MOROSANU` -> `UIPATH\REPLACEMENT_USER`; the
> personal-workspace folder email -> `original_email@test.com`. Kept verbatim:
> the job key, folder key, the error text + .NET stack, the path
> `C:\TestData\evidence\run-report.pdf`, `Shared`,
> `OrchestratorUserIdentity: newrobot`, timestamps, and numeric ids. The
> `jobs list` fixture contains only the single target job so the agent
> investigates it unambiguously.

## Success criteria

This scenario **scores the conclusion, not the trajectory**. The only graded
outcomes are:

- Agent invoked the `uipath-troubleshoot` skill (`skill_triggered`).
- Agent matched `attach-document-file-not-found.md` and reached the same
  conclusion as `RESOLUTION.md`: the `Attach Document` `FilePath` points at a
  non-existent file (`C:\TestData\evidence\run-report.pdf`), the
  `FileNotFoundException` is raised before any Orchestrator/test-case call, and
  the fix is to correct / validate the path (or guard with `File.Exists`). The
  judge applies an anti-fabrication hard gate (cap 0.2) for blaming
  Orchestrator connectivity, permissions, a missing test-job context, or a
  different activity (`llm_judge`).
