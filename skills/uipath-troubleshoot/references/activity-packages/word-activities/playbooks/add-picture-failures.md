---
confidence: medium
---

# Add Picture (WordAddImage) Failures

## Context

`Add Picture` (`UiPath.Word.Activities.WordAddImage`) fails to insert an image into a Word document. The failure falls into one of four distinct categories, each with its own signature and fix. Identify the category first, then apply the matching resolution.

What this looks like:
- A design-time validation warning that the activity is invalid, or an immediate fault when the activity is reached
- A Word COM HRESULT — `Unable to cast COM object ... 0x8002801D` or `The application is busy ... 0x8001010A`, or Word (`WINWORD.EXE`) faulting and closing mid-insert with a `RPC_E_WRONG_THREAD ... 0x8001010E` cast error (see C2)
- A missing-reference error — the bookmark or text anchor where the image should go cannot be found
- A file-not-found or generic exception while reading the `Picture to insert` value

What can cause it — four distinct mechanisms:

- **C1. Activity outside a Word scope.** `Add Picture` is not nested inside a `Use Word File` (`WordProcessScope`) or `Word Application Scope`. It has no document handle of its own — outside a scope there is no document to insert into, so it is invalid. Faults synchronously or shows a design-time validation error. (A common variant: `Add Picture` lives in an `Invoke Workflow File` child and the scope's document context does not cross the invoke boundary.)
- **C2. COM / Interop exception or Word process crash.** The Word COM layer faults, or `WINWORD.EXE` itself crashes mid-insert and the activity then throws a COM cast / `RPC_E_WRONG_THREAD` (`0x8001010E`) error on its async-completion path. This is an **environmental / host-level** failure that is not specific to `Add Picture` (it can hit any Word activity), so its full signature set, decision tree, and fixes live in the package-level playbook **[word-com-interop-failures.md](./word-com-interop-failures.md)** (causes E1 type-library/class not registered, E2 bitness mismatch, E3 busy/blocked, E4 Word process crash). One trigger that *is* Add-Picture-specific: inserting a very large but otherwise valid image — `Add Picture` has no resize property, so a multi-megapixel image is handed to Word at full resolution and can crash it (E4).
  Background/unattended project metadata alone does **not** establish the cause of that crash. If Word launched, opened the document, and then died during insertion, retain the E4 diagnosis and investigate the faulting module, Office health/bitness, orphaned processes, and image size; do not substitute an interaction-setting change for crash remediation.
- **C3. Insertion target not found.** `Insert relative to` is `Text` or `Bookmark`, but the anchor does not exist in the open document. Text matching is **case- and whitespace-sensitive**; the named bookmark may be a typo, may live only in a template, or may have been removed upstream. (`Insert relative to = Document` has no anchor dependency.)
- **C4. Invalid path or unusable image.** `Picture to insert` (`ImagePath`) cannot be read. Causes: an in-memory `UiPath.Core.Image` variable was bound instead of a path string; a relative path that does not resolve under the Robot account; a missing/moved file (UNC unreachable, drive not mapped, OneDrive placeholder); or a path typo / extension-casing mismatch.

## Causes

Name the confirmed sub-cause exactly. Do NOT assert a cause unless the investigation decision tree arrived at it.

- **C1.** Activity outside a `Use Word File` / `Word Application Scope`.
- **C2.** Word COM / Interop exception or Word process crash (environmental/host) — see **[word-com-interop-failures.md](./word-com-interop-failures.md)**.
- **C3.** Insertion target (text/bookmark) not found in the open document.
- **C4.** Invalid path or unusable image fed to `Picture to insert`.

## Investigation

1. **Read the error signature** from job evidence and the `Add Picture` configuration from the `.xaml`. Match against the decision tree below; stop at the first match.
2. **Decision tree:**
   - Design-time "invalid activity" validation error, or a missing-scope/context message → **C1**. Confirm in the `.xaml` that no ancestor of `Add Picture` is a `Use Word File` / `Word Application Scope` (and that the document context is not lost across an `Invoke Workflow File` boundary).
   - Error contains a COM HRESULT (`0x8002801D`, `0x8001010A`, `0x8001010E`, or related), **or** Word (`WINWORD.EXE`) faulted/closed mid-insert → **C2**. This is a host/COM-layer failure shared by all Word activities — switch to **[word-com-interop-failures.md](./word-com-interop-failures.md)** and follow its decision tree (E1 type-library/class not registered, E2 bitness, E3 busy/blocked, E4 Word process crash). Note for `Add Picture` specifically: a very large but valid image can crash Word on insert (E4), since the activity has no resize property.
   - Error references a missing bookmark or an unlocatable text anchor → **C3**. Read `InsertRelativeTo` and its anchor (`Text` string / `BookmarkName`), open the document the scope actually opened, and search for the anchor exactly (case + whitespace for text; the bookmark list for bookmarks). Confirm the opened file is the intended document, not a template or stale copy.
   - File-not-found or a generic exception reading the image → **C4**. Read the `ImagePath` binding and its type. If it is a `String`, resolve it to a concrete path and confirm the file exists on the robot host under the Robot's Windows user; if relative, determine the working directory it resolves against at runtime. If it is an `Image`/object variable, that is the cause.

## Resolution

Apply the fix for the identified sub-cause.

- **C1 — outside a scope:** wrap `Add Picture` in a `Use Word File` (preferred) or `Word Application Scope` pointed at the target document, and move the activity into the scope body. If it sits in an invoked child workflow, open the scope in that child or move the activity into the parent — scope context does not cross the invoke boundary implicitly. If the structure looks correct but validation still flags it, confirm `UiPath.Word.Activities` is installed and restored in `project.json`.
- **C2 — COM / Interop or Word crash:** apply the fixes in **[word-com-interop-failures.md](./word-com-interop-failures.md)** for the identified host cause (E1 online-repair of Office; E2 match bitness; E3 clear orphaned `WINWORD.EXE` / dismiss modal / unblock downloaded files; E4 Word process crash). The XAML is correct — do not edit it. For an `Add Picture`-specific E4 crash on a large image, **pre-resize the image before inserting it** (the activity has no resize property), use a smaller image, or insert via `Paste Chart/Picture Into Document`. If Office cannot be made reliable, migrate to the file-based `Word Document` activities (System > File > Word Document).
- **C3 — target not found:** correct the `Text` anchor to match the document exactly (case + whitespace) or normalize the document text; add or fix the `BookmarkName` so it points at a bookmark that exists in that document. If only top/bottom placement is needed, switch `Insert relative to` to `Document` with `Position` = `Start` / `End` to drop the anchor dependency entirely. If the wrong document was opened, fix the scope's file path.
- **C4 — invalid path / image:** if an in-memory `UiPath.Core.Image` was bound, save it to disk first with `Save Image` and pass that path string. Use a fully-qualified **absolute** path (e.g. `C:\Images\chart.png`) or build one explicitly (`Path.Combine(...)`) so it resolves identically under the Robot account. Ensure the file is present and readable on the robot host under the Robot's Windows user.

If a COM HRESULT or Word crash (C2) persists after all environmental causes are ruled out, follow the escalation guidance in **[word-com-interop-failures.md](./word-com-interop-failures.md)** (capture a `Verbose` robot log plus a Process Monitor trace and/or a ProcDump crash dump of `WINWORD.EXE`, and the offending image) and open a UiPath support case.
