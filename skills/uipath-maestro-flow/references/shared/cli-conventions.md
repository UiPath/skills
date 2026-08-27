# CLI Conventions

Shared conventions for the `uip` CLI across Author, Operate, and Diagnose. Read this before invoking any `uip` command.

## 1. Resolve `uip` and detect the command prefix

Resolve the npm-installed binary, which may be absent from PATH in nvm environments:

```bash
UIP=$(command -v uip 2>/dev/null || echo "$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip")
CURRENT=$($UIP --version 2>/dev/null | awk '{print $NF}')
```

If `uip` is not found, run:

```bash
npm install -g @uipath/cli@latest
```

If global installation fails with a permission error, prompt the user to rerun it with appropriate privileges; do not retry automatically.

Use `uip maestro flow` for CLI version **≥ 0.3.4** and `uip flow` for versions **< 0.3.4**:

```bash
MIN_VERSION="0.3.4"
if [ "$(printf '%s\n%s\n' "$MIN_VERSION" "$CURRENT" | sort -V | head -n1)" = "$MIN_VERSION" ]; then
  FLOW_CMD="uip maestro flow"
else
  FLOW_CMD="uip flow" # <!-- uip-check-skip -->  legacy < 0.3.4 prefix
fi
echo "Using: $FLOW_CMD (CLI version $CURRENT)"
```

Run all commands below with `uip maestro flow ...`; if detection returns < 0.3.4, replace only that prefix with `uip flow`. Arguments and flags are identical. See UiPath/cli#841. <!-- uip-check-skip -->

## 2. Use JSON output

Run programmatically parsed commands with `--output json`:

```bash
uip maestro flow validate <ProjectName>.flow --output json
uip maestro flow registry list --output json
uip maestro flow instance incidents <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json
```

Do not use `--format json`; it does not exist and produces `error: unknown option '--format'` with exit code 3 on every `uip` subcommand. Ignore the benign `--localstorage-file` warning when it appears.

## 3. Extract with `--output-filter`

Prefer `--output-filter '<jmespath>'` for field or projection extraction. It is a global flag on every subcommand, applies to the `Data` envelope before printing, and expressions start at `Data` (never `Data.`).

Run broad discovery with:

```bash
uip maestro flow registry search slack --output json \
  --output-filter "[*].{NodeType:NodeType,DisplayName:DisplayName,Description:Description,AvailableOnTenant:AvailableOnTenant}"
```

Run a narrowed connector query with:

```bash
uip maestro flow registry search slack --output json \
  --output-filter "[?starts_with(NodeType,'uipath.connector.uipath-salesforce-slack.')].{NodeType:NodeType,DisplayName:DisplayName}"
```

Treat `registry search` as returning `Data` as a flat array of PascalCase objects: `NodeType`, `Category`, `DisplayName`, `Description`, `Version`, `Tags`, `AvailableOnTenant`. It does not return `Data.Nodes` or lowercase `type`/`category`.

Do not use `head`, `tail`, `grep -m`, or a pager on discovery queries (`registry search`, `is connectors list`, or any `list`/`search`). Test existence with a predicate in `--output-filter` and return all matches:

```bash
uip … registry search slack --output json --output-filter "[?contains(NodeType,'get-channel-info')].NodeType"   # right: every match
uip … registry search slack --output json --output-filter "[*].{…}" | head -100                                # wrong: hides matches past line 100
```

Treat `Data: []` with exit 0 as a valid but mismatched expression, not proof of absence. Only invalid syntax or type errors fail with exit 3.

Use `python3 -c` or `jq` only when JMESPath cannot perform a multi-step join across CLI calls, JSON-to-CSV or JSON-to-env-var conversion, or conditional output based on multiple fields. Verify the shape first:

- Run `--output-filter "type(@)"`; it returns `"array"` or `"object"`.
- For an object, run `--output-filter "keys(@)"`.
- For an array, run `--output-filter "[0]"` or `--output-filter "[0] | keys(@)"`.
- Do not run `keys(@)` directly on an array; it fails with `Filter 'keys(@)' failed to evaluate: Invalid type: keys() expected argument 1 to be of type (object) but received type array instead`.
- If an expected value is `Data: []`, check field-name casing.

