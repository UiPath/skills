# Final Resolution

**Fault:** The `MainframeInquiry` job (folder Shared, host MOCK-HOST) ended **Faulted**. The fault is raised by a **`UiPath.Terminal.Activities.TerminalSession`** activity ("Mainframe Session") and surfaces as `System.AggregateException`.

**Root cause:** The Terminal Session **could not open its terminal connection**. Unwrapping the `System.AggregateException` reaches the real cause — `UiPath.Terminal.Data.TerminalConnectionException: There was an error connecting to terminal. Error code: UnknownError | ResultCode=UnknownError | ConnectionStatus=Disconnected` — thrown from `TerminalConnection.Start` during connection establishment. The fault happens at connection open, before any child screen-interaction activity runs. The configured terminal host/port is unreachable from the robot machine (the connect attempt could not establish a session within the timeout).

**Fix:** Make the terminal host reachable and the connection settings correct, then re-run:
- Verify the **host and port** in the Terminal Session's connection string are correct and that the host is **reachable from the robot machine** (firewall, DNS, VPN, port). This is the primary fix for `There was an error connecting to terminal`.
- Confirm the **provider/terminal type** matches the host, and that any required terminal emulator/provider runtime is installed on the robot.
- If the host is reachable but negotiation is slow, raise `TimeoutMS`.

**Must NOT attribute the root cause to:**
- `System.AggregateException` itself — it is only the async wrapper around the connect task; the inner `TerminalConnectionException` is the cause.
- A workflow-logic bug, a null variable, or the (empty) child activity body — the session never connected, so no child activity ran.
- A missing/disconnected `ExistingConnection` — this session opens a **new** connection via a connection string, not a reused one.
- A `System.NullReferenceException` — this fault is a connect failure, not the masked-NRE cleanup case.

A correct answer identifies the **terminal connection could not be established (unreachable host / connection settings), surfaced through TerminalSession as an AggregateException wrapping TerminalConnectionException**, and recommends fixing host reachability / connection settings. It must unwrap the aggregate rather than stopping at "one or more errors occurred."
