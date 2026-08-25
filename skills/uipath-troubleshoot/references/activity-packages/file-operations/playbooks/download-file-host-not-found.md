---
confidence: medium
---

# Download File from URL — "Don't know about such a host" (DNS / Firewall)

## Context

What this looks like:
- `Download File from URL` faults with `Don't know about such a host` / `The remote name could not be resolved` / a name-resolution (`System.Net` / socket) error naming the URL's host.

What can cause it:
- **DNS cannot resolve the host** from the robot machine.
- **An enterprise firewall / SSL-inspection proxy blocks the automated outbound connection** — the background, non-interactive request (often with no browser user-agent) is filtered even though the host resolves for interactive users.

What to look for:
- Whether the host resolves / is reachable **from the robot host** specifically (it may work from a developer machine but not the unattended robot).
- Whether the environment uses an outbound proxy / SSL inspection that gates automated traffic.
- Whether the failure is consistent (every run) — pointing at network reachability rather than a transient blip.

## Investigation

1. Read the error from job evidence; confirm it is a host/name-resolution failure (`Don't know about such a host` / `remote name could not be resolved`) at `Download File from URL`, not an HTTP 401/403, an `HttpClient` loop error, or a file-finalize error.
2. Read the `Url` from the `.xaml` and confirm the host name.
3. Establish (hand the user a host check if off-host) whether the host resolves and is reachable **from the robot machine** — e.g. `nslookup <host>` and a test request from the robot host — and whether an outbound proxy / SSL inspection is in play.

## Resolution

- **If DNS / firewall blocks the host:** have the network team **whitelist the target URL endpoint** for the robot's outbound traffic (and automated user-agent), and allow the robot host through the proxy / SSL-inspection policy. This is an environment/network fix, not a workflow change.
- **Verify reachability from the robot host:** confirm the host resolves and the file fetches from the **robot machine** (not just a dev machine) before re-running — e.g. test via an unattended job after the network change.
- **If only automated traffic is blocked:** set `UserAgentHeader` to a recognized browser user-agent if the proxy filters by user-agent (but the primary fix is the network whitelist).

> If the request reaches the server but is rejected with `401`/`403` rather than failing to resolve the host, that is an authentication problem — see [download-file-403-401-auth.md](./download-file-403-401-auth.md).
