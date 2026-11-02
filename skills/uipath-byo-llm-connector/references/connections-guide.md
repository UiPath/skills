# Connections Guide

An Integration Service connection is one set of vendor credentials on a connector. The BYO configuration points at a connection by id; the gateway reads it with its own service identity on every call.

## Test connection vs runtime connection

| | Test connection | Runtime connection |
|---|---|---|
| Purpose | Probe the connector while it is being built and fixed | Serve the product once the configuration is enabled |
| Made with | `uip is connectors test-connection create` — the Connector Builder's Add connection | The Integration Service web UI, on the published connector |
| Connector | The draft (`design-…`); runs whatever was last imported | The published `custom-…` key; runs the published version |
| Credentials | A sandbox key, or the builder's own | The credentials production must use — ask the user |
| Who sees it | Only its creator; `uip is connections` never lists it | The shared folder the configuration names in `--folder-key`, so other admins can manage it |
| Lifetime | Delete when the runtime connection passes (ask first) | Kept; rotate with `edit` |

Use one set of credentials for both only when the user says the same credentials serve production.

## Create the test connection

```bash
uip is connectors test-connection create --connector-dir <CONNECTOR_DIR> \
  --name '<CONNECTOR_NAME> test' --no-wait --output json
```

The connector must be imported first; the command finds it on the tenant by the `key` in `element.json` (`connectorNotFoundOnTenant` means it was not imported).

- A connector without authentication is connected straight away: `Code: "TestConnectionCreated"`, `Data.ConnectionId`.
- Any other returns `Code: "TestConnectionAuthorizationPending"` with `Data.AuthUrl` — a page where the user enters the connection's fields (the ones with `configScreenType: "pre"`); `Data.ExpiresAt` bounds it. Hand the URL to the user and wait for them to say it is done. Never ask for the credentials in the chat or pass them on a command line, and do not open the page on their behalf with stored credentials. `Data.ConnectionId` is the id the finished connection will carry.

```bash
uip is connectors test-connection list --connector-dir <CONNECTOR_DIR> --output json
```

`Data.Connections[]` lists your test connections on the draft (`ConnectionId`, `InstanceId`, `Name`, `CreatedDate`); use the `ConnectionId` as `--connection-id` on the BYO configuration.

Because it belongs to the draft, a re-import changes what the test connection runs: fix a hook, `import`, re-probe. Nothing is published until step 8. The test connection is not in the connections catalog, so `uip is connections ping` cannot check it — the probe is its test.

To change the test connection's credentials, create a new one and delete the old.

## Create the runtime connection

After `publish` (`Data.PublishedKey`, `design-` swapped for `custom-`), the user creates the runtime connection from Integration Service in the web UI, on the published connector, in the shared folder the product will use. `uip is connections create <PUBLISHED_KEY>` has no folder option: it puts the connection in the creator's **Personal** workspace, where the gateway can still use it but only its creator can see, edit or rotate it. With the `design-…` key, `uip is connections create` fails.

Then locate it:

```bash
uip is connections list <PUBLISHED_KEY> --all-folders --refresh --output json
uip or folders list --output json        # the connection's FolderKey: Type Personal or Standard
```

Take the entry's `Id` (the `--connection-id` for the BYO configuration), check `State` is `Enabled`, and use the same folder for `--folder-key` on the configuration.

## Check the runtime connection

```bash
uip is connections ping <CONNECTION_ID> --force-refresh --output json
```

`ping` proves the connection is enabled and, if the connector has a `provisionAuthValidation` resource, that the vendor accepted the credentials. It does not call the flavor's resource — only the probe does that.

## Rotate or fix runtime credentials

```bash
uip is connections edit <CONNECTION_ID> --no-wait --output json    # returns an AuthUrl to re-enter the fields
```

After a rotation, re-run the probe with `byo-connections update <CONFIG_ID>` and the unchanged mapping.

## Delete

Deleting a connection breaks every BYO configuration that names it. List the configurations first and ask the user:

```bash
uip llm-configuration byo-connections list --include-connection-details --output json
uip is connectors test-connection delete <CONNECTION_ID> --connector-dir <CONNECTOR_DIR> --yes --output json   # test connection
uip is connections delete <CONNECTION_ID> --yes --output json                                                  # runtime connection
```
