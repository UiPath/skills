# Resolution — InvoiceParse serverless "Robot Units exceeded"

## Root Cause

Job `c3930001-3333-4333-8333-333333333333` (process `InvoiceParse`, folder
Cloud Robots) went straight to Faulted without running, history Pending →
Faulted (never Running), with:

```
Automation cannot be started. Your tenant's assigned Robot Units have been exceeded. Allocate more Robot Units to your tenant to continue.
```

The job is **`RuntimeType` Serverless** (cloud robot). This is a **tenant-level
licensing/allocation limit** — the tenant's Robot Unit pool for serverless
runs is exhausted, so Orchestrator refuses to start any further serverless
automation until more units are available. It is **not** a code, workflow,
credential, session, or robot-version fault: nothing executed, there is no
Windows session or executor involved, and the message is explicit about the
Robot Units limit at **tenant** scope.

Matches `products/orchestrator/playbooks/serverless-license-quota.md`.

## Fix

- **Allocate more Robot Units to the tenant** (Automation Cloud → Admin →
  tenant → Licenses), which restores serverless capacity for every user in the
  tenant.
- **Or** reduce concurrent/accumulated serverless usage until the pool frees
  up, so scheduled runs fit within the current allocation.
- The scope is **tenant**, not the individual user — raising one user's
  allocation will not help while the tenant pool itself is exhausted.

## Must NOT attribute

Do not attribute this to: an unattended executor/session failure (there is no
`Could not start executor`, no Windows logon code, no session — it is
serverless); a machine/host problem (serverless jobs bind no listed machine
template; the empty `machines list` is expected, not a "no host" fault); a
credential/password issue; a robot-version defect; or a transient blip fixed by
rerunning (a rerun before units free up just re-hits the quota). It is a
tenant-scope Robot Units / licensing limit, fixed by allocating units.
