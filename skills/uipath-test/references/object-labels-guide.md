# Object Labels — tag metadata on test entities

Load this when the task lists, gets, adds, or removes **object labels** (tag metadata) on Test Manager entities (`uip tm objectlabel …`).

Object labels are tag metadata on `Requirement`, `TestCase`, `TestSet`, `TestExecution`, or `TestCaseLog`; use `--object-type` for the parent and `--object-ids` for targets.

- `uip tm objectlabel list --project-key <PROJECT_KEY> --object-type <Requirement|TestCase|TestSet|TestExecution|TestCaseLog>` lists distinct names, paginated; optionally `--object-ids <UUID...>`, `--label-types <UserLabel|SystemLabel|InternalLabel ...>`, `--filter <text>`, `--sort-by`, `--limit`, `--offset`.
- `uip tm objectlabel get --project-key <PROJECT_KEY> --object-type <TYPE> --object-id <UUID>` returns every assignment row on ONE object — `Id`, `ObjectId`, `ObjectType`, `Name`, `Description`, `LabelType`. Use it when the label type matters; `list` returns names only. `--object-id` takes the object's own UUID (the `Id` from `uip tm testcases list`, `testsets list`, or `requirement list`), never a label id.
- `add --project-key <PROJECT_KEY> --object-type <TYPE> --object-ids <UUID...> --labels <name...>` attaches variadic labels across one-to-one, one-to-many, or many-to-many relationships; optionally `--remove-other-labels` for authoritative-set semantics.
- `remove --project-key <PROJECT_KEY> --object-type <TYPE> --object-ids <UUID...> (--labels <name...> | --remove-all-labels) --yes` detaches; selectors are mutually exclusive. `--yes` is required — the CLI never prompts.

## Label types

Writes are `userLabel`-only: `add --label-type` accepts `userLabel` and nothing else. Reads are unrestricted — `list --label-types` still accepts `userLabel`, `systemLabel`, and `internalLabel`, and defaults to `userLabel` + `systemLabel`.

`remove` never detaches a `systemLabel`, on either selector. Both `--labels` and `--remove-all-labels` skip them server-side and still report `Result: Removed` — so a system label surviving a remove is expected, not a failure. `systemLabel` values are backend-owned (for example `automated` on a linked test case); to see which labels on an object are system-owned, use `get` and read `LabelType`.
