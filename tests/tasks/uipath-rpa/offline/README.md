# Real-world XAML processes, graded by running them

Each task here builds a whole process rather than exercising one capability, with its systems turned into file exports so it runs offline, and the grader runs the result.

| Task | The process |
| --- | --- |
| `acme_reconciliation` | The ACME work-item reconciliation on REFramework: System 1's paged work-item list, detail pages and System 3 statements, a config file, business and system exceptions, retries and a stop rule |
| `invoice_intake` | Accounts-payable invoice intake from an exported mailbox: unread mail, OCR'd PDF invoices, field extraction, a vendor and credit check, an ERP posting queue, a failed folder and notifications; shaped after the InvoiceIntake fixture in `tests/tasks/uipath-genome` |

The agent starts from a blank Portable project with only `UiPath.System.Activities` 26.8.2 (`_offline_xaml/_project`) and `UIPATH_XAML.md`, notes on this setup (`_offline_xaml/_notes`).

## Studio Web Autopilot's constraints

Studio Web's host serves only `uip rpa init` and `uip rpa run`.
Each task's `pre_run` installs `_offline_xaml/_uip/uip`, a stand-in with just those verbs (`run` on the same CoreWF runner the grader uses), ahead of `skills-image`'s full `uip`, and builds the runner into `/opt/xaml-runner`.
It does that only inside the docker sandbox, so run these tasks with `experiments/nightly.yaml`.
With the full `uip`, the skill's validate-and-build loop against a cold Studio Helm took every trial of `acme_reconciliation` past a 30-minute turn.

## Grading

`_offline_xaml/grade.sh <task> static` loads and compiles every workflow and checks `Main.xaml`'s argument contract; `grade.sh <task> runtime` runs `Main.xaml` headlessly in each scenario of `<task>/specs/<task>.json` and checks its outputs, the files it writes, its logs and, where a scenario expects one, the fault.
Each task's `specs/<task>.py` builds its scenarios and computes their answers from the prompt's rules; edit it and run it to rewrite the JSON.
A spec grades only the logging its prompt asks for.
Each task's solution, which scores 1.0, is in `tests/fixtures/uipath-rpa-offline-solutions/<task>/`, kept to prove the task can be passed and to check the grader after a change:

```bash
cd tests/fixtures/uipath-rpa-offline-solutions/invoice_intake && bash ../../../tasks/uipath-rpa/offline/_offline_xaml/grade.sh invoice_intake static && bash ../../../tasks/uipath-rpa/offline/_offline_xaml/grade.sh invoice_intake runtime
```

The solutions are kept out of `offline/` on purpose.
coder-eval copies the reference directory (`offline/`) and the task's folder into the sandbox and locks them for the agent's turn, but the agent runs as root there, and root keeps the capability to unlock them (`chmod`), so a solution inside either folder could be read by an agent that set out to.
`tests/fixtures/` is in neither, and is masked when the repo is loaded as the skills plugin.

The verifier and runner (`_offline_xaml/_verifier`, `_offline_xaml/_runner`) are `UiPath/coder_eval_uipath`'s offline XAML suite (`tasks/offline_authoring/xaml`), vendored unchanged but for the verifier's own tests.
The tasks come from `UiPath/builder-sdk` (`typescript/tasks/rpa`), where they run in two arms, hand-written XAML with this repo's `uipath-rpa` skill and the RPA builder SDK with its preview skill; that suite's README has the results.
