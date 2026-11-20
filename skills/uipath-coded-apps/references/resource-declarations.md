# Resource declarations (`uipath_resources.ts`) — preview

A coded app declares the Solution resources it uses (processes, entities, buckets, assets, queues, connections) **once**, in `uipath_resources.ts` next to `package.json`. The tooling derives `bindings_v2.json` from it at pack time, so Solutions can connect and override each resource on deploy. **Never write `bindings_v2.json` by hand** in a project that has `uipath_resources.ts`.

> **Preview.** Needs a CLI with the `resources` tool (`uip resources --help`) and an SDK with the `@uipath/uipath-typescript/resources` entry point. If either is missing, tell the user the feature needs the preview builds.

## Declare a resource

Run from the solution root, logged in (`uip login status --output json`):

```bash
uip resources add <Name> --kind entity  --project-path ./<app>/source
uip resources add <Name> --kind process --folder-path "Shared" --project-path ./<app>/source
uip resources add <Name> --kind bucket  --folder-path "Shared" --project-path ./<app>/source
uip resources list --project-path ./<app>/source      # what is declared, with binding keys
uip resources sync --project-path ./<app>/source      # declare solution resources the code doesn't declare yet
```

`add` looks the resource up in the tenant, writes the declaration, and adds the resource to the solution. Inside a solution, `--project-path` is the app's `source/` folder (where `package.json` is).

Generated file (do not hand-edit the shape; re-run `add` to change it):

```ts
import { resource } from '@uipath/uipath-typescript/resources';

export class ProjectResources {
    static readonly eventFeedback = resource.entity({ name: 'EventFeedback' });
    static readonly summarize = resource.process({ name: 'Summarize', folderPath: 'Shared' });
}
```

## Use the handles

Pass the handle where the SDK takes a resource name — never retype the name or folder:

```ts
import { ProjectResources } from '../uipath_resources';

await entities.insertRecord(ProjectResources.eventFeedback, { guestName, comment });
await processes.start(ProjectResources.summarize, { inputArguments: { text } });
const asset = await assets.getByName(ProjectResources.invoiceThreshold);
```

At runtime the SDK applies the deployment's overrides to the declared name and folder, so the same code works after Solutions maps a resource to a different one.

## Binding keys

| Kind | Key | Notes |
|---|---|---|
| process, bucket, asset, queue | `Name.FolderPath` (bare `Name` if no folder) | `--folder-path` is the folder at design time |
| entity | `Name` | looked up across the tenant by name |
| connection | the connection id | declared as `resource.connection({ id, connector, name })` |

Use these keys in `uipath.json` `access` entries for public apps ([public-coded-app.md](public-coded-app.md)).

## Gotchas

- **Entity names must be unique in the tenant.** `add` looks entities up by name only. If several folders hold an entity with that name (each solution deployment copies its entities into its folder), `add` warns `Found N entity resources named ... Marking unresolved` and imports an empty definition — the deploy then creates an entity without fields. Use a unique name, or remove the stale copies.
- `pack` does not build the app: run `npm run build` first.
- A declaration written while logged out stays `"Solution": "Pending"`; run `uip solution resources refresh` after logging in.
