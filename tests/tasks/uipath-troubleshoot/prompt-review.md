# `tests/tasks/uipath-troubleshoot/` — prompt review

Existing test prompts vs. natural-user rewrites. Methodology in [hitl-prompts-review.html](../../hitl-prompts-review.html) and [CLAUDE.md](../../CLAUDE.md).

## Scope of this folder

`uipath-troubleshoot` is the hypothesis-driven root-cause skill: a user reports a failing/stuck/faulted job (or pastes an error), and the agent walks logs/traces/incidents to identify the originating fault. Each test replays a real investigation against a mocked `uip` CLI. The 19 scenarios here cover a wide error-class spread — argument-null and null-reference exceptions, Excel/O365 faulted jobs, ten Get Asset failure modes, RPA foreground/preflight/selector-healing failures, a stuck Maestro RPA job, a healing-agent recommendation case, and one CI smoke test that verifies every mocked `uip` subcommand still exists.

## Insider markers seen in this folder

This folder is overwhelmingly natural in voice — the prompts read like real desperate customer one-liners ("something is broken", "why did my job <UUID> fail"). The only systematic insider marker is **process-name fixture leakage**: the failing UiPath process is named after its own diagnosis.

- **Telegraphic test-fixture process names**: `AssetSilentFailure`, `AssetVaultFailure`, `AssetFolderMismatch`, `AssetNetworkConnectivity`, `AssetPerRobotNoValue`, `AssetPermissionDenied`, `AssetRobotUnlicensed`, `AssetWrongActivityType`, `GetAssetFailure`, `MisconfiguredForeground`, `ForegroundHolder`. A real customer's process is called `InvoiceProcessor` or `OnboardingFlow`, not `AssetPermissionDenied`. The name gives the answer away — an agent that pattern-matches on the process name alone (without reading any logs) could pass.
- **One legitimate eval-harness smoke prompt**: `smoke-manifest-commands` is a no-op task whose real gate is a `pre_run` script (`fail_on_error: true`). The prompt "Pre-run verification passed. Print 'OK' and stop." is correctly insider — it must short-circuit the agent because the agent shouldn't actually do anything.

Notably **absent** from this folder (good signs):
- No raw `state.json` / `hypotheses.json` / `depth-check.json` schema references.
- No "load the uipath-troubleshoot skill first" / "follow the Critical Rules" callbacks.
- No mention of sub-agents (`triage`, `presenter`, `depth-verifier`, `hypothesis-tester`).
- No numbered diagnostic step lists in the user voice.
- No CLI-flag literacy demands (`--output json`, `jobs get <id>`, etc. all stay inside the skill).
- No `.local/investigations/` paths leaking into the user prompt.

Pasting a raw job UUID is **not** insider here — real Orchestrator users routinely copy-paste job keys when filing a support request.

## Verdict summary

| Verdict | Count |
|---|---|
| Insider — fixable | 11 |
| Insider — legitimate (CLI/refusal/antipattern/smoke coverage) | 1 |
| Mixed | 0 |
| Natural | 7 |

## Per-test review

