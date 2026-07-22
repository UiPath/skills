# IPC Activities Presentation Rules

- **Activities** — use the display name (e.g., "Broadcast Message", "Send Message", "Message Receiver Trigger"), not the fully qualified class name (e.g., `UiPath.IPC.Activities.BroadcastMessage`)
- **Channels** — quote the `Channel` string exactly as configured, in backticks, and flag case sensitivity when a mismatch is suspected (e.g. "sender channel `OrderBus` vs receiver channel `orderbus`")
- **Sender / receiver** — always name which side you mean: the **sender** (the process holding `Broadcast Message` / `Send Message`) and the **receiver** (the process holding the `Message Receiver Trigger`). Never say just "the process" when both are in play
- **Exceptions** — quote the exact exception class and message together (e.g. "`System.TimeoutException`: `Timeout of 3000 ms has passed and no channel was found to send the message to.`"), and state which layer it maps to (no-receiver-in-time vs pipe-ACL-denied)
- **Timeout** — refer to the `Timeout` property in milliseconds and state the practical floor (5000–10000 ms) when recommending a raise; call out `Timeout = 0` explicitly as the silent-drop setting
- **Run surface** — name the session/user in the user's terms (e.g. "attended user session", "unattended robot (Session 0)", "elevated / Run as administrator") so the user can check the boundary, not internal runtime flags
- **Launch mechanism** — name the concrete mechanism the user configures (e.g. "`Run Parallel Process`", "a background job started before the broadcast"), not an abstract "run it in parallel"
