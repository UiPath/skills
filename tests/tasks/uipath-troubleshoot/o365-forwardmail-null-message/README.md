# O365 Forward Mail Null Message — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session (scrubbed).

## What the original session uncovered

The user asked why their last job in folder `Shared` failed. The most recent
job, `ERN_O365_LegacyMailNRE` (key `50bcdb33-f7a8-42d4-a52d-ebbeeb135e99`),
faulted with a raw `System.NullReferenceException: Object reference not set
to an instance of an object.` thrown by the legacy O365 `ForwardMail`
activity (`ForwardMail.ExecuteAsync` top frame). Job trace spans proved the
cause: the activity's `Message` input is bound to variable `originalEmail`,
but only 3 spans exist (job root → Microsoft 365 Scope → Forward Mail) — no
upstream mail-fetch/producer activity ever ran, so `originalEmail` stayed
null. The `To` attribute is a non-null literal, ruling out the
null-recipient-element cause; the fault landed ~1.3 ms into the activity,
before any Microsoft Graph call. Fix: assign/produce the message before
forwarding and/or add a null guard on `originalEmail`; migrating to the
Connections Forward Email is a complementary preventive fix.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `fixtures/mocks/responses/*.json` | real stdout extracted verbatim from the session's investigation `raw/` outputs |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

No `process/` snapshot — the original investigation determined the root cause
from platform evidence alone (job traces carried the binding + missing-producer
evidence).

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent's final response reaches the same root cause and fix as `RESOLUTION.md`

## Re-running the extraction

If the source investigation changes, regenerate the scenario:

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path> --transcript <path> --resolution <path> \
    --scenario-name o365-forwardmail-null-message --apply
```
