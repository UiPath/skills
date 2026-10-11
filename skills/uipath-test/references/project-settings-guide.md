# Project Settings Guide

Read and change a Test Manager project's settings record with `uip tm project settings`. Pass `--output json` to every command.

## Commands

| Command | Does |
|---|---|
| `uip tm project settings get --project-key <PROJECT_KEY> --output json` | Reads the whole record. |
| `uip tm project settings update --project-key <PROJECT_KEY> [--time-zone <IANA_NAME>] [--execution-name-format <TEMPLATE>] --output json` | Writes the time zone, the execution name format, or both. At least one is required. |

Both take `--project-id <UUID>` instead of `--project-key`; the id wins when both are given.

`get` returns `TimeZone`, `ExecutionNameFormat`, `MaxNumberOfTestSteps`, `FolderKey`, `GovernanceEnabled` and `GovernanceSettings`, plus `Id`, `ProjectId` and `ProjectKey`. `ExecutionNameFormat: null` means no template is set. Executions then get the legacy name `[Automated - ]<test set name>[ <version>] - yyyyMMdd.HHmm` (UTC), not the template shown in the CLI help.

## Only two fields are writable

`update` changes `TimeZone` and `ExecutionNameFormat` and nothing else. No flag and no other command changes the rest through this record:

| Field | What to tell the user |
|---|---|
| `MaxNumberOfTestSteps` | Fixed at 250 when the project is created. Nothing can raise or lower it. Report the cap, never offer to change it. |
| `FolderKey` | Set it with `uip tm project set-default-folder`, clear it with `project clear-default-folder` — not with `settings update`. |
| `GovernanceEnabled`, `GovernanceSettings` | Read-only here. The CLI has no command that configures governance. |

When a user asks to change one of these, say it cannot be done this way. Do not invent a flag.

## Time zones are IANA names

`--time-zone` takes an exact, case-sensitive IANA (tz database) name: `Europe/Bucharest`, `America/New_York`, `Asia/Kolkata`, `UTC`. Windows names such as `Romance Standard Time` or `Eastern Standard Time` fail with `HTTP 400 ... Project Timezone must be a valid TimeZone.`

When the user gives a city or a casual name ("Bucharest", "Eastern time", "IST"), pick the IANA name yourself and **say which one you chose** in your reply, so the user can correct it. The CLI cannot list valid time zones.

## Execution name format

The template builds the name of every new test execution in the project, except for a test set that has its own name format override (set outside the CLI), which wins. Use only these placeholders, written exactly as shown:

| Placeholder | Renders |
|---|---|
| `{TestSet.Name}` | The test set's name. |
| `{Execution.Type}` | `manual`, `automated`, `autonomous`, `exploratory` or `unspecified`. |
| `{Execution.StartTime}` | The start time. Add a .NET date format after a pipe: `{Execution.StartTime|yyyyMMdd.HHmmss}`. Default format `yyyyMMdd.HHmmss`. |
| `{TestSet.<custom field name>}` | A Test Set custom field's value, for example `{TestSet.Release}`. |

Text outside braces is copied as is. A misspelled or invented placeholder is **not** rejected: it shows up literally in every execution name. So does `{TestSet.<custom field name>}` on a test set where that field is empty, and a date format after the pipe that .NET cannot parse. Build the template only from the placeholders above, and for custom fields use a Test Set custom field that exists (see [custom-fields-guide.md](custom-fields-guide.md)).

The CLI help calls `{Execution.Type} - {TestSet.Name} - {Execution.StartTime|yyyyMMdd.HHmmss}` the default. The server uses it only for an execution with no test set; a project with no template gets the legacy name above. Suggest it as a starting point, but do not tell the user their executions are already named that way.

Quote the template in the shell; it contains spaces and `|`:

```bash
uip tm project settings update --project-key <PROJECT_KEY> \
  --execution-name-format "{TestSet.Name} - {Execution.StartTime|yyyyMMdd}" --output json
```

A template over 1024 characters is rejected. A shorter one whose rendered name runs past 1024 characters is cut and ends with `...`.

## Updating both at once can half-apply

With both flags, the CLI writes the time zone first and the format second, as two separate requests. If the format fails after the time zone went through, the failure `Message` ends with `The time zone was already updated to '<TZ>'; only the execution name format failed.` Report it as exactly that: the time zone changed, the format did not. Do not say the whole update failed, and do not re-run the time zone change.

## Success output

`Data` echoes `ProjectId`, `ProjectKey` (only when you passed `--project-key`), the fields written, and `Result: "Updated"` — inside the usual envelope, so the top-level `Result` is `Success`:

```json
{ "Result": "Success", "Code": "ProjectSettingsUpdate",
  "Data": { "ProjectId": "…", "ProjectKey": "DEMO", "TimeZone": "Europe/Bucharest", "Result": "Updated" } }
```

To confirm the full record afterwards, run `settings get`.