`registry search` and `list` (and most `uip … --output json` commands) use PascalCase keys such as `[*].NodeType` and `[*].DisplayName`. `registry get` returns the node definition verbatim for pasting into `.flow`; its keys are predominantly camelCase: `Node.nodeType`, `Node.inputDefinition`, `Node.supportsErrorHandling`, and `Node.form.sections[…]`. Some nested runtime-output schemas are PascalCase, such as Summarize's `content.Text` and `content.Citations`. Match the manifest rather than assuming normalized casing. When uncertain, probe with `--output-filter "keys(@)"` for objects or `--output-filter "[0] | keys(@)"` for arrays.

Verify the shape before parsing; most parsing retries result from an incorrect shape guess.

### Cross-references

Keep the broad-discovery recipe aligned with [author/references/plugins/connector/planning.md](../author/references/plugins/connector/planning.md) (§ Discovery) for connector discovery and [author/references/plugins/connector/impl.md](../author/references/plugins/connector/impl.md) for connection-resource lookup. Both files use the `--output-filter` preference and the `registry search` flat-array/PascalCase shape; each may use a task-specific projection.

## 4. Check the JSON response shape

Every `uip` command returns one of these shapes:

```json
{ "Result": "Success", "Code": "FlowValidate", "Data": { ... } }
```

```json
{ "Result": "Failure", "Message": "...", "Instructions": "Found N error(s): ..." }
```

Always check `Result` first. On failure, use `Message` and `Instructions` for diagnostics.

## 5. Login state

| Capability | Login required? |
|---|---|
<!--skill-flavor:flow-init-login-scope:start-->
| **Author** | No — `flow init`, `validate`, `format`, registry (OOTB nodes), `Edit` / `Write` edits, planning all work offline |
<!--skill-flavor:flow-init-login-scope:end-->
| **Operate** | **Yes** — `solution upload`, `solution resources refresh`, `flow debug`, `flow pack`, `process run`, `job status`, `job traces` all require `uip login` |
| **Diagnose** | **Yes** — `instance incidents`, `instance variables`, `instance asset`, `incident get`, `incident summary` all require `uip login` |

Tenant-specific connector and resource nodes require login; without it, the registry shows OOTB nodes only. In-solution sibling projects are always available with `--local` without login.

Check login by running:

```bash
uip login status --output json
```

Log in interactively by running:

```bash
uip login
uip login --authority https://alpha.uipath.com    # non-production environments
```

## 6. Supply `--folder-key`

Run all `uip maestro flow instance` and `uip maestro flow incident get` commands with `--folder-key <FOLDER_KEY>` (or `-f`). Without it, the request is rejected before reaching the API.

Get the folder key by running:

```bash
uip or folders list --output json
```

Alternatively obtain it from job/process context, such as `Data.folderKey` in a job-status response or surrounding debug metadata.

## 7. Use `UIP_LOG_LEVEL=info` for debug runs

Run debug with `UIP_LOG_LEVEL=info`:

```bash
UIP_LOG_LEVEL=info uip maestro flow debug <path-to-project-dir> --output json
```

Capture stderr as well as stdout. At `info`, stderr reports the `jobKey`, `instanceId`, and Studio Web URL. If polling exceeds its budget, stdout may contain only `Debug polling timed out after <N>s`; stderr is then the only way to identify the instance and inspect it with `uip maestro flow debug-instance incidents <instanceId>`.

Use `UIP_LOG_LEVEL`, not `UIPCLI_LOG_LEVEL`; the latter is silently ignored. `--log-level <level>` is the equivalent global flag. The setting applies to every `uip` command.

## 8. Global options

Run `uip maestro flow <subcommand> --help` to discover subcommand options. All `uip` commands support `--output json|yaml|table` and `--help`.