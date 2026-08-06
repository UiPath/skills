# Download File from URL Failure - "Don't know about such a host" (DNS / Firewall)

This scenario reproduces a `Download File from URL` name-resolution failure. The
activity faults with `Don't know about such a host` because DNS cannot resolve the
URL's host from the robot, or an enterprise firewall / SSL-inspection proxy blocks
the automated outbound connection — even though the URL opens from a user's own
laptop browser.

## What this scenario uncovers

**Root Cause:** The host doesn't resolve / isn't reachable from the **robot
machine** (DNS or firewall/proxy), not a workflow defect.

This maps to:
`references/activity-packages/file-operations/playbooks/download-file-host-not-found.md`

The discriminator vs a 401/403: this is a **host-resolution** failure (the request
never reaches the server), not an auth rejection. The fix is an environment/network
change (whitelist / verify reachability from the robot) — not a workflow or host
command run by the agent.

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | hand-authored UiPath project with a single `Download File from URL` to an external partner host |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent's diagnosis matches `RESOLUTION.md`: identifies a DNS / firewall /
  SSL-inspection host-resolution failure from the robot (not an auth/401-403
  issue) and recommends the network fix — whitelist the endpoint for the robot and
  verify the host resolves/reaches from the robot machine — without fabricating
  host actions

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's host-side protected mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
