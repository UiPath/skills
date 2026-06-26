---
confidence: medium
---

# Download File from URL — "This instance has already started one or more requests"

## Context

What this looks like:
- `Download File from URL` faults with `This instance has already started one or more requests. Properties can only be modified before sending the first request.` (a `System.InvalidOperationException` from `System.Net.Http.HttpClient`).
- The failure appears on the **second (or a later) iteration** when the activity runs inside a `For Each` / loop downloading multiple files; the first download often succeeds.

What can cause it:
- **Reused / improperly-disposed HTTP client across loop iterations.** The underlying `HttpClient` from the first download is still occupied (or was disposed and is being reused), so the next iteration cannot start a fresh request — `HttpClient` forbids changing properties / starting requests on an instance that already sent one.

What to look for:
- Whether `Download File from URL` sits inside a `For Each` / `While` loop over multiple URLs.
- Whether the failure is iteration-dependent (first item works, later items fail) — the signature of client-lifecycle reuse, not a per-URL problem.

## Investigation

1. Read the error from job evidence; confirm it is `This instance has already started one or more requests` at `Download File from URL` (an `HttpClient`/`InvalidOperationException`), not an HTTP status, DNS, or file-finalize error.
2. Read the `.xaml`: confirm the download activity is inside a loop, and how the HTTP client / download is structured per iteration.
3. Confirm the timing — first iteration succeeds, a later one fails — pointing at client reuse rather than a bad URL.

## Resolution

- **Instantiate a fresh HTTP client per iteration (preferred):** add an `Assign` immediately before the download inside the loop so each iteration uses a clean client — `httpClient = New System.Net.Http.HttpClient()` (variable type `System.Net.Http.HttpClient`).
- **Force release after each download (alternative):** drag an `Invoke Code` block right after the download step to release the prior client's resources:
  ```vbnet
  GC.Collect()
  GC.WaitForPendingFinalizers()
  ```
- **General:** ensure each loop iteration owns its own request lifecycle (new client per item, or a properly scoped/disposed client) so no instance is asked to start a second request.
