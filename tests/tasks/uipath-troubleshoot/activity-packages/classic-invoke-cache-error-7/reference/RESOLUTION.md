# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** **Project cache corruption.** Studio's compiler lost track of the project's local
workflow dependencies — typically after repeated debug runs — and reports the invoked workflows as
missing (Cache Mechanism Error, `Error code: 7`) even though the `.xaml` files are still present in the
project. This is a stale-cache problem, not a real missing dependency.

**What went wrong:** This is a **design-time / build-time** failure in Studio, not a robot job fault.
`Main.xaml` invokes `ValidateOrder.xaml` and `PostOrder.xaml`; both files exist in the project source.
The build nonetheless reports them missing with `Error code: 7`, which is the signature of a corrupted
project cache — the compiler's cached dependency map has drifted from what is actually on disk.

**Why:**
- `process/Main.xaml` — two `Invoke Workflow File` activities: InvokeWorkflowFile_1 →
  `ValidateOrder.xaml`, InvokeWorkflowFile_2 → `PostOrder.xaml`.
- `process/ValidateOrder.xaml` and `process/PostOrder.xaml` — **both present** in the project. The
  invoked workflows the error calls "missing" are on disk.
- A stale build cache is present (`process/obj/`) — leftover build output from prior debug runs, the
  kind of state that corrupts the compiler's dependency tracking.
- The error is `Cache Mechanism Error` / `Error code: 7` / "Invoked workflows are missing" — a cache
  bookkeeping fault, not a missing-file or path fault (the files resolve on disk).

**Evidence:**
- Error string: `Invoked workflows are missing` + `Cache Mechanism Error (Error code: 7)`.
- Invoked targets `ValidateOrder.xaml` / `PostOrder.xaml` both exist under `process/`.
- Stale `obj/` build artifacts present.
- No Orchestrator job, log, or trace — the failure surfaces in Studio's Output at build/debug time.

**Immediate fix:**
1. **Close Studio.**
2. In the project folder, **delete the `.local` folder** to clear the project cache.
3. Deleting the `bin` and `obj` folders is also safe and recommended.
4. **Reopen the project** so Studio rebuilds a fresh cache. The invoked workflows resolve again once
   the stale cache is gone.

**Preventive fix:**
- Clear `.local` / `bin` / `obj` after long debugging sessions if the compiler starts reporting phantom
  missing workflows; the cache can drift after many debug runs.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The project cache is corrupted; the compiler reports invoked workflows missing (`Error code: 7`) even though `ValidateOrder.xaml` and `PostOrder.xaml` are present on disk. | high | confirmed | Yes | Both invoked files present under `process/`; error is Cache Mechanism Error / code 7; stale `obj/` build output present. | Close Studio, delete `.local` (and `bin`/`obj`), reopen to rebuild the cache. |
| H2 | The invoked workflows were actually deleted or moved out of the project. | low | eliminated | No | `ValidateOrder.xaml` and `PostOrder.xaml` both exist in the project source at the paths the invokes reference. | N/A — the files are present; this is a cache fault, not a missing file. |
