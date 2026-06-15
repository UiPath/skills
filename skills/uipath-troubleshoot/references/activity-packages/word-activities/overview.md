# Word Activities

Activities from the `UiPath.Word.Activities` package for automating Microsoft Word on Windows. The classic `Word Application Scope` (`UiPath.Word.Activities.WordApplicationScope`) drives a real WINWORD.EXE instance via **Microsoft Word Interop (COM)** — it requires desktop Word installed on the execution host. A modern `Use Word File` surface exists for newer design experiences and is the recommended migration target for several classic failure modes.

## How Word Application Scope Executes

`Word Application Scope` opens a `.docx`/`.doc`/`.dotx` document inside a COM-backed WINWORD.EXE session, runs the child activities against that open document, then saves and closes. Behaviour chain:

1. Create the `Word.Application` COM instance (requires registered desktop Word; bitness must be compatible with the robot process)
2. Open the document at the configured path (or create it when `Create if not exists` is set)
3. Run child activities against the open document
4. Save and close, releasing the WINWORD.EXE handle

Failures originate at distinct layers — COM/Interop availability (step 1), file resolution and locks (step 2), interactive prompts that block COM (any step), or package/type loading (before step 1). Knowing which layer produced the error narrows the investigation.

## Key Activities

- **Word Application Scope** (`WordApplicationScope`, display name "Word Application Scope") — open a Word document via Interop and run child activities against it. **COM-only** — requires desktop Word. Properties include the document `Path`, `CreateIfNotExists` (generate the file when absent), and `Password`.

## Common Failure Patterns

- **Word not installed / COM interop failure** — the scope faults at startup creating the COM instance. Surfaces as `Error opening document, make sure Word application is installed`, `REGDB_E_CLASSNOTREG` (`80040154`), or `Could not load ... Microsoft.Office.Interop.Word`. Causes: no desktop Word (web-only Office, Linux/container robot), 32-bit/64-bit Office–robot bitness mismatch, or damaged Office COM registration.
- **"The file appears to be corrupted"** — opening/saving fails reporting corruption. Causes: an orphaned WINWORD.EXE holding the file lock, an in-place template overwrite leaving a half-written source, or Protected View / Mark-of-the-Web blocking the write.
- **Workflow hangs / freezes indefinitely** — WINWORD.EXE is up but unresponsive because Word opened a background modal prompt (password, document-recovery sidebar, Safe Mode, activation, trust-this-file). When the scope runs invisibly, the dialog still wedges the COM calls.
- **"Cannot create unknown type WordApplicationScope"** — load/compile-time failure: the execution host lacks the `UiPath.Word.Activities` package dependency, or runs a version without the type. Common when a process works in Studio but fails on a remote robot with a different/missing package version.
- **File path verification errors** — the document path does not resolve at runtime. Causes: opening a file that should be created (`Create if not exists` unset), a relative path resolved against the wrong working directory, a dynamically built path constructed incorrectly, or an unavailable mapped drive / unhydrated cloud placeholder.

## Package

NuGet: `UiPath.Word.Activities`

Version-specific bugs are documented in the relevant playbooks.
