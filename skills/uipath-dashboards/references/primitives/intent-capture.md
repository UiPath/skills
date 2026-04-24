# intent-capture

## Purpose
Populate `<project>/.uipath-dashboards/state.json` with the one value we cannot infer — `folderKey` — and derive `app.name` from the user's prompt. Everything else comes from `auth-context`.

## Inputs
- User's prompt (natural language).
- `auth-context` output (env, orgName, tenantName).
- Existing state.json (may be absent on first run).

## Outputs
Updated state.json per [state-file.md](state-file.md).

## Rules
1. **Ask for folderKey only.** Never prompt for env / orgName / tenantName / clientId / scopes — these are either inferred from `auth-context` or not needed in secret-mode auth.
2. **Derive `app.name` from kebab-case of the prompt.** "build me an agent health dashboard" → `agent-health-dashboard`. Accept `--name <override>` if user supplies one explicitly.
3. **Derive `app.routingName` = `app.name`** by default. Must be lowercase alphanumeric + hyphens only (server enforces).
4. **Folder list must be live** (Rule 4) — fetch via SDK every Build run, do NOT cache.
5. **Derive `semver`** — default `1.0.0` on first write; Deploy bumps per `deploy-cli.md`.

## Details

### Folder-list picker
Use the SDK to list folders:
```ts
// pseudo-code; agent writes this inline during a Build run
import { Folders } from '@uipath/uipath-typescript/folders';
const folders = new Folders(sdk);
const list = await folders.getAll();
```
Present to user:
```
Which folder should this dashboard query?
  1. Main (a3f2-...)
  2. Shared (b7c1-...)
  3. Engineering (d4e9-...)
  > 1
```
Record `state.json.folderKey = "a3f2-..."`.

### Kebab-case derivation
Rules for turning a prompt into a folder/app name:
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

### Derived vs asked
| Field | Source |
|---|---|
| `env` | auth-context |
| `orgName` / `tenantName` | auth-context |
| `folderKey` | user pick from live folder list |
| `app.name` / `app.routingName` | derived from prompt (with `--name` override) |
| `app.semver` | default `1.0.0`; Deploy manages |
| `scopes` | derived from generated code (see scope-map.md); informational in secret-mode |

### Error paths
| Condition | Action |
|---|---|
| `auth-context` returns `loggedIn: false` | Defer to auth-context's halt message; don't prompt for anything. |
| Folder list empty | "Your account has no folders accessible. Check Orchestrator permissions." Halt. |
| User picks an invalid index | Re-prompt up to 3 times; then halt. |
| Derived `app.name` collides with existing dir | Ask "overwrite / rename / cancel". |
