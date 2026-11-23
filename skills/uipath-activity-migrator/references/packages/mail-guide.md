# Mail Package Guide — classic Outlook to Microsoft Office 365

> **Owner review pending.** Pre-filled from the migrator source (`UiPath.Upgrade.MailActivities`). Lines marked `VERIFY` need confirmation by the Mail and Microsoft 365 package owners. Extend the three hooks; keep their headings.

Extension `MailActivities`. Applies when `project.json` lists `UiPath.Mail.Activities`. It migrates the classic Outlook desktop activities; SMTP, IMAP, POP3, and Exchange activities from the same package are not touched `VERIFY`. Do not pre-scan the XAML: the `analyze` run reports every affected activity per file.

## Hook 1 — Before analyze

### What the extension does

- Raises `UiPath.Mail.Activities` to at least `2.0.11`, the first Windows-compatible release, so non-Outlook mail activities keep compiling; a project already above it keeps its version (measured on 25.10.1: `[2.12.10]` left in place, SARIF note "already exists 2.12.10 and does not need to be updated to 2.0.11").
- Adds or upgrades `UiPath.MicrosoftOffice365.Activities` to at least `3.6.10`.
- Rewrites each classic Outlook activity into its Microsoft 365 connector activity and names it `Migrated <old display name>`.

### Flags

Availability and defaults come from `"<MIGRATOR_EXE>" analyze --help` on the installed build (Step 0).

| Flag | Use |
|---|---|
| `--mail-o365-package-version=<VER>` | Pass the latest stable `UiPath.MicrosoftOffice365.Activities`: `node "<SKILL_DIR>/scripts/resolve-package-lines.mjs" --package UiPath.MicrosoftOffice365.Activities --all-lines --lines 1`. The tool raises values below its built-in minimum |
| `--config=<FILE>` (alias `--mail-config`) | JSON file that supplies `ConnectionId` values and behavior overrides. Without it every migrated activity has an empty ConnectionId and is reported as action required |

Pass extension options as `--name=value`. This extension's options also bind space-separated (measured on 25.10.1 for `--config` and `--mail-o365-package-version`); the `=` form is kept because `--uia-package-version` accepts only it ([tool-behavior-guide.md § Option binding](../tool-behavior-guide.md#option-binding)).

### Connection configuration file

Modern Microsoft 365 activities run through an Integration Service connection. The classic activities had none, so the migrator cannot infer one. Keys are `"<workflow path glob> > [<connector type>] <activity display-name glob>"`, matched from most to least specific; `*` is a wildcard.

```json
{
  "* > *": { "ConnectionId": "<CONNECTION_ID_FALLBACK>" },
  "* > [uipath-microsoft-outlook365] *": { "ConnectionId": "<CONNECTION_ID_OUTLOOK>" },
  "*\\Dispatcher\\Main.xaml > [uipath-microsoft-outlook365] Get *": { "ConnectionId": "<CONNECTION_ID_DISPATCHER>" }
}
```

Connector type for this extension: `uipath-microsoft-outlook365`. Reserved key: `"SaveOutlookMailMessage_IgnoreSaveAsType": true` disables the save-as-type check so Save Outlook Mail Message migrates regardless of its format option.

Procedure before analyze:

1. Ask the user for the Integration Service connection to use for Outlook 365 (name or ID). When the platform skill is available and the user is logged in, list candidates with `uip is connections list --output json` and offer them; otherwise ask for the ID.
2. Write `<PROJECT_DIR>/.upgrade/mail-config.json` with at least the `* > [uipath-microsoft-outlook365] *` entry. The `.upgrade` folder is never copied to the output.
3. Add `--config="<PROJECT_DIR>/.upgrade/mail-config.json"` to `<PACKAGE_FLAGS>`.
4. No connection available yet: proceed without `--config`, and carry "ConnectionId must be set on every migrated mail activity" into manual work as a runtime blocker.

### Stop conditions specific to this package

None. Missing connections degrade to action-required results.

## Hook 2 — Triage

Rule IDs follow `<CLASSIC-ACTIVITY-NAME>-ACTIVITY-MIGRATION`, one rule per classic activity type, for example `SEND-OUTLOOK-MAIL-ACTIVITY-MIGRATION` `VERIFY`. Read the exact IDs from `tool.driver.rules`.

| Level | Meaning | Report as |
|---|---|---|
| `error` | Activity type not supported by the migrator; the classic activity is left in place (observed on 25.10.1: the Outlook Mail Messages Trigger, whose message also carries the prefix below) | "Not migrated", per activity; the summarizer lists it under needs attention: the tool reports it at error level and counts it as failed, unlike UIA leftovers, which it reports at note or warning level and which the left-classic count is reserved for |
| `[PostMigration Action Required]:` in the message, at `note` or `warning` level (25.10.1 reports these at `note`) | Migrated, but a property or connection needs the user | Manual work, per activity |
| `warning` without the prefix | Migrated with a caveat | Note in the report |
| `note` without the prefix | Migrated cleanly | Count |

Do not describe the classic-to-modern mapping from memory: the analyze results name each affected activity, and the migrated activity in the output XAML keeps the display name prefixed with `Migrated`, so its modern type is read from the element tag on that line. Known gaps: the Outlook Mail Messages Trigger (`umao:OutlookMailMessagesTrigger`) has no equivalent; the tool reports it at `error` level with `[PostMigration Action Required]: Migration of 'OutlookMailMessagesTrigger' is currently not supported` and leaves the activity in place; it counts under needs attention, not left classic, because the tool reports it as a failure and this guide wants it named, and it is a capability loss to report; Get Outlook Mail Messages filter options are not migrated and must be recreated by hand; attachments become `LocalResource.FromPath(...)` items; Save Outlook Mail Message is subject to the save-as-type check (see the reserved config key).

## Hook 3 — After upgrade

1. Check for empty or placeholder connections in the output:

   ```bash
   grep -rnE 'ConnectionId="(|00000000-0000-0000-0000-00000000000[0-9])"' --include=*.xaml "<OUTPUT_DIR>"
   ```

   Every hit is a runtime failure waiting to happen. List them under manual work as **Critical**.
2. Runtime prerequisites for the report: a Microsoft 365 connection in Integration Service with mail scopes, shared with the robot account that runs the process; the connection ID configured on each migrated activity.
3. Filters lost on Get Outlook Mail Messages and the trigger redesign go under manual work with their file names.
