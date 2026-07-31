# RPA-review eval suite (`uipath-review`)

Twelve read-only-review evals covering the highest-value RPA (`.xaml` / `.cs`)
review scenarios. The ten single-defect evals each plant one primary,
best-practice-grounded defect and check the reviewer catches it; the two e2e
evals are comprehensive multi-workflow / multi-project reviews graded on
breadth + severity discipline. None edit the artifact.

Scenario ranking is grounded in the UiPath Workflow Analyzer rule taxonomy
(`ST-*`, `UI-*`) plus community/Academy signal (selectors, exception
mis-classification, environment-coupling, and credential exposure dominate real
production incidents).

## The 12 evals

### Single-defect (10)

| Dir | task_id | Artifact | Primary defect | Grades on | Tier |
|---|---|---|---|---|---|
| `selector-brittle/` | `skill-review-rpa-selector-brittle` | XAML | Full-path / `idx` selector + hardcoded env URL; no Object Repository | `UI-REL-001`/`UI-DBP-030`/`UI-ANA-016` or prose | smoke |
| `exception-classification/` | `skill-review-rpa-exception-classification` | XAML | `throw new Exception(ex.Message)` (stack loss) + `ContinueOnError=True` + no Business/System split | `ST-DBP-003`/`UI-ANA-017` or prose | smoke |
| `hardcoded-config/` | `skill-review-rpa-hardcoded-config` | XAML | URL/path/timeout/threshold hardcoded, not in Config/Assets | `ST-USG-005`/`ST-DBP-021` or prose | smoke |
| `credential-security/` | `skill-review-rpa-credential-security` | XAML | Plaintext password as `String` (logged) + `Get Asset` for a credential asset | `ST-SEC-007/008/009` or prose | smoke |
| `logging-pii/` | `skill-review-rpa-logging-pii` | XAML | `Write Line` + PII (email/SSN) in Log Message + Verbose in prod | `ST-MRD-011`/`ST-USG-020` or prose | smoke |
| `reframework-integrity/` | `skill-review-rpa-reframework-integrity` | XAML | System exception swallowed in Process.xaml (marked success) + double-retry + no circuit breaker | prose | integration |
| `transaction-shape/` | `skill-review-rpa-transaction-shape` | XAML | One-to-many bulk-in-transaction, no idempotency guard | prose (shape **and** idempotency) | integration |
| `coded-structural/` | `skill-review-rpa-coded-structural` | `.cs` | No `CodedWorkflow` base, no `[Workflow]`, `out` param (CS1620), hardcoded path | prose (≥2 defects) | smoke |
| `performance-datatable/` | `skill-review-rpa-performance-datatable` | XAML | Nested For Each over DataTables (O(n·m)) + logging in loop + hardcoded `Delay` | `ST-DBP-026`/`ST-PRR-004`/`UI-DBP-013` or prose | smoke |
| `legacy-precision/` | `skill-review-rpa-legacy-precision` | XAML (Legacy) | **NEGATIVE** — no framework defect; reviewer must NOT flag Legacy as Critical, must give tailored migration advice, must not fabricate rule IDs | inverse grader | smoke |

### End-to-end (2)

Comprehensive reviews graded on breadth + severity discipline (not one defect): the grader requires the report to use both severity bands and catch defects across more than one workflow / project.

| Dir | task_id | Artifact | Scope | Grades on | Tier |
|---|---|---|---|---|---|
| `e2e-reframework-process/` | `skill-review-rpa-e2e-reframework-process` | XAML (3 workflows) | REFramework performer (Main → System1_Login → Process): hardcoded credential (Critical) + brittle selector (Warning) + swallowed exception (Critical) + Write Line (Info) + double-retry | ≥800 B, Critical **and** Warning bands, credential + swallowed-exception + ≥3 categories | e2e |
| `e2e-multi-project-solution/` | `skill-review-rpa-e2e-multi-project-solution` | XAML (2 projects) | Dispatcher + Performer under `RetailSolution/`: brittle selector + hardcoded URL/queue (Dispatcher), hardcoded credential + swallowed exception (Performer), shared queue-name config drift | ≥800 B, both projects named, Critical **and** Warning bands, a Performer Critical + a Dispatcher issue | e2e |

