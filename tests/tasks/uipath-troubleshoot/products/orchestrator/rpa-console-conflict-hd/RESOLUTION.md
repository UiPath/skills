# Resolution — ClaimsIntake "another interactive job is using the machine's console"

## Root Cause

Job `b2820001-2222-4222-8222-222222222222` (process `ClaimsIntake`, folder HD
Automations) faulted at executor start, near-zero runtime, with:

```
Another interactive job is using the machine's console. Only one interactive job can use the console at a time.
```

`HD-BOT-POOL` is a **high-density (HD)** host — `machines list --all-fields`
shows 5 unattended slots and 4 robot users, and `jobs list` shows a second
`ClaimsIntake` job **Running** on the same host when this one was dispatched.
The robots are configured with **"Login to Console = True"**, so every job
attaches to the machine's **single physical console session** instead of
creating its own session. A host has exactly one console, so only one
console-attached interactive job can run at a time; the second concurrent job
is refused. This is the documented anti-pattern — Login to Console is **not
recommended for HD robots** precisely because there is only one console
session.

Matches `products/orchestrator/playbooks/console-conflict-login-to-console.md`.

## Fix

**Disable "Login to Console"** for the HD robot users on HD-BOT-POOL (Tenant →
Users → user → Access Rules → Advanced Robot Options). With it off, each job
gets its own RDP/virtual session instead of competing for the single console,
so the parallel ClaimsIntake jobs seat in separate sessions up to the licensed
slot count. Re-run after disabling.

## Must NOT attribute

Do not attribute this to: a credential/logon failure (no `Logon failed` /
`0x000005..` code; sequential jobs on the same users succeed); the "workstation
is in use by another user" slot-capacity case (the message names the
**console** specifically, and this host is HD with ample slots); a foreground
process conflict (that is an Assistant-started single-user case); a transient
blip (a rerun with Login to Console still True re-hits the single-console limit
whenever two jobs overlap); or licensing. The fix is disabling Login to Console
for the HD robots, not credentials, slots, or a rerun.
