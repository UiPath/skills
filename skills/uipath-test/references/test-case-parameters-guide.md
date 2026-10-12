# Test Case Parameters Guide

Parameters are named inputs on a **test case** (name, default value, hint, type). Manage them with `uip tm testcases parameters`. Only test cases have parameters — not requirements, test sets or executions.

## Commands

Every command takes the project (`--project-key <KEY>` or `--project-id <UUID>`) and the test case (`--test-case-key <PROJECT_KEY:NUMBER>` or `--test-case-id <UUID>`).

| Command | Does |
|---|---|
| `parameters list ... [--search <prefix>] [--sort-by 'name asc'] [--limit <n>] [--offset <n>]` | Lists the test case's parameters. `--limit` defaults to 50; page with `--offset`. |
| `parameters get ... (--parameter-name <name> \| --parameter-id <UUID>)` | Gets one parameter. |
| `parameters add ... --name <name> --default-value <value> [--hint <text>] [--type Text\|Asset]` | Adds one parameter. `--default-value ""` stores an empty value. |
| `parameters update ... (--parameter-name <name> \| --parameter-id <UUID>) [--new-name <name>] [--default-value <v>] [--hint <t>] [--type <t>]` | Changes only the fields you pass. |
| `parameters delete ... --parameter-ids <UUID...> --yes` | Deletes one or more by id (up to 100 per call). |

The value flag is `--default-value`, not `--value`:

```bash
uip tm testcases parameters add --project-key <KEY> --test-case-key <KEY:N> --name Timeout --default-value 30 --output json
```

`--type Text` stores the value as typed (the default). `--type Asset` stores an Orchestrator asset **name** that the robot resolves at run time — use it when the user says the value lives in an asset.

## Name matching — exact, not fuzzy

- Names are unique per test case and compared **without case**: `Username` and `username` are the same parameter.
- `get --parameter-name` and `update --parameter-name` need the exact name (any case). `User name` does **not** find `Username`; it fails with `The test case has no parameter named 'User name'.`
- `list --search` matches the **start** of the name, any case: `--search user` finds `Username` and `Userid`; `--search name` finds neither.

So when the user's name does not match exactly, list the test case's parameters, pick the closest one, and **ask the user to confirm** it before you change or delete anything. Never act on a guessed match.

**Checking whether a parameter exists:** run `list --search <name>` and look for a row whose `Name` equals the name, ignoring case. An empty list here is the answer "it does not exist", not a reason to stop (Critical Rules 4 and 10). Do not probe with `get --parameter-name`: it fails with `not_found` when the parameter is missing.

Listing all of a test case's parameters (at most 250; page with `--offset`) and comparing names yourself is expected for closest-name matches and bulk adds — `--search` only matches the start of a name, so it cannot answer those (an exception to Critical Rule 8).

## Find the test case first

Resolve the test case before any parameter call. With a key (`ABC:123`) use it directly. With a name, run `uip tm testcases list --project-key <KEY> --filter <name> --output json` (`--filter` is a **prefix** match). If one row's `Name` equals the given name exactly, use it. Zero matches: apply Critical Rule 8's prefix fallback, and only if that also finds nothing, tell the user the test case does not exist and stop. Several matches and none exact: list them and ask which one. `HTTP 404: TestCase does not exist.` or `No test case found with key '<key>'.` also means stop and tell the user.

## What to do, by request

| Request | Do |
|---|---|
| Add a parameter | Check first with `list --search <name>` (see above). If it already exists, **say so and ask for another name** — do not update it instead. If it does not, `add`. |
| Change a default value or hint, parameter not found | Ask whether to create it with that value. Create it only if the user says yes. |
| Rename, parameter not found | Tell the user it does not exist and stop. Do not create one. |
| Rename to a name another parameter already has | The CLI rejects it (`The test case already has a parameter named '<name>'.`). Report that. Never delete or overwrite the other parameter to make room. |
| Delete one | Confirm the exact parameter with the user unless they already approved that delete, then `delete --parameter-ids <id> --yes`. |
| Delete "all" | First list them and tell the user the names and the count, get confirmation, then delete their ids. More than 100 ids → several calls. |
| Add the same parameters to several test cases | See [Bulk add](#bulk-add-across-test-cases). |
| Which test cases share parameters | No command does this. List each test case's parameters and compare the names without case. |

## Read the delete result, not just `Result`

`delete` returns `Result: "Success"` with counts, even when nothing was deleted:

```json
{ "Result": "Success", "Code": "TestCaseParameterDelete", "Data": { "Passed": 0, "Failed": 1 } }
```

An id that does not exist (or belongs to another test case) is counted in `Failed`, not reported as an error. Report `Passed` and `Failed` to the user; if `Failed` is more than 0, say which part did not go through.

Without `--yes`, `delete` does nothing and fails with `Confirmation required: …`.

## Bulk add across test cases

There is no bulk command. For each test case, list its parameters once, then `add` only the ones it does not have yet:

1. `parameters list` for the test case (page through if it has more than 50). An empty list means there is nothing to skip.
2. For each requested parameter: if a parameter with that name exists (compare without case), **skip it and leave its value alone**. Otherwise `add` it.
3. Finish with a summary **per test case**: which parameters were added and which were skipped because they already existed.

Never `update` an existing parameter during a bulk add unless the user asked to overwrite values.

## Limits and rules

- At most 250 parameters per test case.
- Name: up to 255 characters; letters, digits, spaces, `.`, `_` and `-` only; `clipboard` is reserved. Default value and hint: up to 2048 characters each.
- `list` and `get` omit `Hint` when no hint is set.
