# Connections Guide

An Integration Service connection is one set of vendor credentials on a published connector. The BYO configuration points at a connection by id; the gateway reads it with its own service identity on every call.

## Test connection vs runtime connection

| | Test connection | Runtime connection |
|---|---|---|
| Purpose | Probe the connector while it is being built and fixed | Serve the product once the configuration is enabled |
| Credentials | A sandbox key, or the builder's own | The credentials production must use — ask the user |
| Folder | A shared folder (the gateway cannot read a Personal one) | The shared folder the configuration names in `--folder-key` |
| Lifetime | Delete when the runtime connection passes (ask first) | Kept; rotate with `edit` |

Use one connection for both only when the user says the same credentials serve production.

## Create

The connection page is keyed by the **published** connector key, `custom-<org>-<slug>` (`PublishedKey` in the `publish` output; `design-` swapped for `custom-`). The `design-…` key is rejected.

```bash
uip is connections create <PUBLISHED_KEY> --no-wait --output json
```

`Data.AuthUrl` is a page where the user enters the connection's fields (the ones with `configScreenType: "pre"`); `Data.ExpiresAt` bounds it. Hand the URL to the user and wait for them to say it is done. Never ask for the credentials in the chat or pass them on a command line, and do not open the page on their behalf with stored credentials.

Then locate it:

```bash
uip is connections list <PUBLISHED_KEY> --all-folders --refresh --output json
```

Take the new entry's `Id` (the `--connection-id` for the BYO configuration), and check `State` is `Enabled`.

## The Personal-folder trap

`uip is connections create` has no folder option; the connection lands in the default scope, which on most tenants is the creating user's **Personal workspace**. The gateway resolves BYO connections with its own service identity, which cannot read a Personal workspace, so a probe against such a connection reports it unavailable (`IntegrationServiceConfigurationNotFound`) even though `ping` succeeds for the user.

Check before probing:

```bash
uip or folders list --output json        # find the connection's FolderKey; its Type must not be Personal
```

If the connection is in a Personal workspace, ask the user to create it in the shared folder instead — from Integration Service in the web UI, with that folder selected — and continue with that connection's id. Use the same folder for `--folder-key` on the BYO configuration.

## Check that it works

```bash
uip is connections ping <CONNECTION_ID> --force-refresh --output json
```

`ping` proves the connection is enabled and, if the connector has a `provisionAuthValidation` resource, that the vendor accepted the credentials. It does not call the flavor's resource — only the probe does that.

## Rotate or fix credentials

```bash
uip is connections edit <CONNECTION_ID> --no-wait --output json    # returns an AuthUrl to re-enter the fields
```

After a rotation, re-run the probe with `byo-connections update <CONFIG_ID>` and the unchanged mapping.

## Delete

Deleting a connection breaks every BYO configuration that names it. List the configurations first and ask the user:

```bash
uip llm-configuration byo-connections list --include-connection-details --output json
uip is connections delete <CONNECTION_ID> --yes --output json     # only after the user agreed
```
