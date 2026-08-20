# TestManagerSmoke — published test automation fixture

A minimal cross-platform (Portable) UiPath **TestAutomation** project with two test cases, used by the execution / link-automation P&E scenarios so they have a real published automation to discover, link, and run.

| Entry point (`.xaml`) | What it does | Expected result |
|---|---|---|
| `PassCase.xaml` | logs a message | **Passed** |
| `FailCase.xaml` | logs, then throws | **Failed (expected)** |

Built with `uip rpa init --template-id TestAutomationProjectTemplate --target-framework Portable --expression-language VisualBasic`. Only dependency that matters is `UiPath.System.Activities` (+ `UiPath.Testing.Activities` from the template).

## One-time publish (already done on `codereval` / `DefaultTenant`)

```bash
uip rpa pack <this-dir> ./out                      # -> TestManagerSmoke.1.0.0.nupkg
uip or packages upload ./out/TestManagerSmoke.1.0.0.nupkg
uip or processes create --folder-path Shared/uipath-test --package-key TestManagerSmoke --package-version 1.0.0 --name TestManagerSmoke
```

> Test cases must be `editingStatus: "Publishable"` in `project.json` → `designOptions.fileInfoCollection`, or upload fails with *"A testing project should contain at least one entry point."*
> Packing needs `@uipath/rpa-tool` exempted in the cli repo's `bunfig.toml` `minimumReleaseAgeExcludes` while only a <48h alpha is published.

## How the tests use it

- Folder: **Shared/uipath-test** (`--folder-key fcf79fe1-147b-4000-82b3-9eb81b165452`)
- Serverless robot is already assigned to this folder (no setup needed)
- Discover: `uip tm testcases list-automations --project-key HEALTH --folder-key fcf79fe1-147b-4000-82b3-9eb81b165452 --package-name TestManagerSmoke` → `PassCase`, `FailCase`
- Link: `uip tm testcases link-automation --project-key HEALTH --test-case-key HEALTH:11 --folder-key fcf79fe1-147b-4000-82b3-9eb81b165452 --package-name TestManagerSmoke --test-name PassCase` (HEALTH:11 already linked to `PassCase`)
- Run: `uip tm testsets run` targeting this folder; serverless robot is pre-assigned
