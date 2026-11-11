# Connections Guide

An Integration Service connection is one set of vendor credentials on a connector. The BYO configuration points at a connection by id; the gateway reads it with its own service identity on every call.

## Test connection vs runtime connection

| | Test connection | Runtime connection |
|---|---|---|
| Purpose | Call the unpublished draft through Integration Service while it is being built and fixed (custom-connector-guide.md step 7) | Run the product's probes when the configuration is saved, then serve the product once it is enabled |
| Made with | `curl` on the Integration Service API — the Connector Builder's Add connection (custom-connector-guide.md step 6) | The Connections API with the folder in a header (below), its page opened in the user's browser — or the Integration Service web UI, on the published connector |
| Connector | The draft (`design-…`); runs whatever was last imported | The published `custom-…` key; runs the latest published version — each publish reaches it at once, with no edit |
| Credentials | A sandbox key, or the builder's own | The credentials production must use — ask the user |
| Who sees it | Only its creator; `uip is connections` never lists it, so no configuration can be saved on it | The shared folder the configuration names in `--folder-key`, so other admins can manage it |
| Lifetime | Delete when the runtime connection passes (ask first) | Kept; rotate with `edit` |

Use one set of credentials for both only when the user says the same credentials serve production.

## Create the test connection

custom-connector-guide.md step 6 has the calls: the `<WORK_DIR>/is-api.sh` helper, then open a session, finish it or open its page in the user's browser, and list. They are the requests the Connector Builder sends when you press Add connection:

| Call | Request |
|---|---|
| The draft's key and element id | `GET elements_/v3/element/connectors/<CONNECTOR_ID>` → `key`, `sobaId` (`<CONNECTOR_ID>` is `Data.Id` from `import`) |
| Your Personal workspace | `GET orchestrator_/odata/PersonalWorkspaces/UiPath.Server.Configuration.OData.GetPersonalWorkspace` → `Key`, `Name` |
| Open a session | `POST elements_/v1/elements/normalized-instances/applications/default/sessions` → `sessionID`, `redirectUrl` (the authorization page), `expiration` |
| Read it | `GET elements_/v1/elements/normalized-instances/applications/sessions/<SESSION_ID>` → `elementMetadata` (its `authentication` and `configuration`), `configs`, `headers.folderKey` |
| Finish it, when it asks nothing | `POST elements_/v1/elements/normalized-instances/authenticate` with the folder headers → `elementInstance` |
| List your connections on the draft | `GET elements_/elements/api-v2/elements/<ELEMENT_ID>/instances` |

Every call carries `x-uipath-source: UiPath.IntegrationService.ConnectorBuilder`, under `<BaseUrl>/<OrganizationId>/<TenantName>/` from `uip login refresh`.

- A session asks for something when the connector has authentication or a connection field the page shows (`configScreenType` `"pre"` or `"pre-optional"`). Open `authUrl` in the user's own browser (custom-connector-guide.md step 6 has the command per OS) and wait for them to say it is done. Never ask for the credentials in the chat or pass them on a command line, never complete that session with `authenticate`, and never fill in the page yourself, with stored credentials or any others. The finished connection carries the `connectionId` you chose; the page names it.
- A session is spent once a connection is made from it, and expires at `expiresAt`: reading it then answers `404` "Session expired" — open a new one.

What the calls answer when something is wrong:

| Answer | Meaning | Fix |
|---|---|---|
| `404` "Connector not found" on the connector record | Wrong `<CONNECTOR_ID>` | Use `Data.Id` from the last `import` |
| `400` "Element key is missing or invalid" on the session | The session body has no `elementKey` | Check the connector record call succeeded |
| `404` "No element instances found" on the list | You have no connection on this draft yet | Open a session |
| `404` "Session expired" | The session was spent or timed out | Open a new session |
| `401` | The token expired between calls | Run the call again: the helper reads a fresh one; if `uip login refresh` fails, ask the user to run `uip login` |
| "Argument list too long" | A whole connector record was passed as an argument | Keep the `jq -c '{key, elementId: .sobaId}'` projection |
| `404` "No API found at that URL for the given token and credentials" on a step 7 call | The connector has no resource at that path | Use the flavor's path ([connector-contract-guide.md](connector-contract-guide.md)); `builder inspect` lists the resources |
| `404` "Invalid Element Instance Id provided." on a step 7 call | The test connection was deleted | Create it again |
| On the connection page: "Failed to authenticate with `<connector>` during provisioning", naming `Validation API: GET <vendor path>` and the vendor's status | The `provisionAuthValidation` call failed. Beside a custom token exchange it runs before `onProvision`, so the vendor saw no token (custom-connector-guide.md Rule 13) | Token exchange: remove `provisionAuthValidation`, re-import, open a new session. Otherwise: the key, the header name or its prefix is wrong |
| `400` "Failed to execute API with `<connector>` during provisioning" on a step 7 call, `providerMessage` starting `POST <token URL>\|<status>\|` | The token's lifetime had passed and the refresh (`onRefresh`) failed before the call; what follows the URL is the token service's status and reason ("is not reachable or invalid": the host is down or wrong) | Fix what the token service answers — its host, or credentials that changed (then create the connection again); the call itself never left Integration Service |
| The user connected, yet no call reached the vendor's token endpoint and every call answers `401` | Integration Service never ran the exchange: `onProvision` is not `GET /onProvision` | Patch it (custom-connector-guide.md Rule 13), re-import, create the connection again |

Because it belongs to the draft, a re-import changes what the test connection runs: fix a hook, `import`, call it again. Nothing is published until step 8. The test connection is not in the connections catalog, so `uip is connections ping` cannot check it and no configuration can be saved on it — the step 7 calls are its test.

To change the test connection's credentials, create a new one and delete the old.

## Create the runtime connection

After `publish` (`Data.PublishedKey`, `design-` swapped for `custom-`), the runtime connection is made on the published connector, in the shared folder the product will use. `uip is connections create <PUBLISHED_KEY>` has no folder option: it puts the connection in the creator's **Personal** workspace, where the gateway can still use it but only its creator can see, edit or rotate it. With the `design-…` key, `uip is connections create` fails.

Open the connection session yourself with the call `uip is connections create` makes, plus the folder header the Connections API reads, and open its `authUrl` in the user's browser exactly as for the test connection (they enter the credentials; you never do):

```bash
uip or folders list --output json                                   # Key of the shared folder (Type Standard)
( set -o pipefail; source <WORK_DIR>/is-api.sh &&
  api "$T/connections_/api/v1/Connections" -H 'x-uipath-folderkey: <SHARED_FOLDER_KEY>' \
    --data-raw '{"connector":"<PUBLISHED_KEY>"}' | jq '{sessionId, authUrl, expiresAt}'
)
```

`expiresAt` is in epoch milliseconds. Once the user has connected, the list below shows the connection with that `FolderKey`; if it shows the Personal workspace instead, the header was not applied — have the user create it from Integration Service in the web UI, on the published connector, in the shared folder.

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
uip is connections delete <CONNECTION_ID> --yes --output json                     # runtime connection
```

A test connection is deleted by its `instanceId` (the list in custom-connector-guide.md step 6 maps `connectionId` to it):

```bash
( set -o pipefail; source <WORK_DIR>/is-api.sh &&
  api -X DELETE "$T/elements_/elements/api-v2/elements/<ELEMENT_ID>/instances/<INSTANCE_ID>" && echo deleted
)
```

A call on a deleted test connection answers `404` "Invalid Element Instance Id provided.".
