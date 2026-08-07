# GSuite Drive Multiple-Items Name-Conflict Troubleshooting — Faithful Replay

This scenario replays a real `uipath-troubleshoot` investigation of a Faulted
Orchestrator job whose UiPath.GSuite **Create Folder** activity hit a Google
Drive **duplicate-name ambiguity**.

## What the original session uncovered

The user asked only *"why did my last job from folder Shared fail?"*. The agent:

1. Listed folders → resolved **Shared** to key `1965a46b-db4e-469e-aaaa-7e0b379cb34d`.
2. Listed Faulted jobs in Shared → newest is **DriveFileCreator**,
   job `6c8b1949-2603-437d-86a6-6b82b989fd6a`.
3. Read the job's `Info` → a `UiPath.GSuite.Exceptions.GSuiteException`:
   `Multiple items with the name dupe-folder found in the specified folder.`
   thrown from `CreateFolderConnections`.

Conclusion: the destination already held **more than one item named
`dupe-folder`**, so the activity's `ConflictResolution` (UseExisting) could not
resolve the name to a single item — a **name-ambiguity** conflict, *not* a
404/resource-not-found, connection/auth, invalid-range, or transient fault.
(Listing connections confirms both GSuite connections serving Shared are
Enabled and valid — a defensive fixture reinforces that the connection is fine.)

## Name-conflict signature

```
UiPath.GSuite.Exceptions.GSuiteException: Multiple items with the name dupe-folder found in the specified folder.
   at UiPath.GSuite.Drive.Services.DriveServiceProxy.CreateFolderAsync(...)
   at UiPath.GSuite.Activities.CreateFolderConnections.SafeExecuteAsync(...)
```

## How this test reproduces it

| Layer | Source |
|---|---|

CLI-driven — no `process/` snapshot; the root cause is fully contained in the
`or jobs get` `Info` field.

## Playbook validated

`skills/uipath-troubleshoot/references/activity-packages/gsuite-activities/playbooks/drive-multiple-items-name-conflict.md`

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's host-side protected mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
