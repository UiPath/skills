# classic-browserscope-efail

Faithful-replay scenario for the `uipath-troubleshoot` skill.

## What this scenario covers

A scheduled **unattended** run of `PortalReconciliation` (folder `Finance`) faults ~7 s in at a classic
`Attach Browser` scope (`UiPath.Core.Activities.BrowserScope`) with a
`System.Runtime.InteropServices.COMException` — "Invalid access to memory location."
(HRESULT `0x800703E6`), wrapped as `BrowserOperationException`. The prior run of the same process
succeeded as an **attended** run on a different machine.

The correct diagnosis is an **environmental COM conflict** at the classic BrowserScope (display-scaling
/ privilege-level / non-interactive-session mismatch between the dev machine and the production robot),
**not** a selector, timeout, or extension defect — the source shows valid selectors and a well-formed
scope. Immediate remediation is environment alignment (recommendation only); strategic remediation is
migrating to the modern `Use Application/Browser` container.

Exercises the `activity-packages/classic-activities/playbooks/browser-scope-errors.md` playbook, which
owns the COM/environmental BrowserScope family and its cross-references to the extension/comms
(`browser-open-or-attach-failed.md`) and selector/timeout (`ui-element-not-found.md`,
`ui-activity-timeout.md`) siblings.

## Evidence layout

- `process/` — the failing project source (classic `BrowserScope` + valid child `Get Text`)

Ground truth for the judge: [`RESOLUTION.md`](./RESOLUTION.md).

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
