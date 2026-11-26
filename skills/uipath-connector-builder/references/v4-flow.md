# Community Route (Flow only)

Preview CLI only. Activities run a script instead of `element.json` rows and hooks.
Auth, configuration, system resources and the icon work as on the legacy route.

## What changes

| | Legacy | Community |
|---|---|---|
| Activity metadata | `standard-resources/<name>.json` | `v4/objects/<name>/metadata.json` |
| Activity list | `curated` block in the SR | `v4/activities.json` |
| Vendor call | `element.json` row + hooks | `v4/scripts/<name>.js` |
| Pagination, renames, reshaping | options and hooks | the script |
| Triggers | `trigger create` | not supported |

All paths are under `app/element/`.

## Workflow

Scripts first, then link. `activity create` fails if a method has no script or the file is missing.

```bash
# 1. Scaffold. --v4 marks the connector (flags.v4Compatible). The key is
#    design-{org}-{name}, the same as on the legacy route.
uip is connectors builder init --name '<CONNECTOR_NAME>' --v4 \
  --base-url <BASE_URL> --auth <AUTH_TYPE>

# 2. Write every script: one per method, one per lookup. Contract: scripts.md.
#    app/element/v4/scripts/listContacts.js
#    app/element/v4/scripts/getContact.js
#    app/element/v4/scripts/createContact.js
#    app/element/v4/scripts/listUsers.js        (lookup)

# 3. Link each method to its script, with the field schema.
uip is connectors builder activity create --name contacts --vendor-path /v1/contacts \
  --methods GET,GETBYID,POST --primary-key id --fields-file ./contacts-fields.json \
  --method-script-ref GET=listContacts \
  --method-script-ref GETBYID=getContact \
  --method-script-ref POST=createContact

# 4. Check what was written, then validate.
uip is connectors builder inspect --output json
uip is connectors builder validate
```

Then import and publish as in SKILL.md. The connector publishes to your tenant as `custom-{org}-{name}`.
To offer it in the community catalog afterwards, follow [community-submit-guide.md](community-submit-guide.md).

## Rules

1. **Every method needs `--method-script-ref METHOD=<SCRIPT_NAME>`**, and the script file must exist.
2. **A lookup is a `scriptRef`** ([scripts.md §Lookups](scripts.md#lookups)). In `--fields-file`:
   ```json
   { "name": "ownerId", "type": "string",
     "reference": { "scriptRef": "listUsers", "lookupValue": "id", "lookupNames": ["name"] } }
   ```
   Or on an existing field or parameter:
   ```bash
   uip is connectors builder activity field create --resource contacts --name ownerId \
     --reference '{"scriptRef":"listUsers"}' --lookup-value id --lookup-names name
   ```
   `--reference-object` and `--reference-path` are legacy only.
3. **Parameters are `query` or `multipart`.** A path value (`{id}`) is a `query` input; the script sends it the way the vendor accepts it (for `/contacts/{id}`, in the URL). Headers, body shaping and constants go in the script.
4. **`--has-ceql` adds a `where` query input.** The script must apply it.
5. **Hooks attach only to system resources** (`auth system create`). No hook on an activity, no `--global` hook.
6. **`validate` does not check `v4/` files yet.** Use `inspect` (the `V4` block) and `activity script get <SCRIPT_NAME>` to confirm every script is linked.

## Options that do nothing here

`activity create` warns and ignores: `--pagination-type`, `--root-key`, `--next-page-key`,
`--page-size-param`, `--offset-param`, `--filter-param`, `--resource-path`, `--next-resource`,
`--no-body`, `--resource-type`, `--skip-sr`, `--no-curate`, `--has-events`, `--has-bulk`.

## Commands

| Task | Command |
|---|---|
| List / read an activity | `activity list`, `activity get <NAME>` or `activity get <METHOD>:<NAME>` |
| Fields, parameters, method | `activity field …`, `activity param …`, `activity method get\|set` — same as legacy |
| Rename the Studio activity | `activity method curate --resource <NAME> --method <METHOD> --display-name '<TEXT>'` |
| List scripts / see what uses one | `activity script list`, `activity script get <SCRIPT_NAME>` |
| Delete an unused script | `activity script delete <SCRIPT_NAME>` — fails while a `scriptRef` names it |
| Remove one method | `state patch v4/objects/<NAME>/metadata/method/<METHOD> --op remove` — also deletes its script if nothing else names it |
| Remove an activity | `activity delete <NAME>` — also deletes its scripts that nothing else names |
| Read or write a slice | `state query\|patch v4/objects/<NAME>/…`, `v4/scripts/<FILE>` |

By-id methods are keyed `GETBYID` here, not `GET`.

Scripts are hand-written. Copy a script before removing its method or activity if it will be re-created: `activity create` fails on a missing script file.

## Anti-patterns

1. Running `activity create` before the scripts exist.
2. Writing a hook for an activity. Put the logic in its script.
3. Expecting `--root-key` or `--pagination-type` to shape a list. The script returns the array and pages.
4. Passing `--reference-object`/`--reference-path` for a lookup.
5. Reporting done on `validate` alone. It does not read `v4/`.
