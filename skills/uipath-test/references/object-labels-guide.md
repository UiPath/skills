# Object Labels — tag metadata on test entities

Load for tasks that list, get, add, or remove object labels on Test Manager entities (`uip tm objectlabel …`). Labels are tag metadata on `Requirement`, `TestCase`, `TestSet`, `TestExecution`, or `TestCaseLog`; `--object-type` selects the parent and `--object-ids` the targets.

- `uip tm objectlabel list --project-key <PROJECT_KEY> --object-type <Requirement|TestCase|TestSet|TestExecution|TestCaseLog>` lists distinct names (paginated). Optional flags: `--object-ids <UUID...>`, `--label-types <UserLabel|SystemLabel|InternalLabel ...>`, `--filter <text>`, `--sort-by`, `--limit`, `--offset`.
- `uip tm objectlabel get --project-key <PROJECT_KEY> --label-id <UUID>` gets an assignment row.
- `add --project-key <PROJECT_KEY> --object-type <TYPE> --object-ids <UUID...> --labels <name...>` attaches variadic labels across one-to-one, one-to-many, or many-to-many relationships; optionally use `--remove-other-labels` for authoritative-set semantics.
- `remove --project-key <PROJECT_KEY> --object-type <TYPE> --object-ids <UUID...> (--labels <name...> | --remove-all-labels)` detaches labels; selectors are mutually exclusive.