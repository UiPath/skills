# Object Labels — tag metadata on test entities

Load this when the task lists, gets, adds, or removes **object labels** (tag metadata) on Test Manager entities (`uip tm objectlabel …`).

Object labels are tag metadata on `Requirement`, `TestCase`, `TestSet`, `TestExecution`, or `TestCaseLog`; use `--object-type` for the parent and `--object-ids` for targets.

- `uip tm objectlabel list --project-key <PROJECT_KEY> --object-type <Requirement|TestCase|TestSet|TestExecution|TestCaseLog>` lists distinct names, paginated; optionally `--object-ids <UUID...>`, `--label-types <UserLabel|SystemLabel|InternalLabel ...>`, `--filter <text>`, `--sort-by`, `--limit`, `--offset`.
- `uip tm objectlabel get --project-key <PROJECT_KEY> --label-id <UUID>` gets an assignment row. `add --project-key <PROJECT_KEY> --object-type <TYPE> --object-ids <UUID...> --labels <name...>` attaches variadic labels across one-to-one, one-to-many, or many-to-many relationships; optionally `--remove-other-labels` for authoritative-set semantics. `remove --project-key <PROJECT_KEY> --object-type <TYPE> --object-ids <UUID...> (--labels <name...> | --remove-all-labels)` detaches; selectors are mutually exclusive.
