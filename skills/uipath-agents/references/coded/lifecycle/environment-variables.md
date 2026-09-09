# Coded Agent Environment Variables

Where a coded agent's environment variables are stored, which store the runtime reads, and how to pull a value from an Orchestrator asset instead of hardcoding it.

## Three stores, one variable

Not the same store. Only one is what the cloud runtime reads.

| Store | Read by | Authored with |
|-------|---------|---------------|
| `<PROJECT_DIR>/.env` | Local runs only (`uip codedagent run`, `uipath run`) | Edit file directly |
| Project configuration (AgentHub) | Cloud runtime, every debug and Studio Web run | Studio Web → agent properties → **Coded agent environment variables**. VS Code extension mirrors `.env` here on debug |
| Orchestrator process / job environment variables | Published agent started as an Orchestrator job | `uip or processes update --environment-variables`, or per job on `jobs start` — see [`uipath-platform` run-jobs](../../../../uipath-platform/references/orchestrator/run-jobs.md) |

Consequences:

1. **`.env` is not pushed.** `uip codedagent push` excludes it — see [file-sync](file-sync.md) § Files Involved. Editing `.env` alone changes nothing in the cloud.
2. **Local and cloud runs can disagree.** Different stores. Diagnose a cloud-only failure by comparing both, not by trusting `.env`.
3. **No credentials in `.env`.** `UIPATH_URL`, `UIPATH_ACCESS_TOKEN`, org/tenant identifiers come from the `uip login` session. `UIPATH_PROJECT_ID` is the one identity value that belongs there.

## Referencing an Orchestrator asset

Set a variable's whole value to `%ASSETS/<ASSET_NAME>%`. The platform substitutes the asset's value before the agent process starts; the agent reads an ordinary environment variable and never calls the Assets API.

```env
MY_API_KEY=%ASSETS/ServiceApiKey%
DATABASE_HOST=%ASSETS/DbHost%
```

```python
import os

api_key = os.getenv("MY_API_KEY")
```

The asset name stays out of the code, so it can be re-pointed per environment without a code change.

### Format rules

1. **Whole value only.** `%ASSETS/Name%` resolves. `https://%ASSETS/Host%/api` does not — passed through as literal text, no error.
2. **Uppercase prefix: `%ASSETS/`.** One parser in the chain compares the prefix case-sensitively, so `%assets/Name%` silently fails to resolve on the published path even though the design-time editor accepts it.
3. **Asset name matched case-insensitively.** Name only between the slash and closing `%` — no folder path.
4. **One asset per variable.** No concatenation, no default value.

### Lookup folder

The reference carries no folder, so the folder comes from the launch path. Most common reason a reference resolves in one place but not another:

| Launch path | Lookup folder |
|-------------|---------------|
| Debug run (Studio Web or VS Code extension) | User's **personal workspace** |
| Published agent started as an Orchestrator job | The **job's** folder — not the agent's, not where the package was published |

An asset that exists only in a solution folder resolves for the deployed agent but not while debugging. Create it in the personal workspace too when both paths are needed.

### Asset value types

`Text`, `Bool`, `Integer`, `Secret` resolve. `KeyValueList` and connection-string types have no single-string form and never resolve. Credential types behave differently across the debug and published paths — do not reference them from an environment variable.

### Failures are silent

> An unresolvable reference — asset missing from the lookup folder, no permission, unsupported value type, lowercase prefix — does NOT fail the job and does NOT log a user-visible error. The value resolves to empty and the variable is then dropped from the process environment, so the agent sees it as unset. Nothing anywhere reports why.

Fail loudly in agent code instead:

```python
api_key = os.getenv("MY_API_KEY")
if not api_key:
    raise ValueError("MY_API_KEY is not set — check the referenced asset exists in the job's folder")
```

## Solution resources

Saving env vars in Studio Web also registers each referenced asset as a resource on the surrounding solution.

## Anti-patterns

1. **Do not expect `%ASSETS/...%` to resolve locally.** Substitution is server-side. `uip codedagent run` reads `.env` verbatim, so `os.getenv` returns the literal `%ASSETS/Name%`. Put a real value in `.env` for local testing.
2. **Do not embed a reference in a larger string.** Format rule 1 — no substitution, no warning.
3. **Do not add a variable to `.env` and expect a cloud run to see it.** `.env` is not pushed. Update the project configuration, or debug from the VS Code extension, which mirrors the file.
4. **Do not log a resolved secret.** After substitution it is an ordinary string in the process environment; dumping the environment exposes it.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Agent prints literal `%ASSETS/Name%` | Local run | Expected. Put a real value in `.env`. For a cloud run, check the project configuration, not `.env` |
| Variable unset in a cloud run | Reference did not resolve, variable dropped | Confirm the asset exists in the lookup folder for that launch path: `uip or assets list --folder-path "<FOLDER_PATH>" --output json` |
| Resolves when deployed, not when debugging | Asset is in the solution folder; debug looks in the personal workspace | Create the asset in the personal workspace too |
| Stored with lowercase prefix | `%assets/` fails the case-sensitive prefix check on the published path | Rewrite as `%ASSETS/` |
