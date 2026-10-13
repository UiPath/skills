# Test Case Parameters Guide

Parameters belong to **test cases only** (not requirements, test sets or executions).

```bash
uip tm testcases parameters list   --project-key <KEY> --test-case-key <KEY:N> [--search <prefix>] [--limit <n>] [--offset <n>] --output json
uip tm testcases parameters add    --project-key <KEY> --test-case-key <KEY:N> --name <name> --default-value <value> [--hint <text>] [--type Text|Asset] --output json
uip tm testcases parameters update --project-key <KEY> --test-case-key <KEY:N> --parameter-name <name> [--new-name <n>] [--default-value <v>] [--hint <t>] [--type <t>] --output json
uip tm testcases parameters delete --project-key <KEY> --test-case-key <KEY:N> --parameter-ids <UUID...> --yes --output json
```

The value flag is `--default-value` (not `--value`); `""` stores an empty value. `--type Asset` stores an Orchestrator asset name the robot resolves at run time. `update` changes only the fields you pass. `get --parameter-name|--parameter-id` reads one.

**Find the test case first.** Use the key, or `uip tm testcases list --project-key <KEY> --filter <name> --output json` (prefix match) and prefer the row whose name matches exactly. Nothing found after Critical Rule 8's prefix fallback, or `TestCase does not exist`: tell the user and stop. Several matches: ask.

**Names are unique per test case, ignoring case, and matched exactly — never fuzzily.** `User name` does not find `Username`. To check whether one exists, run `list --search <name>` and look for an exact (case-insensitive) `Name`; an empty list means "not there", not a Rule 4/10 stop. Do not probe with `get`, which fails when it's missing. For a near miss, list all of the test case's parameters (≤250; comparing them yourself is expected here, `--search` is prefix-only) and ask the user to confirm the closest one before changing anything.

| Request | Do |
|---|---|
| Add, name already exists | Say so and ask for another name; don't update it instead |
| Change value or hint, parameter missing | Ask whether to create it |
| Rename or delete, parameter missing | Tell the user and stop |
| Rename onto a name in use | Report the CLI's refusal; never remove the other parameter |
| Delete | Confirm the exact parameter (Rule 5); for "all", show names and count first; >100 ids → several calls |

**`delete` returns `Result: Success` even when nothing was deleted** — read `Data.Passed` / `Data.Failed` and report both.

**Bulk add across test cases** (no bulk command): per test case, `list` once, `add` only the missing names, leave existing ones untouched (never `update`), then summarise added vs skipped per test case. "Which test cases share parameters" also has no command: list each and compare names.
