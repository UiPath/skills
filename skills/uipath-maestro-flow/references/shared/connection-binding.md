# Connection Binding — Shared Workflow

Reference for the common connection-fetch workflow used by connector activity, connector trigger, and managed HTTP nodes in connector mode. Plugin `impl.md` files link here for the standard list + ping + refresh recovery and the no-healthy-connection STOP block; each plugin documents its own divergences on top.

## Standard list + ping

```bash
# 1. List connections for the connector
uip is connections list "<connector-key>" --output json

# 2. Pick the default enabled connection (IsDefault: Yes, State: Enabled)

# 3. Verify health
uip is connections ping "<connection-id>" --output json
```

Add `--folder-key "<folder-key>"` to `connections list` when authoring a connector activity that must bind in a specific folder.

## Empty-list recovery

If `connections list` returns an empty array, retry once with `--refresh` to bypass the CLI cache:

```bash
uip is connections list "<connector-key>" --refresh --output json
```

## No-healthy-connection STOP

If `--refresh` still returns nothing, **STOP**. The node cannot be configured without a real connection ID. Present the path forward via `AskUserQuestion` (see the dropdown rule in [SKILL.md](../../SKILL.md)):

- **Create a new connection** — `uip is connections create "<connector-key>"` starts the OAuth flow; user completes browser auth, then re-run `connections list` to pick up the new connection.
- **Switch this node to manual mode** — applies to HTTP nodes only.
- **Skip this node** — leave it in the flow with empty `inputs`; document it as an open question for the user.
- **Something else** — free-form input.

Do not fall back silently, invent a placeholder ID, or skip the node without explicit user selection.

## Records to carry forward

From the chosen connection, capture:

- `Id` → `connectionId` in `--detail` and `inputs.detail`.
- `FolderKey` → `folderKey` in `--detail` (the CLI writes it back as `connectionFolderKey`).

These feed every subsequent `node configure --detail` call.

## Where plugins diverge

| Plugin | Extra steps |
|---|---|
| connector activity | Add `--folder-key` to `connections list`; the activity also needs `--connection-id` on `registry get` for enriched field metadata. |
| connector trigger | Two-stage flow — get any enabled connection first, query `triggers objects` to read the `byoaConnection` flag, then pick a final connection (BYOA if the flag is `true`). |
| HTTP (v2) | Connector mode only. Manual mode skips this entire workflow. |

For upstream Integration Service rules (default-connection preference, BYOA selection, multi-connection disambiguation, OAuth flow details), see the `uipath-platform` skill's `integration-service/connections.md`.
