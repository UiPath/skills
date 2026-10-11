# Case round-trip probe (MST-15831)

Does a case plan built outside Studio Web survive the Case Designer? The method is
publish one golden to alpha, open it in the Case Designer, save without editing, pull it
back, validate `--strict --sdd`, and diff against the pre-open plan. Then the same with
one small canvas edit.

## Committed before the first publish

| File | What it fixes in advance |
|---|---|
| `PREDICTION.json` | which divergences are expected (`change`), forbidden (`survive`) or not predicted either way (`uncertain`), with the reason for each. Scored both ways: an expected change that does not happen is a MISS, a forbidden one that does is a violation, and anything no rule names is a SURPRISE |
| `consistency.py` | what "consistent" means for `entry-points.json` and a layout side-car, and the CLI-editable check |
| `roundtrip_diff.py` | the leaf-level diff and the scorer |
| `simulate.cjs` | the designer's own converter (`@uipath/case-schema`, vendored in the CLI) run disk → memory → disk |
| `test_roundtrip_probe.py` | planted breaks the harness must catch: a rewritten `uniqueId`, a dropped connector field, a dropped plan file, an inconsistent side-car |

## The golden

`cm_golden_expense`, the plan claude-opus-5-5 built in nightly `2026-10-05_04-24-14`
(a fresh run that passed every criterion, `case debug` included). 15 tasks of every
type, including both connector task types. Strict `--sdd` Valid on cli 59cceb569, with 3
warnings.

- Its ids are the agent's, not `sdd convert`'s. A pre-open versus post-open diff of the
  same artifact does not need deterministic ids: they matter when two independent
  builds are compared. Raw `sdd convert` output was not used because it leaves 9 items
  unresolved, three of them `connector-context`, the exact configuration this probe
  must test.
- The designer's converter round-trips this plan with **zero** divergences. Every
  predicted change is therefore the front end's, not the converter's.
- **Limit:** every task output has `id == var`, so a companion collapse cannot show here.

The project files are not committed (the repo is public and they name tenant
connections). Pre-open SHA-256, first 16 hex: caseplan.json b95c83117d3f692b,
entry-points.json 2dde6a112f2749a3, bindings_v2.json 7334aeacc6d104c4, project.uiproj
a1f7a13f7cb33514, package-descriptor.json fd11f30889b56b58, operate.json f0a0877eb6885d3b.
The staged copy has a fresh `SolutionId`, so the upload imports a new solution and
cannot overwrite the nightly's.

## Protocol per round trip

1. `uip solution upload <stage> --output json`; require `Data.Action == "Imported"` on round 1.
2. A person opens `DesignerUrl` in the Case Designer, waits for the canvas to load, and
   records what the canvas shows, connector tasks especially (a re-configure prompt is
   UI state, not a file diff). Round 1: Save without editing. Round 2: rename one
   wait-for-timer task, then Save.
3. `uip solution download <SolutionId> --extract --destination <post>`.
4. `python3 roundtrip_diff.py <pre>/CMGoldenExpense <post>/CMGoldenExpense --prediction PREDICTION.json`,
   then `consistency.py`, then `uip maestro case validate <post>/…/caseplan.json --strict --sdd sdd.md`.
5. Each divergence is explained as deliberate or filed.
