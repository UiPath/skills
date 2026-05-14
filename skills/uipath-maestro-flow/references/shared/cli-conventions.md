# CLI Conventions

Shared conventions for the `uip` CLI that apply across **all three capabilities** (Author, Operate, Diagnose). Read this first when invoking any `uip` command — every capability assumes these mechanics.

## 1. Resolve the `uip` binary

The `uip` CLI is installed via npm. Resolve the binary (it may not be on PATH in nvm environments):

```bash
UIP=$(command -v uip 2>/dev/null || echo "$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip")
```

If `uip` is not found at all, install it:

```bash
npm install -g @uipath/cli@latest
```

If `npm install -g` fails with a permission error, prompt the user to re-run with appropriate privileges — do not retry automatically.

### Command prefix

All commands in this skill are written as `uip flow ...`. The prefix is top-level — it is **not** nested under `uip maestro flow`. The older `uip maestro flow ...` form still resolves in the Node CLI as an alias, but the Studio Web embedded browser bundle ships only the top-level `flow` prefix, so writing `uip flow` is the only form that works in both environments.

## 2. Always use `--output json`

All `uip` commands support structured JSON output. Use `--output json` whenever output is parsed programmatically — every reference doc and recipe in this skill assumes it.

```bash
uip flow validate <ProjectName>.flow --output json
uip flow registry list --output json
uip flow instance incidents <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json
```

> **Anti-pattern: `--format json` does NOT exist.** The flag is `--output json`. Using `--format json` produces `error: unknown option '--format'` and exit code 3 on every `uip` subcommand — not a helpful message pointing at `--output`.

The `--localstorage-file` warning that appears in some environments is benign and can be ignored.

## 3. CLI output JSON shape

Every `uip` command returns one of two response shapes:

**Success:**
```json
{ "Result": "Success", "Code": "FlowValidate", "Data": { ... } }
```

**Failure:**
```json
{ "Result": "Failure", "Message": "...", "Instructions": "Found N error(s): ..." }
```

Always check `Result` first. On failure, `Message` and `Instructions` carry the diagnostic detail.

## 4. Login state

| Capability | Login required? |
|---|---|
| **Author** | No — `flow init`, `validate`, `tidy`, registry (OOTB nodes), `Edit` / `Write` edits, planning all work offline |
| **Operate** | **Yes** — `solution upload`, `solution resource refresh`, `flow debug`, `flow pack`, `process run`, `job status`, `job traces` all require `uip login` |
| **Diagnose** | **Yes** — `instance incidents`, `instance variables`, `instance asset`, `incident get`, `incident summary` all require `uip login` |

Tenant-specific connector and resource nodes in the registry also require login. Without login, registry shows OOTB nodes only. **In-solution sibling projects** are always available via `--local` without login.

Check login status:

```bash
uip login status --output json
```

Log in interactively (opens browser):

```bash
uip login
uip login --authority https://alpha.uipath.com    # non-production environments
```

## 5. `--folder-key` requirement

All `uip flow instance` and `uip flow incident get` commands require `--folder-key <FOLDER_KEY>` (`-f` shorthand). Without it, the command rejects the request before reaching the API.

Get the folder key:

```bash
uip or folders list --output json
```

Or pull it from the job/process context (e.g., `Data.folderKey` on a job status response, or from the debug output's surrounding metadata).

## 6. `UIPCLI_LOG_LEVEL=info` for debug runs

Set `UIPCLI_LOG_LEVEL=info` on `flow debug` invocations to surface progress and diagnostic detail in the CLI output. Without it, debug runs return only the final result.

```bash
UIPCLI_LOG_LEVEL=info uip flow debug <path-to-project-dir> --output json
```

The env var has no effect on other subcommands.

## 7. Global options

All `uip` commands support `--output json|yaml|table` and `--help`. Run any command with `--help` to discover all available options for that subcommand.

```bash
uip flow <subcommand> --help
```