## Real-project bases (5 of 12)

Five fixtures are built on **real UiPath projects** (copied from real Studio output, stripped of `.local`/`.settings`/`.project` caches and any secrets, then the specific defect injected) rather than hand-authored skeletons:

- `reframework-integrity`, `transaction-shape`, `e2e-reframework-process` — the real **Robotic Enterprise Framework** template (full `Framework/` workflow set, the `Main.xaml` state machine, `Config.xlsx`, `Tests/`). The defect is injected into the real `Framework/Process.xaml` (in VisualBasic, matching the project); the e2e adds an invoked `System1_Login.xaml` with a hardcoded credential + brittle selector.
- `coded-structural` — a real coded invoice process. The correct helper workflows (`ReadExcelData.cs`, `AddToQueue.cs`) stay as authentic context; the defect is injected into the entry `Main.cs`.
- `selector-brittle` — a real desktop UI automation (drives Studio via Use Application + Type Into). The stable `automationid` selector is replaced with a positional `idx`-only chain.

The other 7 are hand-authored but structurally realistic (real Studio `project.json`/XAML shape). Every fixture was validated by a blind Haiku review + the real grader (12/12).

## Layout per task

```
<scenario>/
├── <scenario>.yaml          # coder-eval task (Pattern B)
├── check_<scenario>.py       # grader: reads ./_review_report.md, asserts the defect
└── fixture/<ProjectDir>/     # deliberately-flawed UiPath project (project.json + .xaml/.cs)
```

## Shared conventions

- **Fixture delivery** — static `sandbox.template_sources: [{type: template_dir, path: fixture}]`
  overlays `fixture/<ProjectDir>/` into the sandbox cwd (same mechanism as
  `uipath-troubleshoot`). No `pre_run` inject script; the `.xaml`/`.cs` are
  hand-authored for realism.
- **Read-only enforcement** — two `command_not_executed` guards (Write + Edit)
  whose `command_pattern` matches the project dir, weight 3.0 each. The report
  is written to `./_review_report.md` at the sandbox root (outside the project
  dir) so writing it never trips the guard.
- **Grading** — `skill_triggered` (w3.0) proves invocation; a `run_command`
  sidecar `check_*.py` (w5.0) reads `_review_report.md`, requires ≥500 bytes,
  and PASSES on the expected Workflow Analyzer rule code **or** defect-specific
  prose (RPA has no `rule_id`-emitting judgment catalog — phase 2 — so prose is
  accepted). Each grader warns (not fails) on cited rule codes absent from the
  skill's RPA checklists.
- **CLI checks are advisory** — `uip rpa validate/build/analyze` need Windows
  Studio Helm and won't run on Linux CI, so the `command_executed` check is
  `pass_threshold: 0` (recorded, never gating). The review, report, and grader
  are platform-independent — the skill's checklists teach manual detection — so
  9/10 run in the Linux smoke gate.
- **Tags** — `[uipath-review, <tier>, mode:diagnose, lifecycle:discover]` where
  tier is `smoke` (8), `integration` (2 single-defect REFramework-family), or
  `e2e` (2 comprehensive). `integration`/`e2e` keep the longest agent runs out
  of the PR smoke gate; the e2e graders carry weight 6.0.

## Local verification

```bash
# Structural: YAML/JSON/XAML/py all parse
# (repo has a python with PyYAML at /usr/local/bin/python3)

# Grader discrimination self-test (good report → exit 0, bad report → exit != 0):
#   for each check_*.py, stage a crafted ./_review_report.md and run it.

# CLI-verb reachability:
python3 scripts/check-cli-verbs.py tests/tasks/uipath-review/rpa/*/*.yaml

# Run a task (Linux docker smoke):
cd tests && .venv/bin/coder-eval run \
  tasks/uipath-review/rpa/selector-brittle/selector-brittle.yaml \
  -e experiments/smoke.yaml -v
```
