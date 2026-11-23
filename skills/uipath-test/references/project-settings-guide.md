# Project Settings Guide

```bash
uip tm project settings get    --project-key <KEY> --output json
uip tm project settings update --project-key <KEY> [--time-zone <IANA_NAME>] [--execution-name-format "<TEMPLATE>"] --output json
```

**Only the time zone and the execution name format can be changed.** `MaxNumberOfTestSteps` (fixed at 250), `GovernanceEnabled` and `GovernanceSettings` cannot be changed by any command — say so; do not invent a flag. `FolderKey` is set with `uip tm project set-default-folder` / `clear-default-folder`.

**Time zones are exact IANA names** (`Europe/Bucharest`, `America/New_York`, `UTC`); Windows names like `Romance Standard Time` fail with 400. When the user names a city, pick the IANA name and say which one you chose.

**Execution name format** — build it only from these placeholders; anything else is not rejected but shows up literally in every execution name:

- `{TestSet.Name}`
- `{Execution.Type}` → `manual`, `automated`, `autonomous`, `exploratory` or `unspecified`
- `{Execution.StartTime|<.NET date format>}`, e.g. `{Execution.StartTime|yyyyMMdd}` (default format `yyyyMMdd.HHmmss`)
- `{TestSet.<custom field name>}` — stays literal on a test set where that field is empty

Text outside braces is kept as is. Quote the template (it has spaces and `|`).

`ExecutionNameFormat: null` means no template is set: executions get the legacy name `[Automated - ]<test set name>[ <version>] - yyyyMMdd.HHmm`, not the default shown in `--help`. A test set's own name format override, when it has one, wins over the project template.

**An update with both flags can half-apply.** The time zone is written first; if the format then fails, the `Message` ends with `The time zone was already updated to '<TZ>'; only the execution name format failed.` Report exactly that, and do not re-run the time zone change.
