# Final Resolution

---

**Root Cause:** `Download File from URL` is run inside a `For Each` loop over a
list of URLs, and the underlying `System.Net.Http.HttpClient` is **reused across
iterations**. After the first download completes, the same client instance has
already sent a request; the next iteration cannot modify its properties / start a
new request, so the activity faults with `System.InvalidOperationException: This
instance has already started one or more requests. Properties can only be
modified before sending the first request.`

**What went wrong:** The `BulkDownloader` job (started 2026-06-16T08:14:30Z)
downloaded the first file (`report-1.pdf`, iteration 1), then faulted on
iteration 2 at `Download File from URL` with the "already started one or more
requests" `InvalidOperationException`. The first-works-then-fails pattern points
at HTTP-client reuse, not a bad URL.

**Why:** A single `HttpClient` instance is single-use for property
configuration once it has sent a request. When the loop drives the download
through the same client each pass, the second iteration tries to (re)configure /
reuse a client that is already committed, and `HttpClient` throws. Each iteration
needs its own request lifecycle.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: BulkDownloader -- Faulted at 2026-06-16T08:14:35.620Z (ran ~5 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Batch Downloads (key `fa010001-d4e5-4f60-8a01-000000000001`)
- Final error: `Download File from URL: This instance has already started one or more requests ...` (`System.InvalidOperationException`) -> `Main.xaml` -> `DownloadFileFromUrl "Download File from URL"` -> `ForEach<String> "For Each url"`

### File Operations (Root Cause)
- Activity surface: `UiPath.Activities.System.FileOperations.DownloadFileFromUrl` inside a `For Each<String>`.
- Logs: iteration 1 downloaded `report-1.pdf`; iteration 2 raised the `HttpClient` "already started one or more requests" error. The per-iteration failure is the client-reuse signature, not a per-URL/network/auth problem.

---

**Immediate fix:**

Give each loop iteration its own HTTP client lifecycle.

### Fix path A -- fresh HttpClient per iteration (preferred)
Inside the loop, immediately before the download, add an `Assign` that creates a
clean client: `httpClient = New System.Net.Http.HttpClient()` (variable type
`System.Net.Http.HttpClient`), so each iteration uses a new instance.

### Fix path B -- force release after each download
Add an `Invoke Code` step right after `Download File from URL` to release the
prior client's resources:
```vbnet
GC.Collect()
GC.WaitForPendingFinalizers()
```

### Verification
Re-run the loop over multiple URLs; with a fresh client per iteration (or the GC
release), every iteration downloads instead of failing on the second.

- **Source:** `file-operations/playbooks/download-file-httpclient-reused-in-loop.md`

---

**Preventive fix:**

1. **Loop hygiene** -- scope HTTP client lifecycle per iteration when downloading
   in a loop; don't reuse one instance across requests.
   - **Why:** A single `HttpClient` reused in a loop fails after the first
     request with "already started one or more requests".
   - **Who:** RPA developer.

2. **Batch downloads** -- consider a dedicated per-item request or a properly
   pooled/disposed client pattern for bulk downloads.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Download File from URL reuses its HTTP client across For Each iterations, so the 2nd iteration can't start a new request | High | Confirmed | Yes | iteration 1 downloaded report-1.pdf, iteration 2 raised `InvalidOperationException: This instance has already started one or more requests`; activity is inside ForEach | New System.Net.Http.HttpClient per iteration, or GC.Collect/WaitForPendingFinalizers after the download |

---

Would you like help restructuring the loop with a per-iteration client, or
cleaning up the `.local/investigations/` folder?
