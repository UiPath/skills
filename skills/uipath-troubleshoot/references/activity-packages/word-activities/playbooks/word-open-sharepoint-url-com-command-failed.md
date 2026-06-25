---
confidence: medium
---

# Word Application Scope — Open SharePoint URL COMException "Command failed"

## Context

What this looks like:
- `Word Application Scope` / `Use Word File` faults on **open**, not on a child save/export.
- Exception type `System.Runtime.InteropServices.COMException`, message `Command failed`.
- Stack runs through the OPEN path:
  - `Microsoft.Office.Interop.Word.Documents.Open(...)`
  - `UiPath.Word.Windows.Utilities.WordDocumentFactory.OpenOrCreateNewDocument`
  - `UiPath.Word.Windows.Utilities.WordDocumentFactory.CreateDocument` / `CreateRuntimeWordDocument`
  - `UiPath.Word.Activities.WordApplicationScope.Execute`
- The scope's `FilePath` is a SharePoint / OneDrive **web sharing link**, recognizable by a `:w:` / `:x:` / `:p:` / `:f:` segment and a `?e=` token — e.g. `https://<tenant>-my.sharepoint.com/:w:/p/<user>/<token>?e=<id>`. The scope is often nested inside a `Use OneDrive and SharePoint` (`UseDriveCard`) activity.
- Distinct from the COM wrong-thread cast (`0x8001010E`, IID `{0002096B-...}`) — that faults on a child cast, not on `Documents.Open`. See [word-export-pdf-com-wrong-thread.md](./word-export-pdf-com-wrong-thread.md).

What can cause it (more than one may apply):
- **Web-view sharing-link URL passed verbatim** — `Word Application Scope` passes `FilePath` straight to local Word's `Documents.Open`. A `:w:`/`:f:` sharing link is a browser-redirect landing page, not a document filename, so `Documents.Open` cannot resolve it → generic `COMException "Command failed"`. The enclosing `Use OneDrive and SharePoint` card does **not** pre-download or resolve the file for the nested Word activity — it only manages the M365 connection.
- **`CreateNewFile` against a URL** — `CreateNewFile` defaults `True` when the attribute is absent. "Create if not exists" is not supported with a URL path; `uip rpa validate` surfaces this as a warning, and the create branch fails against a remote URL.
- **File not openable by Word** — locked / checked-out, Protected View, password-protected, an online-only OneDrive placeholder not materialized locally, or an unsupported format.

What to look for:
- The exact `FilePath` value and whether it is a `:w:`/`:f:` sharing link vs a direct document URL vs a local/UNC path.
- Whether `CreateNewFile` is set or defaulting to `True`.
- Whether the document already exists at the target location.

## Investigation

1. Read the error from job evidence. Confirm the type is `COMException` with message `Command failed` and the top frame is `Documents.Open` (the OPEN branch) — not a child cast and not `WordAppHelpers.StartNewApplication` (COM-start; see [word-com-start-background-session0.md](./word-com-start-background-session0.md)).
2. Read the faulted `Word Application Scope` from the `.xaml`. Capture the verbatim `FilePath`, the `CreateNewFile` value (absent ⇒ `True`), and whether the scope sits inside a `Use OneDrive and SharePoint` / `UseDriveCard`.
3. Classify the `FilePath`: a SharePoint web-view **sharing link** has a `:w:`/`:x:`/`:p:`/`:f:` segment and a `?e=` token. A **direct document URL** looks like `https://<tenant>-my.sharepoint.com/personal/<user>/Documents/<file>.docx`. A **local/synced** path is a drive/UNC path.
4. Run `uip rpa validate --file-path "<MAIN_XAML>" --output json`. A warning `'Create if not exists' is not supported when using a URL for the file path` confirms the `CreateNewFile`-with-URL problem.
5. Out-of-band: have the user paste the `FilePath` into desktop Word **File > Open** on the robot host. A sharing link fails there too; a direct document URL or synced local path opens.

## Resolution

- **If `FilePath` is a `:w:`/`:f:` sharing link:** replace it with a Word-openable form — a direct document URL (`.../personal/<user>/Documents/<file>.docx`; in SharePoint use *Copy link* and pick a direct document link, strip any `?web=1`/`?e=` suffix), a WebDAV-style path, or a synced/downloaded local path. Confirm the replacement opens in desktop Word File > Open before relying on it.
- **If `CreateNewFile` defaults `True` and the document already exists:** set `CreateNewFile = False`. "Create if not exists" is unsupported with a URL path; re-run `uip rpa validate` and confirm the warning clears.
- **If the document must stay in SharePoint:** restructure to **download-then-open** — the `Use OneDrive and SharePoint` card does not auto-download for the nested Word activity, so use the connector's file activities to pull the file to a local path, then point `Word Application Scope` at that local path. A guaranteed-local path removes the URL-format and authentication dependencies entirely.
- **If a direct URL still fails after the format is correct:** local Word reaching SharePoint depends on cached M365 credentials in the robot's Word process; an unauthenticated open surfaces the same generic `COMException`. Prefer a synced/local path, or ensure the robot's Word session is signed in to the tenant.

If the failure persists with a confirmed Word-openable path that opens in desktop Word File > Open, capture a `Verbose` robot log plus the full stack and open a UiPath support case.
