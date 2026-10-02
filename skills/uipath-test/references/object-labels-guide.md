# Object Labels — tag metadata on test entities

Load this when the task lists, gets, adds, or removes **object labels** (tag metadata) on Test Manager entities (`uip tm objectlabel …`).

Object labels are tag metadata on `Requirement`, `TestCase`, `TestSet`, `TestExecution`, or `TestCaseLog`; use `--object-type` for the parent and `--object-ids` for targets.

- `uip tm objectlabel list --project-key <PROJECT_KEY> --object-type <Requirement|TestCase|TestSet|TestExecution|TestCaseLog>` lists distinct names, paginated; optionally `--object-ids <UUID...>`, `--label-types <UserLabel|SystemLabel|InternalLabel ...>`, `--filter <text>`, `--sort-by`, `--limit`, `--offset`.
- `uip tm objectlabel get --project-key <PROJECT_KEY> --object-type <TYPE> --object-id <UUID>` returns every assignment row on ONE object — `Id`, `ObjectId`, `ObjectType`, `Name`, `Description`, `LabelType`. Use it when the label type matters; `list` returns names only. `--object-id` takes the object's own UUID (the `Id` from `uip tm testcases list`, `testsets list`, or `requirement list`), never a label id.
- `uip tm objectlabel add --project-key <PROJECT_KEY> --object-type <TYPE> --object-ids <UUID...> --labels <name...>` attaches variadic labels across one-to-one, one-to-many, or many-to-many relationships; optionally `--remove-other-labels` for authoritative-set semantics.
- `uip tm objectlabel remove --project-key <PROJECT_KEY> --object-type <TYPE> --object-ids <UUID...> (--labels <name...> | --remove-all-labels) --yes` detaches; selectors are mutually exclusive. `--yes` is required — the CLI never prompts.

## Label types

Writes are `userLabel`-only: `add --label-type` accepts `userLabel` and nothing else. Reads are unrestricted — `list --label-types` still accepts `userLabel`, `systemLabel`, and `internalLabel`, and defaults to `userLabel` + `systemLabel`.

`remove` detaches `userLabel`s only — never `systemLabel` or `internalLabel`. Names match case-insensitively. Output: `RemovedLabels` (names removed), `SkippedSystemLabels` (matched system labels the server keeps), `SkippedInternalLabels` (internal names never sent, plus user labels sharing a name with one). `Result: Skipped` when nothing was removed, else `Removed` (`--labels`) or `AllRemoved` (`--remove-all-labels`). Max 100 `--object-ids` per call — batch larger sets. `remove` reads the objects' labels first, so it needs read access to them; when they cannot be read it returns `Result: Failure` and removes nothing.

A system label surviving a remove is expected, not a failure. `systemLabel` values are backend-owned (for example `automated` on a linked test case); `internalLabel`s are backend bookkeeping and hidden from `get`.
