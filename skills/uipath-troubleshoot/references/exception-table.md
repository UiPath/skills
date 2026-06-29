# Exception Table — fast-path signature index

Central, cross-product lookup from an **exact observed signature** to its playbook. Triage greps this table after signal extraction (see `agents/triage.md` § Signature lookup). Two jobs:

1. **Fast-path** — a `fast_path: yes` row whose signature is the clear top match is a cause-naming, single-cause signal. Triage runs the row's `confirm` step inline, writes a confirmed `H1`, and the orchestrator goes straight to depth-check → resolution (no generate/test loop, no dedicated agent).
2. **Routing index** — every row (including `fast_path: no`) gives triage a direct signature→playbook→domain lookup, so it doesn't have to scan every domain summary.

## Eligibility rules (READ FIRST — this is the guardrail)

`fast_path: yes` ONLY when ALL hold:
- The signature is **exact and cause-naming** — an error code, a specific HRESULT, an exception FQN that by itself names the failure mode, or a verbatim message that names the cause. NOT a generic exception class shared by many causes.
- The matched playbook is **single-cause** (its `## Resolution` is not a multi-branch disambiguation the evidence can't settle).
- The signature, when observed, is the **originating fault** — not a wrapper (`AggregateException`) or a downstream/propagation symptom (a parent "job stuck/running", a Maestro incident raised by a child fault).

Everything else is `fast_path: no` → the **full generic loop** runs (GENERATE → TEST → EVALUATE → deepen), including child-job traversal and cross-domain scope expansion. **A `fast_path: no` row never short-circuits the loop.** When in doubt, mark `no` — a false fast-path is worse than a slower correct answer.

Opaque/wrapper/symptom signatures are listed with `fast_path: no` ON PURPOSE (so the table documents why they are NOT fast-pathed), not omitted.

## Match precedence

When multiple rows match: prefer `kind: code` / `hresult` (most specific) > `exception` FQN > `message` regex. A `fast_path: yes` row only fires if it is the unambiguous top match AND no co-equal match from a different domain exists (co-equal cross-domain → generic loop, per `SKILL.md` ROUTING).

## Table

| signature | kind | domain | playbook | fast_path | confirm |
|---|---|---|---|---|---|
| `DAP-GE-3005` | code | integration-service | products/integration-service/playbooks/connector-general-exception.md | yes | `uip is connections ping <id>` shows disabled; cause unambiguous |
| `DAP-GE-3000` | code | integration-service | products/integration-service/playbooks/connector-general-exception.md | no | multi sub-branch (invalid / no-access / Connections.View / Bad Gateway) — disambiguate via connection resource + ping |
| `DAP-RT-1002` | code | integration-service | products/integration-service/playbooks/connector-runtime-exception.md | yes | "Connection ID is empty" — binding gap; cause named by code |
| `DAP-RT-1003` | code | integration-service | products/integration-service/playbooks/connector-runtime-exception.md | yes | "<field> is required" — input gap; cause named by code |
| `DAP-RT-1052` | code | integration-service | products/integration-service/playbooks/connector-runtime-exception.md | yes | "Trigger could not find any matches" |
| `DAP-RT-1101` | code | integration-service | products/integration-service/playbooks/connector-runtime-exception.md | no | "Status code BadRequest/NotFound" — needs the failing request/resource to disambiguate |
| `msg:/connection is invalid or you do not have access/` | message | integration-service | products/integration-service/playbooks/connection-invalid.md | yes | connection missing/disabled/no-permission named by message |
| `UiPath.Ipc.RemoteException` | exception | integration-service | products/integration-service/playbooks/connector-remote-exception.md | no | no code — unwrap innermost message and re-classify |
| `System.AggregateException` | exception | (wrapper) | — | no | never the cause — unwrap `InnerExceptions[0]` and re-match this table |
| `System.NullReferenceException` | exception | (opaque) | — | no | opaque — needs stack frame + source; classify by frame, then full loop |
| `RobotNoMatchingUsernames` | code | orchestrator | products/orchestrator/playbooks/robot-credentials.md | yes | PendingReason names robot/machine credential mismatch |
| `TemplateNoLicense` | code | orchestrator | products/orchestrator/playbooks/robot-credentials.md | yes | template has no license — cause named |
| `msg:/No host is available on the machine template/` | message | orchestrator | products/orchestrator/playbooks/job-pending-no-host.md | yes | confirm template has zero connected runtimes |
| `0x0000052E` | hresult | orchestrator | products/orchestrator/playbooks/job-faulted-logon-failure.md | no | logon-failure family is multi-branch (session/AD/password/MFA/RDP) — full loop |
| `0x40010004` | hresult | orchestrator | products/orchestrator/playbooks/job-stopped-exit-code-0x40010004.md | no | multi-cause (Kill/restart/logoff/OOM/crash/recycle) |
| `msg:/job .*Running/ (parent, no progress)` | message | orchestrator | products/orchestrator/playbooks/job-stuck.md | no | SYMPTOM — a stuck parent is downstream; full loop must traverse to the child job before concluding |
| `UiPath.UIAutomationNext.Exceptions.NodeNotFoundException` | exception | ui-automation | (ui-automation selector playbook) | no | selector mismatch — single-domain cases are tractable, but verify the selector against the live element via the loop; never fast-path when reached as a child of a stuck parent |
| `incident:170002` | code | maestro | products/maestro (bpmn service-task failure) | no | "Failure in the Orchestrator Job" — raised BY a child fault; the child's failure is the real cause. Full loop, traverse to child. |

## Extending

Add a row when a product documents a new exact signature. Default `fast_path: no`; promote to `yes` only after confirming the signature is exact, cause-naming, single-cause, and originating (per Eligibility rules). The table is the single place fast-path coverage grows — no agent edits.
