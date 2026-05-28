# CLI Conventions

Shared conventions for the `uip` CLI that apply across **all three capabilities** (Author, Operate, Diagnose). Read this first when invoking any `uip` command — every capability assumes these mechanics.

## 1. Resolve the `uip` binary and detect command prefix

The `uip` CLI is installed via npm. Resolve the binary (it may not be on PATH in nvm environments) and detect the command namespace.

```bash
UIP=$(command -v uip 2>/dev/null || echo "$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip")
CURRENT=$($UIP --version 2>/dev/null | awk '{print $NF}')
```

If `uip` is not found at all, install it:

```bash
npm install -g @uipath/cli@latest
```

If `npm install -g` fails with a permission error, prompt the user to re-run with appropriate privileges — do not retry automatically.

### Command prefix by version

| Installed version | Command prefix | Example |
| --- | --- | --- |
| **≥ 0.3.4** | `uip maestro flow` | `uip maestro flow init MyProject` |
| **< 0.3.4** | `uip flow` | `uip flow init MyProject` <!-- uip-check-skip --> |

```bash
MIN_VERSION="0.3.4"
if [ "$(printf '%s\n%s\n' "$MIN_VERSION" "$CURRENT" | sort -V | head -n1)" = "$MIN_VERSION" ]; then
  FLOW_CMD="uip maestro flow"
else
  FLOW_CMD="uip flow" # <!-- uip-check-skip -->  legacy < 0.3.4 prefix
fi
echo "Using: $FLOW_CMD (CLI version $CURRENT)"
```

> **All commands across this skill are written as `uip maestro flow ...` (the ≥ 0.3.4 form).** If version detection above returns < 0.3.4, replace `uip maestro flow` with `uip flow`. Arguments and flags are identical — only the prefix differs. See UiPath/cli#841 for background on the restructuring. <!-- uip-check-skip -->

## 2. Always use `--output json`

All `uip` commands support structured JSON output. Use `--output json` whenever output is parsed programmatically — every reference doc and recipe in this skill assumes it.

```bash
uip maestro flow validate <ProjectName>.flow --output json
uip maestro flow registry list --output json
uip maestro flow instance incidents <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json
```

> **Anti-pattern: `--format json` does NOT exist.** The flag is `--output json`. Using `--format json` produces `error: unknown option '--format'` and exit code 3 on every `uip` subcommand — not a helpful message pointing at `--output`.

The `--localstorage-file` warning that appears in some environments is benign and can be ignored.

## 3. Prefer `--output-filter` for extraction

When extracting one field or a projection from `uip --output json`, use `--output-filter '<jmespath>'`. The CLI exposes `--output-filter <expression>` as a global flag on every subcommand; it applies a [JMESPath](https://jmespath.org/) expression to the `Data` envelope **before** printing. Write expressions starting at `Data` — do **not** prefix them with `Data.`.

**Canonical example (broad discovery)** — list all nodes matching a keyword with the standard projection:

```bash
uip maestro flow registry search slack --output json \
  --output-filter "[*].{NodeType:NodeType,DisplayName:DisplayName,Description:Description,AvailableOnTenant:AvailableOnTenant}"
```

This is the form used in the connector skill — see [Cross-references](#cross-references) below — and is the right starting point when you want to inspect what's available.

**Narrow query** — once you know the connector namespace, filter to a single connector's activities:

```bash
uip maestro flow registry search slack --output json \
  --output-filter "[?starts_with(NodeType,'uipath.connector.uipath-salesforce-slack.')].{NodeType:NodeType,DisplayName:DisplayName}"
```

`registry search` returns `Data` as a **flat array of PascalCase objects** — `NodeType`, `Category`, `DisplayName`, `Description`, `Version`, `Tags`, `AvailableOnTenant`. Not `Data.Nodes`, not lowercase `type`/`category`; those shapes do not exist. Pinning the shape inside `--output-filter` makes a shape-mismatch fail loudly with a non-zero exit on call #1, rather than silently returning `[]` and prompting a retry loop.

### When to fall back to `python3` / `jq`

`--output-filter` is the preferred extraction mechanism, but it is not a general-purpose transformation tool. Fall back to `python3 -c` or `jq` when JMESPath cannot express the operation:

- Multi-step joins across two CLI calls.
- Format conversion (JSON → CSV, JSON → env-var assignments).
- Conditional output that depends on a value computed from multiple fields.

Before reaching for an external parser, verify the JSON shape — either by running the command once without filtering and inspecting the raw output, or with `--output-filter "keys(@)"` to list top-level keys at `Data`. Most agent-side retry loops on `uip --output json` parsing come from guessing the shape wrong; verify, then parse.

### Cross-references

The broad-discovery recipe above is used in [author/references/plugins/connector/planning.md](../author/references/plugins/connector/planning.md) (§ Discovery) for connector discovery and [author/references/plugins/connector/impl.md](../author/references/plugins/connector/impl.md) for connection-resource lookup. Keep the three in sync on the **preference** (always `--output-filter`) and the **shape pin** (`registry search` Data is a flat array of PascalCase objects); each file may pick a projection appropriate to its task.

## 4. CLI output JSON shape

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

## 5. Login state

| Capability | Login required? |
|---|---|
| **Author** | No — `flow init`, `validate`, `format`, registry (OOTB nodes), `Edit` / `Write` edits, planning all work offline |
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

## 6. `--folder-key` requirement

All `uip maestro flow instance` and `uip maestro flow incident get` commands require `--folder-key <FOLDER_KEY>` (`-f` shorthand). Without it, the command rejects the request before reaching the API.

Get the folder key:

```bash
uip or folders list --output json
```

Or pull it from the job/process context (e.g., `Data.folderKey` on a job status response, or from the debug output's surrounding metadata).

## 7. `UIPCLI_LOG_LEVEL=info` for debug runs

Set `UIPCLI_LOG_LEVEL=info` on `flow debug` invocations to surface progress and diagnostic detail in the CLI output. Without it, debug runs return only the final result.

```bash
UIPCLI_LOG_LEVEL=info uip maestro flow debug <path-to-project-dir> --output json
```

The env var has no effect on other subcommands.

## 8. Global options

All `uip` commands support `--output json|yaml|table` and `--help`. Run any command with `--help` to discover all available options for that subcommand.

```bash
uip maestro flow <subcommand> --help
```
