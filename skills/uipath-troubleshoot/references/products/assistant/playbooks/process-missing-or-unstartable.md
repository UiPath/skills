---
confidence: medium
---

# Process Missing or Won't Start in the Assistant

## Context

The Assistant is signed in and connected, but a process the user expects is not listed, or clicking it fails to start.

What this looks like:
- **Missing:** the process list is empty or short; `combined.log` shows the list fetched with few/zero entries; `robotStatus` is Connected.
- **Won't start:** `combined.log` shows `/process/start` invoked with `result: false`/`null`, often repeated.
- `Robot.log` on a start attempt: package restore/download errors — `NU1101` ("Unable to find package"), NuGet feed URLs, or a download `TaskCanceledException`/`HttpRequestException`; or a launch error before the workflow runs.

What can cause it:
1. **Package feed unreachable** — `NU1101` / feed timeout: the process package cannot be downloaded from Orchestrator/the NuGet feed (network, or feed misconfigured).
2. **Not assigned / wrong folder scope** — the process is not assigned to this user's robot, or lives in a folder the user's robot isn't in → it never appears (missing case).
3. **License / robot type mismatch** — no attended license, or the robot type can't run this process.
4. **Package/dependency error at launch** — the package downloads but a missing dependency or corrupt package fails the launch (error in `Robot.log` before first activity).

What to look for:
- Missing vs won't-start — the two split cause 2/3 (missing) from cause 1/4 (start fails).
- On a start failure, whether `Robot.log` shows a **download** error (`NU1101`, feed URL) vs a **launch** error after download.

## Investigation

1. Anchor: missing from the list, or listed-but-won't-start? Note the exact process name.
2. **Missing:** in `combined.log` confirm the process-list fetch returned few/zero entries while Connected → the list is authoritative, so the process isn't assigned/in scope for this robot → cross-reference the `orchestrator` domain (process assignment, folder, license).
3. **Won't start:** find `/process/start` in `combined.log`, note the timestamp, then read `Robot.log` (timezone-convert) at that point:
   - `NU1101` / feed URL / download timeout → cause 1.
   - Download succeeded, then a dependency/corrupt-package error → cause 4.
   - License/robot-type error → cause 3.
4. For cause 1, capture the feed host and ask the user to `curl -v <feed-url>` from the machine to separate network from feed config.

## Resolution

- **Cause 1 (feed unreachable):** restore access to the package feed (network/proxy/firewall), or fix the feed URL/credentials in Orchestrator; retry start.
- **Cause 2 (assignment/scope):** assign the process to the user's robot and confirm the robot is in the process's folder — resolve via the `orchestrator` domain; the process then appears.
- **Cause 3 (license/type):** allocate an attended license / correct the robot type for the user; reconnect and retry.
- **Cause 4 (package/dependency):** republish the package with its dependencies resolved (or fix the corrupt version); clear the local package cache and retry.
