# Task Catalogs Reference

Task catalogs group tasks and define their retention policy. Folder-scoped: a
catalog created in one folder is invisible from another. Catalog IDs are numeric.

## Folder scoping

Every catalog command is folder-scoped. Pass `--folder-id <id>`, or omit it on an
interactive terminal to pick a folder from a list. `--folder-id` is required when
stdout is not a TTY (coding agents, CI) — pass it explicitly there.

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
| `--retention-period` | days (positive integer) | Days before the action fires |
| `--retention-bucket-id` | numeric | Storage bucket ID — required when the action is `Archive` |

> `Archive` moves tasks into a storage bucket at the retention limit, so it needs
> a `--retention-bucket-id`. `Delete` needs no bucket.
