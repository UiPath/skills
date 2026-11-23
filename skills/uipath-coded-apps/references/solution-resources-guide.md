# Solution Resources — Declare, Add to Solution, Reach by Handle

Applies to every coded app inside a solution: `project.uiproj` beside the app with a `.uipx` in a parent folder, or any app opened in Studio Web (cloud or local workspace). Standalone apps may use the same pattern; it is mandatory only in a solution (Critical Rule 23).

**Why.** Solutions maps each binding to the right tenant resource per environment, and admins change it on the post-deployment screen; both reach the app as runtime overrides. The SDK applies overrides inside by-name and handle lookups. By-id calls and `getAll()` + name match bypass them, and ids differ per environment. A literal name or folder repeats the declaration and drifts from it. A resource the app never declares has no binding, so it stays unresolved at deploy and cannot be remapped.

## Prerequisites

<!--skill-flavor:sdk-install:start-->
Install the SDK line that ships resource handles (`/resources` subpath, `1.9.0-preview.0` or newer; `uip codedapp init` pins `^1.8.4`, which lacks it):

```bash
npm install @uipath/uipath-typescript@preview --@uipath:registry=https://registry.npmjs.org
```

Verify `node_modules/@uipath/uipath-typescript/dist/resources/index.d.ts` exists. Pack and upload add declared resources to the solution and derive `bindings_v2.json` from `uip` `1.207.0-preview.340` on (`npm install -g @uipath/cli@preview --@uipath:registry=https://registry.npmjs.org`).
<!--skill-flavor:sdk-install:end-->

## 1. Declare every resource in `uipath_resources.ts`

File sits next to the app's `package.json` (in a solution project: `source/uipath_resources.ts`). Exact fields: `dist/resources/index.d.ts` (Critical Rule 19).

```typescript
import { resource } from '@uipath/uipath-typescript/resources';

export class ProjectResources {
  static readonly invoiceThreshold = resource.asset({ name: '<ASSET_NAME>', folderPath: '<FOLDER_PATH>', type: 'integer' });
  static readonly invoices = resource.bucket({ name: '<BUCKET_NAME>', folderPath: '<FOLDER_PATH>' });
  static readonly review = resource.queue({ name: '<QUEUE_NAME>' });
  static readonly nightly = resource.process({ name: '<PROCESS_NAME>', folderPath: '<FOLDER_PATH>' });
  static readonly customers = resource.entity({ name: '<ENTITY_NAME>' });
  static readonly slack = resource.connection({ id: '<CONNECTION_ID>', connector: '<CONNECTOR_KEY>', name: '<CONNECTION_NAME>' });
}
```

1. **Literal values only.** CLI and Studio Web read the file as text; a computed value is skipped with a warning.
2. **Field name:** camelCase of the resource name, as the CLI writes it (`invoiceThreshold` for `Invoice Threshold`).
3. **Folder:** existing tenant resource keeps its tenant folder; a resource the solution creates and deploys has no `folderPath`.
4. **Entity:** `name` only; the declaration has no folder field, whether the entity is tenant-scoped or folder-scoped (section 2 treats the two differently). **Connection:** `id` plus connector key; admins remap it by id.
5. **Never write `bindings_v2.json`.** Pack, push, and Studio Web publish/debug derive it from this file.

## 2. Add every declared resource to the solution

A declaration alone is not solution membership: Solutions deploys and remaps only resources the solution lists (Studio Web shows them in the Resources panel).

<!--skill-flavor:declare-shortcut:start-->
On the CLI this is automatic: `uip solution pack` and `uip solution upload` look up each declared resource and add every one the solution does not list yet, so a solution uploaded to Studio Web arrives with them. When `uip resources --help` succeeds, `uip resources add <NAME> --kind <asset|bucket|queue|process|entity|connection> [--folder-path <FOLDER_PATH> | --skip-verify] --output json` declares and adds in one step; run it from the folder holding `package.json` or pass `--project-path <APP_SOURCE_DIR>`. Pass `--skip-verify` for a resource the solution creates (no tenant lookup) and `--type <CONNECTOR_KEY>` to narrow a connection lookup. `uip resources list --output json` shows what the file declares; `uip resources sync --all --output json` declares every solution resource the file lacks (`--all` is required without a terminal). After pack or upload, run step 1 to confirm; run steps 2–3 only for a resource still missing.
<!--skill-flavor:declare-shortcut:end-->

