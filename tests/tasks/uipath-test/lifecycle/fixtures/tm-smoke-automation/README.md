# TestManagerSmoke — minimal test automation fixture

A tiny UiPath **test automation** for the full-lifecycle e2e, with **two very
simple test cases** so the lifecycle test can link different automation entry
points to different Test Manager test cases:

| Entry point (`.xaml`) | What it does | Expected result |
|---|---|---|
| `PassCase.xaml` | log → take screenshot → log | **Passed** |
| `FailCase.xaml` | log → take screenshot → log → throw | **Failed (expected)** |

Each case is intentionally trivial. `PassCase` just logs and screenshots and
passes. `FailCase` is a **deliberate expected failure**: it models a login-gated
step the robot can't complete, so after logging + screenshotting it `Throw`s a
"login required" exception. This gives the automated run a realistic
**1 passed / 1 failed** breakdown that the lifecycle test's collect-results and
report legs can show — the failure is expected, not a problem with the test. The
only dependencies are `UiPath.System.Activities` and
`UiPath.UIAutomation.Activities` (for the screenshot).

> **Deployed fixture:** this package is published on `codereval / DefaultTenant`
> as process **`TestManagerSmoke`** v1.0 in the **`Shared`** folder, exposing
> entry points `PassCase` and `FailCase`. Discover with
> `uip tm testcases list-automations --project-key <…> --folder-key <Shared> --package-name TestManagerSmoke`.

## Why it exists

The lifecycle test (`../full_lifecycle_e2e.yaml`) does **not** build a `.xaml`
per run. It links an already-published automation and runs it. This is that
automation — created once, outside the test, exactly like the serverless robot.

## One-time setup (outside the test)

Build + publish it once to the Orchestrator folder the test targets
(`$E2E_TM_FOLDER`), then the test discovers its entry point via
`uip tm testcases list-automations` and links it:

```bash
# from this directory, after opening the project in Studio (or via CLI pack):
uip solution pack . --output ./out                 # or build in Studio
uip or packages upload ./out/TestManagerSmoke.*.nupkg
uip or processes create --folder-path "$E2E_TM_FOLDER" \
  --name TestManagerSmoke \
  --package-key TestManagerSmoke --package-version 1.0.0
```

The published test entry point ("OpenTestManager") is what the lifecycle test
binds to with `uip tm testcases link-automation` and then runs automated.

> The `.xaml` here is a hand-authored minimal starter. Open it once in Studio
> to validate/build before publishing; Studio may normalize the file on save.
