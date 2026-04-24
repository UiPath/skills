# intent-capture

## Purpose
At Build time, populate `<project>/.uipath-dashboards/state.json` with derivable config. Folder is NOT asked at Build — widgets default to tenant-wide queries (the token's permissions decide scope). Folder is a deployment concern, collected at Deploy time.

## Inputs
- User's prompt (natural language).
- `auth-context` output (env, orgName, tenantName).
- Existing state.json (may be absent on first run).

## Outputs
Updated state.json per [state-file.md](state-file.md) — `folderKey` left `null` at Build unless the prompt explicitly scopes to a folder.

## Rules
1. **Build asks nothing unless the prompt is ambiguous.** env / orgName / tenantName come from `auth-context`; `app.name` / `app.routingName` come from the prompt. No folder prompt, no clientId prompt.
2. **Folder is a Deploy concern.** Leave `folderKey: null` in state.json after Build. Deploy mode will resolve it (prompting if needed). See [../plugins/deploy/impl.md](../plugins/deploy/impl.md).
3. **Query-time folder scoping is OPT-IN via the prompt.** If the user writes "build me an agent dashboard **for the Finance folder**", the generator SHOULD resolve that folder at Build time and pass `folderId` / `folderKey` to the generated query hooks. Otherwise queries go tenant-wide (no folder header). See [data-router.md](data-router.md) § "Folder scoping at query time".
4. **Derive `app.name` from kebab-case of the prompt.** "build me an agent health dashboard" → `agent-health-dashboard`. Accept `--name <override>` if user supplies one explicitly.
5. **Derive `app.routingName` = `app.name`** by default. Must be lowercase alphanumeric + hyphens only (server enforces).
6. **Derive `semver`** — default `1.0.0` on first write; Deploy bumps per `deploy-cli.md`.

## Details

### Build-time folder resolution (ONLY when prompt explicitly mentions a folder)
If the user's prompt contains a phrase like "for the X folder", "in the X folder", or "within X folder", resolve at Build time:
```ts
import { Folders } from '@uipath/uipath-typescript';
const folders = new Folders(sdk);
const list = await folders.getAll();
const match = list.items?.find(f => f.displayName?.toLowerCase() === folderName.toLowerCase());
```
- Found → write `folderKey` to state.json; pass to generated query hooks.
- Not found → ask: "I couldn't find a folder named X. Proceed tenant-wide, pick from a list, or cancel?"
- Prompt has no folder mention → skip entirely. Don't fetch the folder list at all.

### Kebab-case derivation
Rules for turning a prompt into an app name:
1. Lowercase the prompt.
2. Extract the topic phrase (the noun phrase before "dashboard" or similar): "an agent health dashboard" → "agent health".
3. Replace whitespace + punctuation with single hyphens.
4. Strip leading/trailing hyphens.
5. If the result is empty or < 3 chars, ask the user for an explicit name.

Examples:
| Prompt | Derived name |
|---|---|
| "build me an agent health dashboard" | `agent-health-dashboard` |
| "create a queue throughput dashboard" | `queue-throughput-dashboard` |
| "chart errors" | (too vague — ask user) |

### Derived vs asked vs deferred
| Field | When set | Source |
|---|---|---|
| `env` | Build | auth-context |
| `orgName` / `tenantName` | Build | auth-context |
| `folderKey` | **Deploy** (or Build if prompt explicitly names a folder) | Deploy's folder picker, OR prompt parse |
| `app.name` / `app.routingName` | Build | derived from prompt (with `--name` override) |
| `app.semver` | Build | default `1.0.0`; Deploy manages bumps |
| `scopes` | Build | derived from generated code (see scope-map.md); informational in secret-mode |

### Error paths
| Condition | Action |
|---|---|
| `auth-context` returns `loggedIn: false` | Defer to auth-context's halt message; don't prompt for anything. |
| Derived `app.name` collides with existing dir | Ask "overwrite / rename / cancel". |
| Prompt names a folder that doesn't exist | Ask: "proceed tenant-wide / pick from list / cancel". |
