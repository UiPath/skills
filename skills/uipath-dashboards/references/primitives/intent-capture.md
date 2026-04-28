# intent-capture

## Purpose
At Build time, decide where the new dashboard project lives on disk and populate its state file with derivable config. Projects ALWAYS live under `<cwd>/.uipath-dashboards/<kebab-name>/` so a workspace can host many dashboards cleanly. Per-project state lives at `<project>/.dashboard/state.json` — note this is `.dashboard/`, NOT `.uipath-dashboards/`, to avoid colliding with the outer workspace dir of the same name. Folder is NOT asked at Build (Deploy concern); widgets default to tenant-wide queries.

## Inputs
- User's prompt (natural language).
- `auth-context` output (env, orgName, tenantName).
- Existing state.json (may be absent on first run).

## Outputs
Updated state.json per [state-file.md](state-file.md) — `folderKey` left `null` at Build unless the prompt explicitly scopes to a folder.

## Rules
1. **Build asks nothing unless the prompt is ambiguous.** env / orgName / tenantName come from `auth-context`; `app.name` and `app.routingName` come from the prompt. No folder prompt at Build.
2. **Folder is a Deploy concern.** Leave `folderKey: null` in state.json after Build. Deploy mode will resolve it (prompting if needed). See [../plugins/deploy/impl.md](../plugins/deploy/impl.md).
3. **Query-time folder scoping is OPT-IN via the prompt.** If the user writes "build me an agent dashboard **for the Finance folder**", the generator SHOULD resolve that folder at Build time and pass `folderId` / `folderKey` to the generated query hooks. Otherwise queries go tenant-wide (no folder header). See [data-router.md](data-router.md) § "Folder scoping at query time".
4. **`app.name` is the user-friendly display name** — Title Case derived from the prompt. "build me an agent health dashboard" → `Agent Health Dashboard`. This is the title rendered in the dashboard's own Header chrome and in the deploy plan output. (The Governance Unified Portal currently displays the routing slug, not `app.name`, until the CLI exposes a `--title` flag — see [../plugins/deploy/impl.md § Note on the displayed title](../plugins/deploy/impl.md).) Accept `--name <override>` if the user supplies one explicitly.
5. **`app.routingName` is the deploy slug** — `govdash-<kebab-of-app.name>-<4-rand-chars>`. The `govdash-` prefix scopes deploys to a recognizable namespace; the kebab encodes the app name; the 4-char random suffix avoids collisions with prior deploys (or other users' deploys) of the same dashboard name. Server enforces lowercase alphanumeric + hyphens AND a 32-character total length cap. With `govdash-` (8 chars) + `-<4rand>` (5 chars) reserved, the kebab body must fit in 19 characters. `scaffold-project.sh` enforces this by applying common abbreviations (`observability` → `obs`, `dashboard` → `dash`, `monitoring` → `mon`, `performance` → `perf`, etc.) before falling back to last-hyphen truncation.
6. **Project always lives at `<cwd>/.uipath-dashboards/<kebab-of-app.name>/`.** The project directory uses the kebab form (no random suffix, no `gov-dashboard-` prefix) so a user revisiting their workspace sees clean directory names. Random suffix is appended only at deploy-time to the routing name.
7. **Project-name collision: append numeric suffix.** If `<cwd>/.uipath-dashboards/<kebab>/` already exists with a `.dashboard/state.json` inside, treat as an existing dashboard. Two paths:
   - User clearly wants to update the existing one (incremental Build prompt) → operate on it; reuse the existing routingName from state.json.
   - User clearly wants a new one (e.g., the prompt is materially different) → suffix the directory with `-1`, `-2`, etc. and generate a fresh routingName for the new project.
   - Ambiguous → ask: *"You already have an Agent Health Dashboard. Update it, or create a new one?"*
8. **Derive `semver`** — default `1.0.0` on first write; Deploy bumps per `deploy-cli.md`.

## Details

### Routing-name generation (canonical recipe)

The full recipe lives in `scaffold-project.sh`. Conceptually:

```bash
# 1. Kebab-case the app name
KEBAB=$(echo "$APP_NAME" | tr '[:upper:]' '[:lower:]' | tr -s ' ' '-' | tr -cd 'a-z0-9-')

# 2. Apply abbreviations to fit the 19-char kebab-body cap (32 total minus
#    "govdash-" prefix and "-<4rand>" suffix)
KEBAB="${KEBAB//observability/obs}"
KEBAB="${KEBAB//dashboard/dash}"
KEBAB="${KEBAB//performance/perf}"
KEBAB="${KEBAB//monitoring/mon}"
KEBAB="${KEBAB//throughput/tput}"
KEBAB="${KEBAB//invocation/invoc}"
# ... (see scaffold-project.sh for the full table)

# 3. If still too long, truncate at last hyphen within the cap
[[ ${#KEBAB} -gt 19 ]] && KEBAB="${KEBAB:0:19}" && KEBAB="${KEBAB%-*}"

# 4. Generate a 4-char lowercase-alphanumeric suffix
SUFFIX=$(LC_ALL=C tr -dc 'a-z0-9' </dev/urandom | head -c 4)

# 5. Compose
ROUTING_NAME="govdash-${KEBAB}-${SUFFIX}"
```

Examples:
| `app.name` (display) | `app.routingName` |
|---|---|
| `Agent Health Dashboard` | `govdash-agent-health-dash-x7k2` (18-char body) |
| `Agent Observability Dashboard` | `govdash-agent-obs-dash-q4n7` (14-char body) |
| `Queue Throughput Dashboard` | `govdash-queue-tput-dash-9fp1` (15-char body) |
| `Engineering Cost` | `govdash-engineering-cost-mq3d` (16-char body) |

The 4-char random suffix gives ~1.6M permutations — collisions are vanishingly rare. **If a deploy still fails on routingName uniqueness, regenerate the suffix and retry** (handled in [../plugins/deploy/impl.md § Routing-name retry](../plugins/deploy/impl.md)).

**The Plan-phase agent MUST compute the routing name via this recipe before showing the plan to the user** — so the slug shown in the plan matches the slug actually deployed.

### Build-time folder resolution (ONLY when prompt explicitly mentions a folder)
If the user's prompt contains a phrase like "for the X folder", "in the X folder", or "within X folder", resolve at Build time. **Use the CLI form, not the SDK form** — Build mode and Deploy mode should agree on tooling for tenant reads:
```bash
uip or folders list --all -n "<folder-name>" --output json
```
- The `--all` flag fetches the full tenant folder list (default omits folders the calling user can't access).
- The `-n <name>` filter looks up by display name in one round-trip — never make the user pick from a list when they already named the folder.

Parse `Data[0].Key` (the folder key). If empty result → ask: "I couldn't find a folder named X. Proceed tenant-wide, pick from a list, or cancel?"

If the prompt has no folder mention → skip entirely. Don't fetch the folder list at all.

### Title-case → kebab derivation
Rules for turning a prompt into the display name + project directory:
1. Extract the topic phrase (the noun phrase before "dashboard" or similar): "an agent health dashboard" → "agent health".
2. Append "Dashboard" if missing: "agent health" → "Agent Health Dashboard".
3. Title-case for `app.name`: "Agent Health Dashboard".
4. Lowercase + hyphenate for the project directory: `agent-health-dashboard`.
5. If the result is empty or < 3 chars, ask the user for an explicit name.

Examples:
| Prompt | `app.name` (display) | Project dir |
|---|---|---|
| "build me an agent health dashboard" | `Agent Health Dashboard` | `agent-health-dashboard` |
| "create a queue throughput dashboard" | `Queue Throughput Dashboard` | `queue-throughput-dashboard` |
| "chart errors" | (too vague — ask user) | — |

### Derived vs asked vs deferred
| Field | When set | Source |
|---|---|---|
| `env` | Build | auth-context |
| `orgName` / `tenantName` | Build | auth-context |
| `folderKey` | **Deploy** (or Build if prompt explicitly names a folder) | Deploy's folder picker, OR prompt parse |
| `app.name` | Build | derived from prompt as Title Case (with `--name` override) |
| `app.routingName` | Build (Plan-phase agent calls `derive-routing-name.sh`) | `govdash-<kebab>-<4-rand>` |
| `app.semver` | Build | default `1.0.0`; Deploy manages bumps |
| `scopes` | Build | derived from generated code (see scope-map.md); informational in secret-mode |

### Error paths
| Condition | Action |
|---|---|
| `auth-context` returns `loggedIn: false` | Defer to auth-context's halt message; don't prompt for anything. |
| Derived project dir collides with existing one | Ask "overwrite / rename / cancel". |
| Prompt names a folder that doesn't exist | Ask: "proceed tenant-wide / pick from list / cancel". |
