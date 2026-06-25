---
confidence: medium
---

# Word Application Scope — File Path Verification Errors / Document Not Found

## Context

What this looks like:
- Activity `Word Application Scope` (`UiPath.Word.Activities.WordApplicationScope`) faults because the target document does not exist at the resolved path — `Could not find file '<path>'`, `Could not find a part of the path`, or a generic open failure pointing at a path that is wrong
- The path string is built dynamically and resolves to the wrong location at runtime

What can cause it:
- The target file genuinely does not exist (the workflow expects to **create** a new document but the scope is configured to open an existing one)
- A **relative path** resolves against the wrong working directory — on an unattended robot a relative path resolves against the robot's working directory (often `C:\Windows\System32\config\systemprofile`), not the project folder, so a path that resolves correctly in Studio is not found at runtime
- A **dynamically generated path** is built incorrectly (string concatenation with wrong separators, missing folder segment, stale variable)
- Under an unattended robot session, a mapped drive letter is not available, or a OneDrive/SharePoint Files-On-Demand placeholder has not been hydrated

What to look for:
- Whether the workflow intends to open an existing document or create a new one.
- How the path is constructed (literal vs. concatenation vs. `Path.Combine`).

## Investigation

1. Read the `Word Application Scope` node from the `.xaml` and capture the literal expression bound to the document path.
2. Resolve that expression to a concrete path for the failing run and confirm whether the file exists at that location on the robot host (not the developer machine).
3. If the path is relative, determine the robot's working directory at run time — relative paths resolve there, not against the document's folder.
4. Confirm the intent: is the scope meant to open an existing document, or generate a new one?

## Resolution

- **If a new document should be created** — enable the activity's `Create if not exists` option so the scope generates the file when it is absent, instead of faulting.
- **If the path is relative or fragile** — build an **explicit absolute path** (an absolute root or a UNC path the robot can reach), or anchor the filename to a known base folder, rather than concatenating bare strings — so it resolves deterministically on every host. Do **not** rely on `Environment.CurrentDirectory`: on an unattended robot that is the robot's working directory (`...\systemprofile`), not the project folder, so `Path.Combine(Environment.CurrentDirectory, "yourfile.docx")` resolves to the same wrong location that failed. For a configurable base, store the folder path in an Orchestrator asset and combine the filename onto it.
- **If a mapped drive / cloud placeholder is the issue** — use a UNC path the robot session can reach, or ensure OneDrive/SharePoint files are hydrated (not Files-On-Demand placeholders) before the run.
- **If the file was moved/deleted upstream** — fix the upstream step that produces it, or add a `Path Exists` check before the scope to fail with a clear message instead of a raw open error.
- **If you are on StudioX / modern design** — consider replacing `Word Application Scope` with the modern `Use Word File` activity, which provides improved stability and clearer file-resolution behavior.
