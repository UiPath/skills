# UiPath Assistant Playbooks

**Overview:** [overview.md](./overview.md) — the two-log architecture (`combined.log` / `Robot.log`) and evidence model (on-disk logs, no `uip` CLI surface)
**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — anchor-on-symptom rules, high-value artifacts to request, combined.log-first scan, Robot.log timezone correlation, flow attribution and escalation

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Sign-in fails | Medium | Signed-out stays signed-out. `combined.log` `/robot/interactiveConnectSignIn` `result: false`; `Robot.log` `InteractiveConnectFlow.SignIn` — transport error (`TaskCanceledException`/`HttpRequestException`) on `/identity_`/`/discovery_`, or HTTP `401`/`403`, wrong environment, or lost browser callback | [sign-in-failure.md](./playbooks/sign-in-failure.md) |
| Cannot connect to Orchestrator | Medium | Signed in but stays Offline. `combined.log` `/robot/connectToServer` `result: false`; `Robot.log` `CloudConnectFlow` — Orchestrator unreachable (`HttpClient.Timeout`/`TaskCanceledException`), `401`/`403` (machine/robot not authorized), wrong URL, or TLS/cert | [orchestrator-connection-failure.md](./playbooks/orchestrator-connection-failure.md) |
| Process missing or won't start | Medium | Process not listed, or `/process/start` fails. `Robot.log` package errors (`NU1101`, feed timeout), not-assigned/wrong-folder scope, license/robot-type mismatch, or a package/dependency launch error | [process-missing-or-unstartable.md](./playbooks/process-missing-or-unstartable.md) |
| Crashes or closes unexpectedly | Low | Window closes/blanks/freezes. Renderer exception (DevTools console, not `combined.log`), main-process exception (`combined.log` tail), Robot-service crash (`Robot.log`), or environment (GPU/OOM/AV) | [assistant-crash.md](./playbooks/assistant-crash.md) |

## No-signature routing

| Symptom | Entry |
|---|---|
| Assistant hangs on an action with no error toast and no clear log trace | Anchor on the action (sign-in / connect / start), run that playbook, and treat the silent hang as a UX bug to file (investigation guide § Presenting, item 4) |
| Archive has an expected trace missing | The user likely pasted a truncated file — ask for the full `combined.log` / `Robot.log` (investigation guide Rule 6) |
