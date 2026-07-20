# Final Resolution

## Root Cause
The unattended `NewHireDocs` job faults because the process is bound to a
**OneDrive connection (`b4d6f8a0-c2e4-4671-8390-a1b2c3d4e5f6`) that lives in Priya's personal workspace**
("Personal Workspace - priya.sharma", folder key `9e0f1a2b-3c4d-4e5f-a6b7-c8d9e0f1a2b3`), not in the
`Shared/HR/Onboarding` folder where the job runs. Personal-workspace
connections are only usable by their owner, so Connection Service answers the
robot's resolution attempt with **HTTP 404, error code `CNS1049`**
("connection is on a personal folder"), surfaced as `DAP-GE-3000` at
"Upload Offer Letter". Studio runs work because Priya *is* the owner.

## Evidence the root cause is correct
- Job log error: *"Connection 'b4d6f8a0-c2e4-4671-8390-a1b2c3d4e5f6' is on a personal folder and can only
  be used by its owner"* with `ErrorCode: CNS1049` (TraceId `5d7f9b1c3e0a42c6e8a0b2c4d6e8f0a1`).
- The job's folder (`Shared/HR/Onboarding`) contains **no** connections
  (`is connections list --folder-key 6b8d0f21-3a4c-4e5f-9012-a3b4c5d6e7f8` is empty).
- The connection itself is alive and **Enabled** — but located in
  "Personal Workspace - priya.sharma". It was NOT deleted; the 404 is a
  scoping rejection, not a missing record.
- Owner-vs-robot split: Priya's Studio runs succeed (she owns the
  connection); the unattended robot fails.

## Fix
1. Create the Microsoft OneDrive connection **in the `Shared/HR/Onboarding`
   folder** (or move/re-create the existing one there), authenticated with
   the account the automation should run as.
2. **Rebind** the `NewHireDocs` process ("Upload Offer Letter" activity /
   project connection reference) to the new shared-folder connection and
   republish.
3. Re-run the scheduled job.

**Explicitly wrong fixes:** re-authenticating the personal connection (it is
healthy — ownership, not auth, is the problem), concluding the connection was
deleted, or granting the robot folder permissions (permissions cannot make a
personal-workspace connection resolvable to a robot).

## Verification
With the shared-folder connection bound, the robot resolves it (200 instead
of 404/CNS1049) and the run proceeds past "Upload Offer Letter".

## Prevention
Never publish unattended processes bound to personal-workspace connections —
create connections in the shared folder where the process will run before
publishing. "Works in Studio, fails unattended" plus a 404 with the
personal-folder message is this exact pattern.
