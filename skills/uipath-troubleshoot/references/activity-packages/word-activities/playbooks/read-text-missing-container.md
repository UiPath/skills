---
confidence: high
---

# Read Text — Activity Outside Its Container (Validation Warning / Runtime Error)

## Context

What this looks like:
- The modern `Read Text` activity (from the `UiPath.Word.Activities` pack) shows a **design-time validation warning** ("activity must be placed inside a `Use Word File`") or **faults at runtime** as invalid / missing parent
- Common messages: `Read Text` must be inside a `Use Word File` (or legacy `Word Application Scope`); a validation error preventing the run, or a runtime "activity is not valid in this context"

What can cause it:
- The modern Word-pack `Read Text` activity has **no file input of its own** — it reads the document held open by a surrounding `Use Word File` / `Word Application Scope` container. Dropped **outside** any container, it has nothing to read and is invalid.

What to look for:
- Whether the `Read Text` node is nested inside a `Use Word File` / `Word Application Scope` in the `.xaml`, or sits loose in the sequence.
- Whether the activity is the **modern pack** Read Text (needs a container) or the **standalone System** Read Text (takes its own file path).

## Investigation

1. Read the workflow `.xaml`. Confirm the `Read Text` node is the modern Word-pack activity and whether it is inside a `Use Word File` / `Word Application Scope`.
2. Note whether the failure is design-time (validation warning in Studio) or a runtime invalid-context fault — both point at the same missing-container cause.

## Resolution

- **If you want to read from an already-open document** — move the `Read Text` activity **inside** a `Use Word File` container (or a legacy `Word Application Scope`) that opens the target file. The activity then reads the container's open document.
- **If you want a stand-alone read with no container** — use the native **`Read Text`** activity under **`System > File > Word Document`** instead. It takes the **file path directly in its own properties**, so no scope is required.
- **Pick one surface deliberately** — the pack Read Text (scoped) for workflows already inside a Word scope; the System Word Document Read Text (standalone) for a one-off extraction by path.
