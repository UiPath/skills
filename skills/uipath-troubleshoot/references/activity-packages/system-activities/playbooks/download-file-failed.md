---
confidence: medium
---

# Download File / Wait for Download Failed

## Context

A `Download File from URL` activity, or the `Wait for Download` / `Get Latest Downloaded File` helper (`UiPath.System.Activities`), faulted while fetching a file over HTTP or while waiting for a browser-initiated download to land. Route on the message text.

What this looks like:
- A raw `System.Net.Http.HttpRequestException`, often wrapping a `System.Net.Sockets.SocketException` — `Download File from URL`: the HTTP GET failed at the transport layer. The message carries the underlying cause, e.g. a DNS/name-resolution failure (`The requested name is valid, but no data of the requested type was found. (<host>:443)`), connection refused, or a TLS error. (Some package builds wrap this as `Failed to execute rest call.`)
- `The server didn't respond within the specified timeout value of <n> second(s)` (`TimeoutException`) — `Download File from URL`: the server accepted the connection but did not respond in time.
- `No file detected in <folder> during the timeout period (<n> seconds). Increase the timeout if the file takes longer to download or check if the Downloads folder is correct.` — `Wait for Download`: no new file appeared in the watched folder within the timeout.
- `The <file> was found but it's in use.` — `Wait for Download`: the file appeared but is still locked (download in progress, or an antivirus scan holding it open).

What can cause it:
- URL is wrong, expired, requires authentication, or returns a non-2xx status.
- Proxy, firewall, or TLS-inspection on the robot host blocks the endpoint, or the server is slow/overloaded.
- The watched folder is not the browser's actual download directory, or the action that should trigger the download never fired (or was blocked by a browser "save as" / security prompt).
- The file is still being written or is locked by antivirus when the workflow tries to consume it.

What to look for:
- The message plus the resolved URL, watched folder path, and timeout value the activity used at run time.
- Whether the URL is reachable (and returns the file) from the robot host, not just the developer machine.
- Whether a download actually started, and where the browser writes downloads on the robot.

## Investigation

1. Capture the message and the resolved URL / watched folder / timeout.
2. For the transport `HttpRequestException` or the response-timeout: test the URL from the robot host — reachability, required auth/headers, response status, and any proxy/TLS interception. The inner `SocketException` text names the transport cause (DNS, connection refused, TLS).
3. For `No file detected` / `found but it's in use`: confirm the watched folder is the browser's real download directory on the robot, and that the upstream action triggers the download without a blocking prompt.

## Resolution

### Transport failure — `HttpRequestException` (DNS / connection / TLS)
Verify the URL is correct and its host resolves and is reachable from the robot host (the inner `SocketException` names the cause — DNS, connection refused, TLS); add the required authentication/headers if the endpoint needs them; allow the host through proxy / firewall / TLS inspection. Check the HTTP status the server returned — this is a transport/endpoint fix, not a workflow retry.

### `The server didn't respond within the specified timeout ...`
If the server is legitimately slow, raise the activity timeout; otherwise address the server-side latency or the hung endpoint. Do not raise the timeout to mask a wrong URL or an auth rejection (those surface as the rest-call error, not a timeout).

### `No file detected in <folder> ...`
Point the activity at the browser's actual Downloads folder on the robot; ensure the upstream step reliably triggers the download and no "save as" / security prompt blocks it; raise the timeout for large or slow files.

### `The <file> was found but it's in use.`
Wait for the download to finish before consuming the file — add a short retry until the file is no longer locked. If antivirus real-time scanning holds the file open, allowlist the download folder for the robot.
