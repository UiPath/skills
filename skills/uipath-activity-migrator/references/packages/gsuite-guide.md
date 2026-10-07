# GSuite Package Guide — classic to modern GSuite

> **Owner review pending.** Pre-filled from the migrator source (`UiPath.Upgrade.GSuiteActivities`). Lines marked `VERIFY` need confirmation by the GSuite package owners. Extend the three hooks; keep their headings.

Extension `GSuiteActivities`. **Preview-gated:** in the public build its flags may be absent and its migrators inactive. Confirm with `"<MIGRATOR_EXE>" analyze --help`: when no `--gsuite-*` flag is listed, this extension does nothing in this build; report classic GSuite activities as not migrated and skip the rest of this guide.

Applies when `project.json` lists the classic GSuite package `VERIFY` (`UiPath.GSuite.Activities` below the modern `3.x` line). Do not pre-scan the XAML: the `analyze` run reports every affected activity per file.

## Hook 1 — Before analyze

### What the extension does

- Upgrades the GSuite dependency to at least `3.8.10` `VERIFY`.
- Migrates Gmail, Calendar, Apps Script, Docs, Sheets, and Drive activities to their connector-based modern activities; scopes become `GSuiteApplicationScope` or a plain `Sequence` when the classic scope used custom OAuth credentials.
- Where the modern output type differs, generates an HTTP request plus `Assign` bridge, or reports action required.

### Flags

Availability and defaults come from `"<MIGRATOR_EXE>" analyze --help` on the installed build (Step 0); this extension's flags appear only in preview builds.

| Flag | Use |
|---|---|
| `--gsuite-package-version=<VER>` | Latest stable: `node "<SKILL_DIR>/scripts/resolve-package-lines.mjs" --package UiPath.GSuite.Activities --all-lines --lines 1`. The tool raises values below its built-in minimum |
| `--gsuite-config=<FILE>` | Same JSON grammar as the Mail guide; connector types `uipath-google-gmail`, `uipath-google-drive`, `uipath-google-sheets`, `uipath-google-calendar` `VERIFY`, `uipath-google-docs` `VERIFY` |
| `--gsuite-migrate-only=<svc,...>` | Restrict to services: `gmail`, `calendar`, `appsscript`, `docs`, `sheets`, `drive` (case sensitive); default is all |

Extension options bind only in the `--name=value` form; the space-separated form is silently ignored.

Connection configuration follows [mail-guide.md § Connection configuration file](mail-guide.md#connection-configuration-file) with the GSuite connector types:

```json
{
  "* > *": { "ConnectionId": "<CONNECTION_ID_FALLBACK>" },
  "* > [uipath-google-gmail] *": { "ConnectionId": "<CONNECTION_ID_GMAIL>" },
  "* > [uipath-google-drive] *": { "ConnectionId": "<CONNECTION_ID_DRIVE>" },
  "* > [uipath-google-sheets] *": { "ConnectionId": "<CONNECTION_ID_SHEETS>" }
}
```

Write it to `<PROJECT_DIR>/.upgrade/gsuite-config.json` and pass `--gsuite-config="<PROJECT_DIR>/.upgrade/gsuite-config.json"`.

### Stop conditions specific to this package

None. Missing connections degrade to action-required results.

## Hook 2 — Triage

Rule IDs follow `<CLASSIC-ACTIVITY-NAME>-ACTIVITY-MIGRATION`, for example `SEND-EMAIL-ACTIVITY-MIGRATION`, `DOWNLOAD-FILE-ACTIVITY-MIGRATION`. Levels as in the Mail guide: `error` = left classic, `warning` with `[PostMigration Action Required]:` = manual work, `note` = migrated.

Unsupported classic activities are reported at `error` and left in place; the analyze results are the only authoritative list for a given package version.

Known caveats: Send Email loses the classic attachment-existence check and de-duplication; outputs typed as raw Google API objects are rebuilt through an HTTP bridge or reported when the file or document ID is not a literal.

## Hook 3 — After upgrade

1. Empty connections:

   ```bash
   grep -rnE 'ConnectionId="(|00000000-0000-0000-0000-00000000000[0-9])"' --include=*.xaml "<OUTPUT_DIR>"
   ```

   List hits under manual work as **Critical**.
2. Scopes migrated to a plain `Sequence` (custom OAuth) need a connection-based scope or per-activity connections; list them.
3. Runtime prerequisites for the report: Google connections in Integration Service per service used, shared with the robot account.
