# Uia Silent Noop Verify Missing — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session.

## What the original session uncovered

**Root Cause:** The "Click 'I'm Feeling Lucky'" activity in Main.xaml was authored with `InteractionMode=Simulate` and a target-less (inert) Verify Execution. Under Simulate, the click reports Successful as soon as the element is found and the event is posted — it never validates that the click had any effect — and the inert Verify (`Mode=Appears` with no verification target and empty Retry/Timeout) had nothing to check. So when the click did not take effect, no fault surfaced: the job ended Successful, and Healing Agent — which only engages on a faulting/timing-out modern UI activity — had nothing to recover.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | frozen snapshot of the failing UiPath project |
| `fixtures/mocks/responses/*.json` | real stdout extracted verbatim from the session transcript |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`

## Validation

Passing run: `experiments/default.yaml`, model `claude-sonnet-4-6`, `--repeats 3 --max-parallel 3`. All 3 reps SUCCESS — `skill_triggered` 1.0, `file_exists` 1.0, `llm_judge` 1.0 / 0.9 / 0.8 (gate respected; no `Main.xaml` edit). Requires `SKILLS_REPO_PATH` and a tilde-free `TMPDIR/TEMP/TMP` (e.g. `C:/cetmp`) on Windows.

## Re-running the extraction

If the source transcript or project changes, regenerate the scenario:

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path> --project <path> --transcript <path> \
    --scenario-name uia-silent-noop-verify-missing --apply
```
