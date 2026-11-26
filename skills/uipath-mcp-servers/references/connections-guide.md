# Creating a Connection

Detail behind `--connection-id` on [`remote` servers](../SKILL.md#server-types) and [Per-User Connections](../SKILL.md#per-user-connections). A `remote` server's connection is an OAuth connection of the UiPath MCP connector, `uipath-uipath-mcp`. When the user has none to use, create one with them.

Ask the user first: it opens their browser and signs them in to the server's provider. Then:

1. Tell them what the page asks for, so they have it ready: the authentication type, **OAuth 2.0 Authorization code**, or **OAuth 2.0 Authorization code with PKCE** for an OAuth app with no client secret; the server's URL as **Base URL**; and the OAuth app's **Client ID**, **Client secret**, **Authorization URL**, **Token URL** and **Scope**, from the provider. The app must allow the callback URL the page shows (`https://cloud.uipath.com/provisioning_/callback` on Automation Cloud), and it must issue refresh tokens ([Checking a Server](../SKILL.md#checking-a-server)). They type these on the page: never ask for the client secret in the chat, and never fill the page in yourself.
2. Run `uip --interactive is connections create uipath-uipath-mcp --folder-path <FOLDER_PATH> --output json` with a command timeout of at least 6 minutes. It opens the page in the browser, with the folder already chosen, and waits up to 5 minutes for the user to finish. Then it answers `Code: ConnectionCreated`, with `Data.ConnectionId` and `Data.State: Enabled`: pass that id as `--connection-id`, or to `mcp-user-connections set`.
   - `--folder-path` is the server's folder, for the server's connection. Leave it out for a user's own per-user connection: it then goes to their Personal Workspace.
   - Without `--interactive`, a run from an agent's shell opens nothing and answers `Status: AuthorizationPending` with an `AuthUrl`.
3. When the shell cannot wait 6 minutes, pass `--no-wait` instead. Open the `AuthUrl` it answers in the user's browser (`open '<AUTH_URL>'` on macOS, `xdg-open '<AUTH_URL>'` on Linux, `powershell.exe -NoProfile -Command "Start-Process '<AUTH_URL>'"` on Windows) and wait for them to say it is done: the page expires about 12 minutes after it opens. Then find the connection with `uip is connections list <CONNECTOR_KEY> --folder-path <FOLDER_PATH> --refresh --output json`, with `<CONNECTOR_KEY>` `uipath-uipath-mcp`: the newest `Enabled` one.

Then `refresh-tools` checks the server with the new connection (Rule 7).
