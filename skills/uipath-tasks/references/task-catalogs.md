# Task Catalogs Reference

A task catalog is a reusable, folder-scoped definition that buckets related tasks
and configures how they behave: data retention (delete or archive the tasks after
a retention period), encryption of task data, and labels. Every task is associated
with at most one catalog, and it inherits that catalog's configuration when it is
linked through its metadata (`tasks metadata --catalog-id`). A catalog created in one folder is invisible from
another, and catalog IDs are numeric. See the
[Action Center documentation](https://docs.uipath.com/automation-cloud/docs/actions).

## Folder scoping

Every catalog command needs a folder. In an interactive terminal you can omit
`--folder-id` and pick a folder from a list. In a non-interactive run (a coding
agent or CI, where no picker can be shown) you must pass `--folder-id <id>`
explicitly, otherwise the command fails.

## List

```bash
# List catalogs in a folder (fetches all pages if --limit omitted)
uip tasks catalogs list --folder-id <folder-id> --output json

# Cap the number returned
uip tasks catalogs list --folder-id <folder-id> --limit 20 --output json
```

Success `Code: TaskCatalogList`, `Data` is an array.

## Get

```bash
uip tasks catalogs get <catalog-id> --folder-id <folder-id> --output json
```

Success `Code: TaskCatalogDetails`.

## Create

`--name` is required. `--encrypted` is create-only (the API forbids changing
encryption after creation).

```bash
uip tasks catalogs create \
  --name "Invoices" \
  --folder-id <folder-id> \
  --description "Invoice approvals" \
  --retention-action Delete \
  --retention-period 90 \
  --output json
```

Success `Code: TaskCatalogCreated`.

## Update

Read-modify-write: any field not passed keeps its current value. `--name` is
optional on update. `--encrypted` is not offered (immutable).

```bash
uip tasks catalogs update <catalog-id> \
  --folder-id <folder-id> \
  --name "Invoices 2026" \
  --retention-period 120 \
  --output json
```

Success `Code: TaskCatalogUpdated`.

## Retention

| Flag | Values | Notes |
|------|--------|-------|
| `--retention-action` | `Delete`, `Archive` | The two accepted retention actions |
| `--retention-period` | 1 to 180 (days) | Days before the action fires. Must be between 1 and 180; a value outside that range is rejected with an API error. |
| `--retention-bucket-id` | numeric | Storage bucket ID, required when the action is `Archive` |

> `Archive` moves tasks into a storage bucket at the retention limit, so it needs
> a `--retention-bucket-id`. `Delete` needs no bucket.
