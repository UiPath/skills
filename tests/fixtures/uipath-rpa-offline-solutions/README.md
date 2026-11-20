# Solutions to the offline XAML tasks

One solution per task in `tests/tasks/uipath-rpa/offline/`, each scoring 1.0 with that folder's grader; that folder's README says how to grade one.
They live here, outside the task and reference folders coder-eval copies into the sandbox, so that no agent under test can reach them.
They were written with the RPA builder SDK (`UiPath/builder-sdk`, `typescript/rpa-sdk`), which keeps their `.rpa.ts` sources.
