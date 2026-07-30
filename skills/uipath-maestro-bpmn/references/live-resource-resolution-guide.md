# Live resource resolution

Use this guide only when the user asks for a live, tenant-bound, or runnable
node, or supplies a concrete live resource that must be verified. A portable,
synthetic, local-only, or structural draft does not authorize tenant inventory.
`RequiresDiscovery` describes what a node needs to become runnable; it is not
permission to discover resources.

If the requested mode is unclear and live discovery would materially change the
result, ask before inventorying the tenant. In draft mode, preserve unresolved
placeholders, label the node non-runnable, and name the missing resource
contract. An unknown live adapter blocks a runnable claim, not the structural
draft.

## 1. Verify the active context

Run status before any tenant-dependent discovery:

```bash
uip login status --profile <name> --output json
```

The live examples below show a named profile deliberately. Omit `--profile`
only when the user selected the default CLI context instead.

Follow the [login boundary](cli-conventions.md#login-boundary). If the user
provided `--profile`, pass that same profile to status and every dependent
command. Profile selection is per command, not a session switch: a successful
`login status --profile <name>` does not make later commands inherit that
profile. Stop on a base URL, organization, or tenant mismatch; never silently
switch environments.

## 2. Select the adapter from the full contract

Retrieve the chosen node's full contract:

```bash
uip maestro bpmn registry get <extensionType> --profile <name> --output json
```

A flattened `registry list` row is only a screening view. Route from
`Data.ExtensionType.BindingInfo` and `BindingPattern` in the full response:

| Full-contract signal | Live discovery adapter |
| --- | --- |
| `RequiresDiscovery: false` / no live binding | No live lookup; the current template is sufficient. |
| `BindingInfo.Resource: process` | Authenticated registry `Data.Processes`. |
| `BindingInfo.Resource: queue` | Exact folder-scoped queue list when supplied; otherwise `uip or queues list --profile <name> --all-folders --output json`. |
| `BindingPattern: connection` (even when `BindingInfo` is null) | `uip is connections list <connector-key> --profile <name> --all-folders --output json`. |
| unrecognized live resource | Block the runnable claim; do not guess an adapter. |

Prefer `BindingInfo.Resource` when present. A specialized binding pattern can
still bind to a process. Connection-backed contracts can have
`BindingInfo: null`, so `BindingPattern: connection` is the authoritative
fallback for that adapter. Never route from a display label or a list-only
guess.

## 3. Resolve exact resource identity

Only candidates in a usable lifecycle state are viable. Preserve exact keys,
types, and folder identity; do not substitute a similarly named row.

### Process

Use authenticated registry `Data.Processes`. Match the requested process name,
the exact `Type` expected by the selected node, and any supplied folder. Names
can repeat across folders or versions, so do not collapse rows or exchange one
key field for another.

### Queue

Use an exact supplied folder directly:

```bash
uip or queues list --profile <name> --folder-path "<folder-path>" \
    --name <queue-name> --all-fields --output json
```

Use `--folder-key` when the exact key is supplied. If scope is unknown, search
exhaustively:

```bash
uip or queues list --profile <name> --all-folders --name <queue-name> \
    --output json
```

The server-side name filter is a contains match, so compare returned names
exactly. All-folder results can aggregate folder associations into
`FoldersCount`; a count greater than one is ambiguous until a folder is chosen.

### Connection

Take the connector key from registry discovery, never from a provider or product
label:

```bash
uip is connections list <connector-key> --profile <name> --all-folders \
    --output json
```

Accept only an exact `ConnectorKey` match in the `Enabled` state. Preserve the
connection id and folder identity. Disabled rows and enabled rows for another
connector are not fallbacks.

If several viable candidates remain and the user did not approve a deterministic
selection policy, ask which one to use. Never select the first row implicitly.

## 4. Refresh once, then stop

A missing selected id, an id absent from current discovery, or incomplete
required scope is stale or blocked evidence. Refresh only the affected source
once:

- process: `uip maestro bpmn registry pull --profile <name> --force --output
  json`, then `uip maestro bpmn registry list --profile <name> --limit -1
  --output json`;
- queue: repeat the affected `uip or queues list --profile <name> ... --output
  json` call (the queue command has no refresh flag); or
- connection: repeat `uip is connections list <connector-key> --profile <name>
  --all-folders --refresh --output json`.

A second failure remains blocked. Do not loop, use stale ids, or replace live
evidence with bundled data.

## 5. Preserve the binding boundary

For `BindingInfo.Resource: process` or `queue`, fill the context field named by
`BindingInfo.ContextField` with the selected resource's exact value at the
property named by `BindingInfo.PropertyAttribute`. Do not put the property-name
token itself into the context, guess a GUID, or reuse a resource from another
folder.

A connection id proves identity only. It does not prove an operation, object,
payload schema, output schema, or XML connection-binding shape. Those require
the retrieved enrichment contract; keep the node draft when that contract is
unavailable.

This workflow is read-only. Follow the
[side-effect boundary](cli-conventions.md#side-effect-boundary) before any
connection mutation or direct connector operation.
