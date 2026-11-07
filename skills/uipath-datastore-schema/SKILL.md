---
name: uipath-datastore-schema
description: "UiPath Data Store Schema resource (`kind: schema`, `resources/solution_folder/schema/*.json`): SQL tables a solution installs in Data Service through Liquibase-style JSON changesets. Create a Schema resource, pick Folder or Tenant scope, write changesets (createTable, addColumn, dropColumn, modifyDataType, createIndex, dropIndex, add/dropForeignKeyConstraint, insert, update, delete, sqlCheck preconditions), evolve it safely across upgrades, fix deploy errors, and write the SQL a coded app or agent sends to POST api/v3/QueryExecutor. For pack/publish/deploy→uipath-solution; Data Fabric entities and records→uipath-platform; coded app code→uipath-coded-apps."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Data Store Schema Resources

A Schema resource is a solution resource that installs real SQL tables in the tenant's Data Service database. Its `spec.changesets` array is a Liquibase-style JSON changelog: each deploy runs, in number order, the changesets that are not installed yet. Apps and agents then read and write the tables with SQL through `POST api/v3/QueryExecutor`.

## When to Use This Skill

- Add SQL tables to a solution, or a column, index, foreign key, or seed rows to an existing Schema resource
- Choose between folder-scoped and tenant-scoped tables
- A deploy or upgrade of a Schema resource fails, or a changeset did not do what was expected
- Write the SQL request a coded app, agent, or process sends to query or change those tables

## Critical Rules

1. **Scaffold with the CLI, then edit the JSON.** Run `uip solution resources add --source local --kind Schema --name <Name> --output json` from the solution folder. It writes `resources/solution_folder/schema/<Name>.json` with a fresh `key`. Replace `"changesets": ""` with an array, set `spec.scope`, and add `"isOverridable": false` next to `apiVersion`. Never invent or copy a `key`.
2. **Never change the `key` of an installed resource, and never delete and re-add it.** Upgrades find the installed schema by its key. A new key installs a second schema, whose `createTable` then fails with "creates table … which another schema already has".
3. **Never edit or remove an installed changeset.** An installed changeset is skipped whatever it now says; edits are silently ignored. Every change, including a fix, goes in a **new** changeset.
4. **Number new changesets above every installed one.** Numbers are whole numbers from 1 to 999999999, unique within the resource; they run in ascending order, not array order. A new number below the highest installed one is refused.
5. **Choose `scope` once.** `Folder` (default): every folder the solution deploys to gets its own copy of the tables. `Tenant`: one set of tables shared by the whole tenant. A later version cannot change it.
6. **A changeset holds only `changeset`, `changes`, and optionally `preConditions`.** No `id`, `author`, `name`, `comment`, `upSql`, or `downSql`: each is refused as an unknown property.
7. **Use only the supported changes, columns, and types** in [changes-reference.md](references/changes-reference.md). There is no `dropTable`, `renameTable`, `renameColumn`, `sql`, `autoIncrement`/identity, or `valueComputed`.
8. **Write decimal numbers as strings.** `"valueNumeric": "12.5"`, never `12.5`; a JSON number with a fraction or exponent is refused. Whole numbers may be JSON integers.
9. **A changeset may only touch its own schema's tables.** Foreign keys, `sqlCheck`, and every change must name tables this schema created in an earlier change or changeset; another Schema resource's tables are refused.
10. **Rollback, downgrade, and uninstall change no tables.** Plan forward-only changes: to undo, write a new changeset that does the reverse.

## Workflow

### 1. Create the resource (new schema only)

```bash
cd <SOLUTION_FOLDER>
uip solution resources add --source local --kind Schema --name SalesSchema --output json
```

`Data.Key` is the resource key; keep it. `spec.name` must start with a letter and use 3–100 letters or digits.

### 2. Write the changesets

Start from [schema-resource-template.json](assets/templates/schema-resource-template.json) for the shape. Change only `spec`:

```json
"spec": {
  "name": "SalesSchema",
  "scope": "Folder",
  "description": "Orders and customers",
  "changesets": [
    { "changeset": 1, "changes": [
      { "createTable": { "tableName": "Customer", "columns": [
        { "column": { "name": "Id", "type": "BIGINT", "constraints": { "primaryKey": true } } },
        { "column": { "name": "Email", "type": "NVARCHAR(320)", "constraints": { "nullable": false, "unique": true } } }
      ] } }
    ] }
  ]
}
```

Every change, column, type, value, `where`, and precondition rule: [changes-reference.md](references/changes-reference.md).

### 3. Change an installed schema

Append a changeset with the next number; leave every installed changeset exactly as it is. For example, to add a column:

```json
{ "changeset": 2, "changes": [
  { "addColumn": { "tableName": "Customer", "columns": [
    { "column": { "name": "Phone", "type": "NVARCHAR(30)" } }
  ] } }
] }
```

A new `NOT NULL` column needs a default, for the rows the table already has. Retyping or dropping a column a foreign key uses needs the foreign key dropped first: [changes-reference.md § Foreign keys](references/changes-reference.md#foreign-keys).

### 4. Check, then pack and deploy

1. Run `python3 -c "import json,sys; json.load(open(sys.argv[1]))" <file>` to confirm the file is valid JSON.
2. Read every changeset against [changes-reference.md](references/changes-reference.md); there is no local validator for changesets.
<!--skill-flavor:pack-and-deploy:start-->
3. Pack, publish, and deploy through the uipath-solution skill (`uip solution pack <SOLUTION_FOLDER> <OUTPUT_DIR> --output json`, then `publish` and `deploy`). Data Service validates the changesets at deploy; read its message against the error table in [schema-resource-guide.md](references/schema-resource-guide.md#deploy-errors).
<!--skill-flavor:pack-and-deploy:end-->

### 5. Query the tables

Apps and agents send one SQL statement with `@` parameters to `POST api/v3/QueryExecutor`, naming tables by their logical names. Request, scope headers, permissions, allowed SQL, and limits: [query-executor-guide.md](references/query-executor-guide.md).

## Reference Navigation

| Need | Read |
|---|---|
| Resource file shape, scope, upgrades, what a deploy does, deploy errors | [schema-resource-guide.md](references/schema-resource-guide.md) |
| Every change type, column, type, value, `where`, `sqlCheck`, naming rule, limit | [changes-reference.md](references/changes-reference.md) |
| Querying the tables from an app or agent | [query-executor-guide.md](references/query-executor-guide.md) |
| A blank resource file | [schema-resource-template.json](assets/templates/schema-resource-template.json) |

## Anti-patterns

- **Editing changeset 1 to add a column** to a schema that is already deployed. The edit is ignored on every tenant that has it. Add changeset 2.
- **Deleting the resource file and re-adding it** to "start over". The new key makes a second schema whose tables clash with the first.
- **Copying a Schema resource file into another solution.** Both solutions then share one resource key; for tenant scope they share one schema.
- **`upSql` / raw SQL changesets.** Not supported; every change is a JSON change.
- **Foreign keys between two Schema resources.** Put tables that reference each other in one Schema resource.
