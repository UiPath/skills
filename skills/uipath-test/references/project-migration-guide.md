# Project Migration Guide

Back up, copy or move a project as a `.tmh` package; export and import are jobs of a minute or more. Flags: `uip tm project export --help`, `uip tm project import --help`.

## Back up (export) a project

1. `uip login status --output json`, then `uip tm project list --filter <KEY>`.
2. `uip tm project export --project-key <KEY> --wait --output-file <name>.tmh`.
3. Without `--wait`, follow `Instructions`: `uip tm migration get --project-key <KEY> --job-id <id>` until `Completed`, then `uip tm migration download --project-key <KEY> --job-id <id> --output-file <name>.tmh`. Lost the id: `uip tm migration list --project-key <KEY> --type exportProject`.

- Never start a second export to check on one; a timeout means still running.
- An existing `--output-file` is refused; ask before `--overwrite`.
- Automation is in by default (`--exclude automation` drops it); governance, project-config and prompts only with `--include`. project-config needs Test Cloud (else 403: tell the user and stop).

## Copy a project in the same tenant

1. Export as above.
2. `uip tm project import --file <name>.tmh --create-project --new-project-key <NEW_KEY> --new-project-name "<NEW_NAME>" --wait`.
3. Verify: `uip tm testcases list --project-key <NEW_KEY>` and `uip tm testsets list --project-key <NEW_KEY>`.

- The package's key is taken here: ask for the new key and name, never pick them.

## Move to another tenant or environment

1. Export as above.
2. Another tenant: `uip login tenant set <tenant-name>`. Another environment: log in there (a named `--profile` keeps both sessions).
3. Ask: an existing project (`--project-key`) or a new one (`--create-project`)?
4. Import with `--wait`, then verify as above.

- Never import before asking where. A 403: name the tenant that refused and stop.

## Import a package you were given

1. Ask: existing project or new? A taken key: ask for `--new-project-key`.
2. `uip tm project import --file <pkg>.tmh (--project-key <KEY> | --create-project) --wait`. A new project stays inactive until the import finishes.

- Never guess the target. Import's `--include`/`--exclude` take governance, project-config, automation (no prompts).
- A failed or cancelled job: report its message and stop.

## Format

Test sets travel only as `.tmh`, so don't ask. Test cases and requirements can also go to Excel (`testcases export`, `requirements export`). "Export" with no format or purpose: ask.
