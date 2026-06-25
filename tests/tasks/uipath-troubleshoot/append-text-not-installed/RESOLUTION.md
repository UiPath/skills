# Final Resolution

---

**Root Cause:** The `Append Text` runs inside a `Word Application Scope`,
which drives Microsoft Word via **COM Interop** and needs a **registered
desktop Word** install. The locked-down unattended server (MOCK-HOST) has no
Word, so the `Word.Application` COM class cannot be created and the scope
faults at startup with `make sure Word application is installed` /
`REGDB_E_CLASSNOTREG` (0x80040154). "Worked on dev, fails on the server"
corroborates a host-environment cause, not a workflow defect.

**What went wrong:** The `ServerAppend` job (2026-06-17T07:15) faulted ~2s
after launch when the `Word Application Scope` tried to start Word, with
`Retrieving the COM class factory for component with CLSID
{000209FF-0000-0000-C000-000000000046} failed ... 0x80040154
(REGDB_E_CLASSNOTREG)`. CLSID `{000209FF-...}` is `Word.Application`.

**Why:** App-Integration Word activities (`Word Application Scope` + `Append
Text`) require Interop, which only works with a registered desktop Word on
the execution host. On a server / unattended box without Office, every such
activity faults at scope startup. The **standalone Word Document** activities
(OpenXML) do **not** need Word installed — that is the server-friendly
alternative.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: ServerAppend -- Faulted at 2026-06-17T07:15:04Z (~2s), Schedule-triggered, machine MOCK-HOST
- Folder: Server Docs (key `f4a5b6c7-d8e9-4193-c4a5-b6c7d8e9f001`)
- Final error: `make sure Word application is installed` + `REGDB_E_CLASSNOTREG` on CLSID `{000209FF-...}` (Word.Application) -> `WordApplicationScope "Word Application Scope"` -> `Main.xaml`. Faulted at scope startup (Append Text never ran).

### Project source (Root Cause)
- `Main.xaml`: `Append Text` (`WordAppendText`) inside a `Word Application Scope` opening `data\Summary.docx`. The Interop scope requires desktop Word; the activity placement is fine — the host lacks Word.

---

**Immediate fix:**

The agent can't change the server. Hand the user the host check and the two
fix paths.

### Host check (Server Docs / MOCK-HOST, as the robot's Windows user)
- Confirm whether Microsoft Word (desktop) is installed:
  `Control Panel > Programs and Features`, or
  `Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\winword.exe'`
  in PowerShell. Expect it to be **absent** on a locked-down server.

### Fix path A -- install desktop Word
- Install Microsoft Word / Office on the server under a license the robot's
  Windows user can activate, then re-run. Interop requires a registered
  desktop Word; web/online Word does not satisfy it.

### Fix path B -- switch to the standalone Word Document activities (preferred on servers)
- Replace the `Word Application Scope` + App-Integration `Append Text` with
  the standalone **`Append Text`** under the **Word Document** category,
  which uses OpenXML and needs **no Word install** — the recommended path on
  servers / unattended hosts without Office.
- **Source:** `word-activities/playbooks/word-scope-com-not-installed.md` (this Append Text case shares its signature).

> The activity placement and document are fine — the only gap is desktop Word
> on the server. On Office-less hosts, prefer the Word Document (OpenXML)
> activities over the Interop scope.

---

**Preventive fix:**

1. **Use OpenXML (Word Document) activities on servers** when full Office
   isn't provisioned, rather than the Interop `Word Application Scope`.
   - **Why:** "works on dev, fails on the server" recurs whenever the server
     image lacks desktop Word.
   - **Who:** RPA developer + platform team.

2. **Standardize the robot image** — include desktop Word if any process in
   the portfolio relies on the Interop Word scope.
   - **Who:** Platform / robot host team.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Desktop Word isn't installed on the unattended server; the Append Text's Word Application Scope can't create the Word.Application COM object | High | Confirmed | Yes | `REGDB_E_CLASSNOTREG` on CLSID for Word.Application at scope startup + "worked on dev, fails on the server" | Install desktop Word on the server, OR switch to the standalone Word Document Append Text (no Word needed) |

---

Would you like help converting the workflow to the standalone Word Document
`Append Text` (no Word install), or the exact host commands to confirm Word
is missing on MOCK-HOST?
