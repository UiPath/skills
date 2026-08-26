# Final Resolution

---

**Root Cause:** The document arrived as an **email attachment** (from outside
the machine), so it carries a **Mark-of-the-Web**. Word opens such files in
**Protected View** — a read-only sandbox — and the Interop read against a
Protected-View document is blocked, faulting with a `COMException` ("the
command cannot be performed because a document is open in Protected View").
Internally-created documents have no Mark-of-the-Web and read fine.

**What went wrong:** The `InboundDocReader` job (2026-06-16T11:02) opened
`Invoice_From_Email.docx` and faulted with `Word cannot open the document …
because it is in Protected View (the file originated from an Internet/email
location)`. The failure is specific to externally-sourced files.

**Why:** Windows tags files downloaded or received from outside the machine
with a Mark-of-the-Web (a zone identifier). Word treats those as untrusted
and opens them in Protected View, which blocks programmatic (Interop) access
until the file is trusted. The same workflow reads locally-authored files
without issue because they carry no such tag. This is a host **security
configuration / file-trust** issue, not a format, path, or install problem.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: InboundDocReader -- Faulted at 2026-06-16T11:02:06Z (ran ~4s)
- Folder: Inbound Docs (key `c9d0e1f2-a3b4-4193-bf50-14a5b6c7d8e9`), machine MOCK-HOST
- Final error: `COMException: The command cannot be performed because a document is open in Protected View` — `Word cannot open … because it is in Protected View (the file originated from an Internet/email location)` -> `Word Application Scope` -> `Main.xaml`
- The error names Protected View and the Internet/email origin; the user reports only externally-sourced files fail.

### Project source (context)
- `Main.xaml`: a `Word Application Scope` opens `data\inbound\Invoice_From_Email.docx` and reads it with `Read Text`. The file path and activity are correct — the open is blocked by Protected View, not a config defect in the workflow.

---

**Immediate fix:**

The agent cannot change the robot host's settings. Hand the user host steps
(and an optional workflow pre-step).

### Host steps (Inbound Docs / MOCK-HOST, as the robot's Windows user)
1. **Unblock the file before reading (most targeted)** — clear the
   Mark-of-the-Web: `Right-click > Properties > Unblock`, or run
   `Unblock-File <path>` in PowerShell. This can be wired as a workflow
   pre-step (run `Unblock-File` on each inbound file before the read).
2. **Add the inbound folder to Trusted Locations** — `File > Options >
   Trust Center > Trust Center Settings > Trusted Locations`, add
   `…\Inbound Docs\data\inbound`. Files there skip Protected View.
3. **Disable Protected View** — `File > Options > Trust Center > Trust
   Center Settings > Protected View` and uncheck the relevant rules (files
   from the internet / Outlook attachments / unsafe locations). Apply only
   on a controlled robot host — it lowers a safety control.
- **Source:** `word-activities/playbooks/read-text-protected-view.md`

> Prefer the per-file `Unblock-File` pre-step or Trusted Locations over a
> blanket Protected View disable, to keep the safety control for everything
> else on the host.

---

**Preventive fix:**

1. **Unblock inbound files at intake** — add an `Unblock-File` (or
   equivalent) step when saving email attachments, so Protected View never
   triggers downstream.
   - **Why:** email/internet attachments always carry a Mark-of-the-Web.
   - **Who:** RPA developer.

2. **Provision a trusted inbound folder** — designate the inbound directory
   as a Word Trusted Location on robot hosts that process external documents.
   - **Who:** Platform / robot host team.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Email-sourced documents carry a Mark-of-the-Web, so Word opens them in Protected View and blocks the Interop read | Medium | Confirmed | Yes | `COMException … document is open in Protected View` / "originated from an Internet/email location" + only externally-sourced files fail | Unblock the file (Unblock-File pre-step), add the folder to Trusted Locations, or disable Protected View on the host |

---

Would you like an `Unblock-File` pre-step added to the workflow, or the exact
Trusted Locations / Protected View steps for MOCK-HOST?