<!--skill-flavor:add-to-solution-scope:start-->
Run the steps from the solution root (folder holding the `.uipx`) or pass `--solution-folder <SOLUTION_DIR>`.
<!--skill-flavor:add-to-solution-scope:end-->

1. List what the solution holds: `uip solution resources list --source local --output json`.
2. Add each declared resource missing from that list:

   | Declared as | Command |
   |---|---|
   | Existing tenant resource (has `folderPath`) | `uip solution resources add --source remote --kind <KIND> --name "<NAME>" --folder-path "<FOLDER_PATH>" --output json` |
   | Folder-scoped entity (created in a folder, e.g. `uip df entities create --folder-key`) | `uip solution resources add --source remote --kind Entity --name "<ENTITY_NAME>" --folder-path "<FOLDER_PATH>" --output json` |
   | Tenant-scoped entity (created without a folder) | Do not add: it is not a solution resource. The destination tenant must already hold an entity with the same name and schema (fields and SQL types); the solution does not provision it. |
   | Connection | `uip solution resources add --source remote --kind Connection --cloud-key <CONNECTION_ID> --output json` |
<!--skill-flavor:local-stub-row:start-->
   | Resource the solution creates (asset/bucket/queue without `folderPath`) | `uip solution resources add --source local --kind <KIND> --name "<NAME>" --output json` (asset: add `--type <ASSET_TYPE>`) |
<!--skill-flavor:local-stub-row:end-->

   Remote `<KIND>`: `Asset`, `Bucket`, `Queue`, `Process`. Local `<KIND>`: `Asset`, `Bucket`, `Queue` — a process the solution creates is its own project, already listed. A local asset starts with an empty value, which deploy refuses: give it a value before deploy, or tell the user.
<!--skill-flavor:add-idempotency:start-->
   Repeating an identical add returns `Status: "Unchanged"`.
<!--skill-flavor:add-idempotency:end-->
3. List again and confirm every declared resource except tenant-scoped entities is present. On no match or several matches, fix `--name` / `--folder-path` (or pass `--cloud-key`) and retry once; still failing, stop and name the missing resource to the user.

## 3. Reach resources only through their handles

| Kind | Lookup |
|---|---|
| Asset | `assets.getByName(ProjectResources.<FIELD>)` |
| Bucket | `buckets.getByName(ProjectResources.<FIELD>)` |
| Queue | `queues.getByName(ProjectResources.<FIELD>)` (result carries bound methods) |
| Process | `processes.getByName(ProjectResources.<FIELD>)` |
| Entity | `entities.getByName(ProjectResources.<FIELD>)` |
| Connection | `connections.getById(ProjectResources.<FIELD>)` (accepted wherever a connection id is) |

Methods that take a `<kind>Ref` plus folder options (`processes.start`, bucket file methods, entity record methods) apply overrides themselves: pass the handle's declared `name` and `folderPath`.

```typescript
import { Processes } from '@uipath/uipath-typescript/processes';
import { ProjectResources } from '../uipath_resources';

const { nightly } = ProjectResources;
await new Processes(sdk).start({ name: nightly.name }, { folderPath: nightly.folderPath });
```

An omitted `folderPath` means the folder the app runs in (deploy folder meta tag). Code outside the SDK (labels, links, `fetch`) reads `ProjectResources.<FIELD>.value`: the resolved `{ name, folderPath }` (connection: `{ id, folderKey? }`) an SDK call would use, with no network call.

## Anti-shapes in a solution app

| Never | Instead |
|---|---|
| `getById('<GUID>')`, a literal `processKey` or entity id | Handle lookup — ids differ per environment |
| `getAll()` then `.find(x => x.name === '<NAME>')` | `getByName(ProjectResources.<FIELD>)` |
| `{ folderId: <NUMBER> }` | Handle's `folderPath` — folder ids differ per environment |
| `getByName('<NAME>', { folderPath: '<FOLDER_PATH>' })` repeating a declaration | `getByName(ProjectResources.<FIELD>)` — one source of truth |
| A resource used in code but not declared, or declared but not in the solution (tenant-scoped entities excepted) | Sections 1 and 2 |
| `uip solution resources add` for a tenant-scoped entity | Leave it out of the solution; the destination tenant holds it |
| Hand-written `bindings_v2.json` | Declare in `uipath_resources.ts` |
