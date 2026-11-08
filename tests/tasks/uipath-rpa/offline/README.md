# ACME work-item reconciliation

A real-world XAML process, rather than one capability: the ACME work-item reconciliation robot on REFramework, with its two systems turned into file exports so the task runs offline.
The agent builds a multi-workflow project from a blank one (`_project`, a Portable VB project with only `UiPath.System.Activities` 26.8.2), and the grader runs it.

| Folder | What it is |
| --- | --- |
| `_project`, `_notes` | What the agent starts with: the blank project and `UIPATH_XAML.md`, notes on this setup |
| `specs/` | The six graded scenarios; `acme_reconciliation.py` writes `acme_reconciliation.json` and computes each scenario's answers from the prompt's rules |
| `grade.sh` | The grader: builds the XAML runner once, then runs `_verifier` against the spec |
| `_uip` | The Studio Web `uip` stand-in |
| `_verifier`, `_runner` | The verifier and the CoreWF runner from `UiPath/coder_eval_uipath`'s offline XAML suite (`tasks/offline_authoring/xaml`) |
| `reference/` | A solution that scores 1.0, kept to prove the task can be passed and to check the grader after a change |

The agent works under Studio Web Autopilot's constraints: Studio Web's host serves only `uip rpa init` and `uip rpa run`, so `pre_run` installs `_uip/uip`, a stand-in with just those two verbs (`run` on the same CoreWF runner the grader uses), ahead of `skills-image`'s full `uip`, and builds the runner into `/opt/xaml-runner`.
It does that only inside the docker sandbox, so run the task with `experiments/nightly.yaml`.
With the full `uip`, the skill's validate-and-build loop against a cold Studio Helm took every trial past a 30-minute turn.

`grade.sh static` loads and compiles every workflow and checks `Main.xaml`'s argument contract; `grade.sh runtime` runs `Main.xaml` headlessly in each scenario and checks its outputs, `Updates.csv`, its logs and, in one scenario, the fault.
Both use the runner `pre_run` built (and build it themselves if it is missing), which needs the .NET 10 SDK (`skills-image` has it) and the public NuGet feeds in `_runner/nuget.config`.

To grade the reference by hand:

```bash
cd tests/tasks/uipath-rpa/acme_reconciliation/reference && bash ../grade.sh static && bash ../grade.sh runtime
```

The task comes from `UiPath/builder-sdk` (`typescript/tasks/rpa`), where it runs in two arms, hand-written XAML with this repo's `uipath-rpa` skill and the RPA builder SDK with its preview skill; that suite's README has the results.
