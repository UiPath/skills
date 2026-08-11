# Final Resolution

---

**Root Cause:** `Download File from URL` cannot resolve the URL's host from the
robot machine — `System.Net.Sockets.SocketException: Don't know about such a host`
for `feeds.partner-portal.example`. Either DNS does not resolve the host from the
robot, or an enterprise firewall / SSL-inspection proxy blocks the automated
outbound connection. The URL opens from the user's own laptop browser because that
network path / DNS differs from the unattended robot's.

**What went wrong:** The `FeedDownloader` job (started 2026-06-16T14:26:51Z)
faulted ~2 seconds in at `Download File from URL` while resolving
`https://feeds.partner-portal.example/data/export.csv`, with `Don't know about
such a host. (feeds.partner-portal.example:443)`. The request never reached the
server — this is name resolution / network reachability, not an HTTP status.

**Why:** The activity issues the request from the **robot host's** network
context. If that host can't resolve the name (no/different DNS) or an outbound
firewall / SSL-inspection proxy filters automated, non-interactive traffic, the
connection fails before any HTTP exchange. "Works from my laptop" doesn't mean the
robot can reach it. This is distinct from a `401`/`403` (where the request reaches
the server and is refused).

---

**Evidence:**

### Orchestrator (Propagation)
- Job: FeedDownloader -- Faulted at 2026-06-16T14:26:53.300Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: External Feeds (key `fa040004-d4e5-4f60-8a04-000000000004`)
- Final error: `Download File from URL: Don't know about such a host. (feeds.partner-portal.example:443)` (`HttpRequestException` -> `SocketException`) -> `Main.xaml` -> `DownloadFileFromUrl "Download File from URL"`

### File Operations (Root Cause)
- Activity surface: `UiPath.Activities.System.FileOperations.DownloadFileFromUrl`, `Url=https://feeds.partner-portal.example/data/export.csv`.
- The error is a host/name-resolution `SocketException` ("Don't know about such a host") — the request never reached the server (not a 401/403, not an HttpClient loop error, not a file-finalize error). It fails from the robot but the URL works from the user's laptop.

---

**Immediate fix:**

This is an environment/network fix, not a workflow change.

### Fix path A -- whitelist / enable the endpoint for the robot (preferred)
Have the network team **whitelist the target host/URL** for the robot's outbound
traffic (and its automated user-agent), and allow the robot host through the
firewall / SSL-inspection proxy so the name resolves and the connection is
permitted.

### Fix path B -- verify reachability from the robot host
Confirm the host resolves and the file fetches **from MOCK-ROBOT specifically**
(not just a developer laptop) — e.g. `nslookup feeds.partner-portal.example` and a
test download from the robot host — then re-run (e.g. via an unattended job) after
the network change.

### Optional
If only automated traffic is filtered by user-agent, set `UserAgentHeader` to a
recognized browser user-agent — but the primary fix is the network whitelist.

### Verification (hand to the user - off-host)
From MOCK-ROBOT: `nslookup feeds.partner-portal.example` (does it resolve?) and a
test fetch of the URL. If it fails there but works on your laptop, it confirms the
DNS/firewall cause; after the network whitelist, the download succeeds.

- **Source:** `file-operations/playbooks/download-file-host-not-found.md`

---

**Preventive fix:**

1. **Provisioning** -- ensure robot hosts can resolve and reach the external
   endpoints their automations call (DNS + firewall/proxy allowlist), and validate
   from the robot, not just dev machines.
   - **Why:** "Works on my laptop, host-not-found on the robot" is a recurring
     environment gap for outbound downloads.
   - **Who:** Network / platform team.

2. **Pre-flight** -- for critical external feeds, verify connectivity from the
   robot host before relying on the download in production.
   - **Who:** RPA developer / platform team.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | DNS can't resolve the host from the robot, or a firewall/SSL-inspection proxy blocks the automated outbound connection | High | Confirmed | Yes | `Don't know about such a host. (feeds.partner-portal.example:443)` SocketException at Download File from URL; works from the user's laptop, fails from the robot | Network fix: whitelist the endpoint for the robot and verify the host resolves/reaches from the robot machine |

---

Would you like the exact host commands to check DNS / connectivity on MOCK-ROBOT,
or help cleaning up the `.local/investigations/` folder?
