# Uia Ambiguous Node Test — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent diagnosed a `NodeAmbiguousException` against a DataTables grid and
matched the `ambiguous-selector.md` playbook at high confidence.

## What this scenario reproduces

- Process: `ERN` (entry point `Amb.xaml`)
- Failing activity: `NClick "Click 'Airi Satou'"` inside `NApplicationCard "Edge DataTables  Javascript table library"`
- Selector authored too generically (`SearchSteps='FuzzySelector'`, no `FullSelectorArgument` set):

  ```
  <webctrl id='example' matching:id='fuzzy' fuzzylevel:id='0.0' tag='TABLE' />
  <webctrl tag='TD' />
  ```

  The outer segment uniquely identifies the DataTables demo grid (`id='example'`). The inner `<webctrl tag='TD' />` matches EVERY `<td>` cell rendered in that table — the row value `Airi Satou` appears nowhere in the selector.

- Exception: `UiPath.UIAutomationNext.Exceptions.NodeAmbiguousException`
- Friendly message (`Strings.NodeNotFoundMultipleMatches`): "Multiple similar matches found. Could not uniquely identify the user-interface element for this action. Edit the element, run Validation, and add anchors in order to ensure the element is uniquely identified."
- Stack origin: `TargetCommonLogic.GetSearchResultAsync` → `NClick.SearchAndSetTargetAsync` → `NClick.ExecuteAsync` (no `VerifyExecutionService` frames, no Healing Agent recovery frames — the find phase short-circuits before either runs)
- Branch (B) of `ambiguous-selector.md` — repeated UI pattern without a row anchor or idx qualifier.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | minimal UiPath project where `Amb.xaml` encodes the ambiguous-selector failure (only the failing entry point is shipped; the original project's other entry-point XAMLs and binary `.screenshots/`/`.storage/`/`.uia/` directories are stripped) |
| `fixtures/mocks/responses/*.json` | verbatim `uip` CLI responses captured from the original session (`or folders list`, `or jobs list --state Faulted`, `or jobs get`, `or jobs logs --level Error`, `or jobs history`) |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `ambiguous-selector.md` AND reached the same root cause as `RESOLUTION.md` (branch (B), row-anchor / `aaname` fix)
- Agent did NOT recommend any of the anti-patterns listed in the playbook's "Anti-patterns" section (increase Timeout, switch InteractionMode, enable Healing Agent, wrap in Retry Scope or try/catch, blind `idx='1'`)

## Re-running the extraction

If the source transcript or project changes, regenerate the scenario:

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path>/.local/investigations \
    --project C:/Users/dan.morosanu/Documents/UiPath/ERN \
    --transcript <path>/C--work-DA-runs-uia-amb2/<sessionId> \
    --scenario-name uia-ambiguous-node-test --apply
```

Note: re-running the generator restores the full `process/` snapshot (including the other entry-point XAMLs and binary subdirs). Strip those again after regeneration — only `Amb.xaml`, `project.json`, and `project.uiproj` are needed for the test.