### All tests

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `argument-null-exception` | Natural | "Why did my job 0686cab1-…-c91d9c275524 from Shared folder has failed?" | _Keep as-is — already natural (typical customer one-liner with a job key)._ |
| `faulted_excel_o365` | Natural | "This process is failing to run from Orchestrator, the last failing job is in my personal folder. Pinned job key: 3033bce6-…. The project source for the failing process is at ./RPA Workflow/ in the current working directory." | _Keep as-is — already natural. The `./RPA Workflow/` path is something a customer would say when pointing the agent at their local checkout._ |
| `getasset-activity-silent-failure` | Insider — fixable | "My AssetSilentFailure process is faulting in Orchestrator on every run. Can you investigate? The project source for the failing process is in the current working directory." | "My asset-lookup process is faulting in Orchestrator on every run, but the logs aren't showing a clear error — it just keeps going and ends up with the wrong data downstream. Can you take a look? Project source is in the current working directory." |
| `getasset-external-vault-failure` | Insider — fixable | "My AssetVaultFailure process is faulting in Orchestrator on every run. Can you investigate? …" | "My InvoiceLookup process is faulting in Orchestrator on every run when it tries to pull a credential. Can you investigate? Project source is in the current working directory." |
| `getasset-folder-scope-mismatch` | Insider — fixable | "My AssetFolderMismatch process is faulting in Orchestrator on every run. …" | "My ClaimsProcessor process is faulting in Orchestrator on every run — it worked in dev but fails as soon as we publish. Can you investigate? Project source is in the current working directory." |
| `getasset-name-mismatch` | Insider — fixable | "My GetAssetFailure process is faulting in Orchestrator on every run. The folder is 'Remote Debugging'. Can you investigate? …" | "My OrderSync process is faulting in Orchestrator on every run. The folder is 'Remote Debugging'. Can you investigate? Project source is in the current working directory." |
| `getasset-network-connectivity` | Insider — fixable | "My AssetNetworkConnectivity process is faulting in Orchestrator on every run. …" | "My DailyReports process is faulting in Orchestrator on every run. Can you investigate? Project source is in the current working directory." |
| `getasset-per-robot-no-value` | Insider — fixable | "My AssetPerRobotNoValue process is faulting in Orchestrator on every run. …" | "My PayrollExport process is faulting in Orchestrator on every run — works fine on my dev robot but fails when scheduled. Can you investigate? Project source is in the current working directory." |
| `getasset-permission-denied` | Insider — fixable | "My AssetPermissionDenied process is faulting in Orchestrator on every run. …" | "My FinanceReconciliation process is faulting in Orchestrator on every run. Can you investigate? Project source is in the current working directory." |
| `getasset-robot-not-authenticated` | Insider — fixable | "My AssetRobotUnlicensed process is faulting in Orchestrator on every run. …" | "My VendorOnboarding process is faulting in Orchestrator on every run since we rotated robot credentials yesterday. Can you investigate? Project source is in the current working directory." |
| `getasset-wrong-activity-type` | Insider — fixable | "My AssetWrongActivityType process is faulting in Orchestrator on every run. …" | "My ContractRenewal process is faulting in Orchestrator on every run. Can you investigate? Project source is in the current working directory." |
| `healing-agent-recommendation-only` | Natural | "why did my last job from folder Shared from orch has failed?" | _Keep as-is — already natural (sloppy lowercase real-user voice with the typical Orchestrator/folder reference)._ |
| `maestro-stuck-rpa-job` | Natural | "This job 0fbda085-…-012c1914845a from my personal workspace is stuck running. why?" | _Keep as-is — already natural._ |
| `null-reference-exception` | Natural | "why did my job 77dc53dd-…-a52e9e7ef163 from Shared folder has failed?" | _Keep as-is — already natural._ |
| `rpa-foreground-already-running` | Insider — fixable | "My ForegroundHolder process just faulted in Orchestrator a few seconds after it started — can you investigate? The project source is in the current working directory." | "My InvoiceScraper process just faulted in Orchestrator a few seconds after it started — can you investigate? Project source is in the current working directory." |
| `rpa-foreground-misconfigured` | Insider — fixable | "My MisconfiguredForeground process just faulted in Orchestrator a few seconds after it started — can you investigate? …" | "My CRMUpdater process just faulted in Orchestrator a few seconds after it started — can you investigate? Project source is in the current working directory." |
| `rpa-preflight-failure` | Natural | "can you investigate my last failed job?" | _Keep as-is — already natural. Minimal, vague, exactly what a frustrated user types._ |
| `rpa-selector-healing-disabled` | Natural | "troubleshoot 777d35d4-…-5243ba2947fc. something is broken" | _Keep as-is — already natural (terse, real-user voice with just a job key)._ |
| `smoke-manifest-commands` | Insider — legitimate | "Pre-run verification passed. Print 'OK' and stop." | _Keep as-is — this is a CI fixture-validation smoke test whose real gate is the `pre_run` script (`fail_on_error: true`). The agent prompt has to be a no-op stub. Legitimate harness use._ |

## Notes for the PR description

- **One systematic finding worth surfacing**: 11 of 19 scenarios name the failing UiPath process after its own diagnosis — `AssetPermissionDenied`, `AssetRobotUnlicensed`, `MisconfiguredForeground`, etc. This is fixture leakage: a sufficiently lazy agent could guess the root cause from the project name before reading a single log line. Rename the snapshotted `process/` folders to neutral business-flavored names (`InvoiceProcessor`, `ClaimsLookup`, `PayrollExport`) — the scrub-pass tooling already supports renaming, this is the same class of substitution as personal Windows paths or `<name>@uipath.com`.
- **Voice is otherwise excellent.** The non-Asset prompts read like genuine support tickets: lowercase, terse, sometimes ungrammatical ("why did my job … has failed?"), often nothing but a UUID and "something is broken". This is exactly right — the troubleshoot skill should handle that, and the tests don't over-explain on the user's behalf.
- **The folder cleanly avoids harness leakage at the schema layer** — no `.local/investigations/` paths, no `state.json` references, no playbook machine names, no sub-agent names (`triage`, `depth-verifier`, `presenter`) in the user prompts. The CLAUDE.md in this folder already enforces "the judge grades on presentation, not internal state", and the prompt corpus reflects that discipline.
- **The one smoke prompt** (`smoke-manifest-commands`) is correctly insider — it's CI hygiene for mock-dispatcher coverage. Flagging it as legitimate, not fixable.
