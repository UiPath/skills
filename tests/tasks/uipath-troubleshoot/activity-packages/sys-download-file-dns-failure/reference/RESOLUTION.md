# Final Resolution

---

**Root Cause:** The `Download File from URL` activity in `Main.xaml`
failed at the transport layer. The
`System.Net.Http.HttpRequestException` wraps a
`System.Net.Sockets.SocketException` ("The requested name is valid, but
no data of the requested type was found") for host
`files.acme-vendorportal.example.com:443` — a DNS / name-resolution
failure. The host does not resolve from the robot machine, so no HTTP
request was ever sent.

**What went wrong:** The `VendorPortalSync` job (started
2026-06-24T10:02:31.400Z) faulted ~1.6 seconds after launch when the
`Download File from URL` activity tried to fetch
`https://files.acme-vendorportal.example.com/reports/monthly.xlsx`.

**Why:** The exception never reached HTTP status handling — it failed
during connection setup. The inner `SocketException` is a name-resolution
error: the OS could not resolve `files.acme-vendorportal.example.com` to
an address (or resolved it to no usable record) from the robot host. This
is a wrong/expired hostname or a DNS/network/proxy/firewall problem on the
robot, NOT a 404, a missing file, or an authentication failure — those
would produce a response with a status code.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: VendorPortalSync — Faulted at 2026-06-24T10:02:33.010Z (ran ~1.6 seconds)
- Folder: Finance (key `4b1c7e90-2a3d-4f5e-9c8b-1a2b3c4d5e6f`)
- Machine: MOCK-HOST
- ErrorCode: `Robot`
- Final error: `The requested name is valid, but no data of the requested type was found. (files.acme-vendorportal.example.com:443)` → `Main.xaml` → `DownloadFileFromUrl "Download File from URL"` → `Sequence "Main Sequence"` → `VendorPortalSync "VendorPortalSync"`

### System Activities (Root Cause)
- Activity: `DownloadFileFromUrl` (DisplayName: "Download File from URL")
- Url: `https://files.acme-vendorportal.example.com/reports/monthly.xlsx`
- Outer exception: `System.Net.Http.HttpRequestException: The requested name is valid, but no data of the requested type was found. (files.acme-vendorportal.example.com:443)`
- Inner exception: `System.Net.Sockets.SocketException` at `HttpConnectionPool.ConnectToTcpHostAsync` — connection/DNS resolution failed before any HTTP exchange.

---

**Immediate fix:**

### System Activities (Root Cause)
1. Verify the URL host is correct and resolves + is reachable FROM THE ROBOT host.
   - **Why:** The `SocketException` fired during connect, so the failure is DNS/network — the request never went out. Fixing the activity's other properties will not help.
   - **Where:** On the robot machine (MOCK-HOST), confirm `files.acme-vendorportal.example.com` resolves (e.g. `nslookup`/`Resolve-DnsName`) and that port 443 is reachable. Check the hostname is current (not a decommissioned/renamed endpoint), and review DNS, proxy, firewall, and TLS/egress configuration on the robot — the dev machine resolving it is not sufficient.
   - **Who:** RPA developer + infra/network owner for the robot host
   - **Source:** `system-activities/playbooks/download-file-failed.md` ("Transport failure — HttpRequestException" branch)

---

**Preventive fix:**

1. **Studio** — Wrap `Download File from URL` in a Try/Catch that catches transport failures and retries with backoff, and emit a clear "host unreachable / DNS failure" message including the host.
   - **Why:** Transient DNS/network blips otherwise surface as a raw socket error deep in the stack.
   - **Who:** RPA developer

2. **Infra** — Ensure the vendor host is on the robot's DNS/proxy allowlist and monitored, so a hostname change or DNS outage is caught before a scheduled run fails.
   - **Why:** A robot commonly resolves differently from a developer workstation.
   - **Who:** Infra / network team

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | DNS/name-resolution (transport) failure for the download host | High | Confirmed | Yes | `HttpRequestException` wrapping `SocketException` at connect; no HTTP status | Verify host resolves/reachable from robot; fix DNS/proxy/hostname |
| H2 | HTTP 404 / file removed at source | Low | Rejected | No | No response/status code — failure was pre-request at the socket layer | — |

---

Would you like help adding a retry/Try-Catch around the download, or
confirming the host resolves from the robot? I can also clean up the
`.local/investigations/` folder if you no longer need it.
