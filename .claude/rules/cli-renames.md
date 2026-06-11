# Retired `uip` CLI Verbs

Verbs the CLI used to ship but has since renamed or removed. Drives the **Medium**-severity hint in `/lint-task`'s CLI-verb axis: when a task's `command_pattern` only matches a verb in this table, the linter suggests the canonical replacement.

The catalog at `assets/uip-catalog-snapshot.json` is the source of truth for which verbs **currently exist**. This file is the source of truth for which verbs **used to exist** and where they moved.

| Retired                | Canonical            | Retired at |
|------------------------|----------------------|------------|
| `flow`                 | `maestro flow`       | uip 1.2.0  |
| `solution new`         | `solution init`      | uip 1.2.0  |
| `is resources execute` | `is resources run`   | uip 1.1.0  |
| `resource`             | `or`                 | uip 1.196.0|


## When to add an entry

Add a row when the CLI renames or removes a verb that was previously documented in this repo (skill examples or task YAMLs). Drop the row once `grep -r '<retired verb>' tests/ skills/` returns nothing — the registry is for verbs still referenced somewhere in the repo.

## How it's used

`scripts/check-cli-verbs.py` parses this table at runtime. The first two pipe-delimited columns are read as `retired` and `canonical`. The third column is informational only.
