# Get Asset Failure — Network / Connectivity Issue

This scenario reproduces a runtime `Get Credential` failure caused by
the **robot host being unable to reach the Orchestrator URL** —
network, firewall, DNS, proxy, SSL/TLS, or session-expiry. The asset,
folder, robot license, and robot roles are all correctly configured;
the failing layer is below all of them, in the robot-to-Orchestrator
connectivity path.

Orchestrator's response surfaces in the job logs as:

```
[Get Credential] Orchestrator information is not available.
Connection timed out connecting to https://cloud.uipath.com.
```

## What this scenario uncovers

**Root Cause:** The robot host running this job (`RobotUser1` on
`MOCK-HOST`) cannot reach the Orchestrator URL. The CLI commands that
query Orchestrator from the developer's session (folders, jobs,
assets, users) all succeed because they run from a different network
context. Only the in-job HTTP call from the robot to Orchestrator
times out, surfacing as "Orchestrator information is not available."

This maps to:
`references/activity-packages/system-activities/playbooks/get-asset-network-connectivity.md`
(**low-confidence** playbook).

> **Why "low-confidence":** the playbook's symptom — "Orchestrator
> information is not available" — covers many distinct sub-causes
> (Robot service not running, firewall, DNS, proxy, SSL cert, TLS
> EMS, session expiry). The agent's job here is to recognize the
> **connectivity layer** as the failing layer, not to pinpoint the
> exact sub-cause. The LLM judge is correspondingly flexible: any
> connectivity-family conclusion + connectivity-family fix scores
> high.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project, correctly configured at every workflow layer |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence:

1. **Job logs** contain "Orchestrator information is not available" along with connection timeout / TCP failure language.
2. **Asset list** shows `myHiddenAsset` present and correctly typed — rules out asset-side issues.
3. **`users list`** shows `RobotUser1` is licensed with the right roles — rules out license/permission issues.
4. **Folders list** returns `Remote Debugging` — rules out folder-scope issues.

The CLI-query-success / robot-call-failure asymmetry is the signal: the developer's session can reach Orchestrator; the robot host cannot.

## How this differs from sibling scenarios

| Dimension | Other 8 GetAsset scenarios | `network-connectivity` (this) |
|---|---|---|
| Failing layer | Asset, folder, permission, type, per-robot value, license, vault, package | **Robot-to-Orchestrator connectivity** |
| Error signature | Codes 1002 / 1100 / 0 / 400 / 2304 / "Invalid asset type" / NRE | **"Orchestrator information is not available" + timeout/SSL** |
| Playbook confidence | high (5 scenarios) / medium (3) | **low** |
| Sub-cause variants in playbook | 1–3 per playbook | **6+** (Robot service, firewall, DNS, proxy, SSL, TLS EMS, session expiry) |
| Judge tolerance for sub-cause | strict (must name) | **flexible (family recognition is enough)** |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-diagnostics` skill
- Agent matched the correct playbook AND reached a connectivity-family conclusion
- Conclusion must (a) name "Orchestrator information is not available" as the defining symptom and (b) recommend at least one connectivity-family fix (Robot service, network/firewall, proxy, SSL/TLS)

The judge is permissive about which sub-cause the agent picks, since the playbook itself enumerates many.

## Regenerating from a real session

```bash
python tests/tasks/uipath-diagnostics/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name getasset-network-connectivity --apply
```
