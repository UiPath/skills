# classic-runlocaltriggers-generated-missing

Faithful-replay scenario for the `uipath-troubleshoot` skill.

## What this scenario covers

An attended `OrderEntryAssistant` automation (folder `Operations`) faults ~2 seconds after start. The
project uses **Run Local Triggers**, whose read-only trigger workflow Studio auto-generates in the
hidden design-time cache at `.local\generated\Triggers.Generated.xaml`. That generated file was **not
present** when the package the robot ran was built — the `.local` cache is not normally committed, so a
cloned/shared project (or a stale cache / a Studio↔Assistant version mismatch after an upgrade) lacks
it. At run time Run Local Triggers cannot load the generated workflow and the job faults.

The Error log is **deliberately generic** — `System.Exception: The invoked workflow could not be loaded.
A referenced workflow file was not found in the running package.` at `RunLocalTriggers.Execute` →
`GeneratedWorkflowLoader.Load` — it does **not** name the file. So the diagnosis cannot be read straight
off the log: the agent has to combine the faulting activity (`Run Local Triggers`), the project layout
(no `.local` generated workflow), and the knowledge that Run Local Triggers loads an auto-generated
trigger workflow. This mirrors the `classic-openapp` design (misleading surface, cause established by
investigation) so the scenario reliably exercises the skill rather than being one-shot from the error.

This is a **signature** case (Faulted job with an Error log). The agent routes via
`classic-activities/summary.md` to
`classic-activities/playbooks/trigger-scope-and-local-triggers-failed.md`.

The correct diagnosis names the **missing auto-generated Run Local Triggers workflow**
(`.local\generated\Triggers.Generated.xaml`), and the fix **regenerate it by opening/rebuilding the
project in Studio and republishing** (delete the stale `.local` cache first if corrupt; align
Studio/Assistant versions if the fault followed an upgrade) — never hand-create the file. Wrong turns to
avoid: misreading the generic "invoked workflow could not be loaded" as an `Invoke Workflow File`
path/dependency bug (there is no Invoke Workflow File in the source), a workflow-authoring bug in
`Main.xaml`, or fixing it by writing the file by hand.

## Evidence layout

- `data/m/r/10fold.json` — `or folders list` (Operations folder key)
- `data/m/r/20jobs.json` — `or jobs list` (the Faulted job)
- `data/m/r/30jobg.json` — `or jobs get` (State Faulted, Attended, MOCK-HOST, ~2s)
- `data/m/r/40errl.json` — `or jobs logs --level Error` (generic `invoked workflow could not be loaded` at `RunLocalTriggers.Execute` → `GeneratedWorkflowLoader.Load`; the file is **not** named)
- `data/m/r/50infl.json` — `or jobs logs` (Info/Trace: started → Run Local Triggers faulted)
- `process/` — the failing project source: `Main.xaml` has a `ui:RunLocalTriggers` activity, `project.json` depends on `UiPath.Form.Activities`, and there is **no `.local` folder** (the missing artifact is the cause)

Ground truth for the judge: [`RESOLUTION.md`](./RESOLUTION.md).
