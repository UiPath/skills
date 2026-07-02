---
confidence: medium
silent: true
---

# Read Text — Standalone System Activity Fails on Legacy .doc Files

## Context

What this looks like:
- The standalone **`Read Text`** activity under **`System > File > Word Document`** reads `.docx` files fine but **errors or returns nothing** on older `.doc` files
- Surfaces as a read/parse exception, an empty result, or a format-not-supported error when the input is a binary `.doc`

What can cause it:
- The standalone System Word Document `Read Text` activity is optimized for the **OpenXML `.docx`** format. The legacy binary **`.doc`** format is not reliably supported, so it fails or extracts nothing.

What to look for:
- The target file's extension/format — `.doc` (legacy binary) vs `.docx` (OpenXML).
- Whether the activity is the **standalone System** Read Text (the OpenXML-limited one) rather than the scoped Word-pack activity.

## Investigation

1. Confirm the input file is a legacy `.doc` (not `.docx`) — check the actual format, not just the extension (a renamed file can mislead).
2. Confirm the failing activity is the standalone `System > File > Word Document` `Read Text`, which is the OpenXML-limited surface.

## Resolution

- **Read `.doc` through the Interop container** — wrap the file in a **`Use Word File`** container (or legacy `Word Application Scope`) and read it with the Word-pack `Read Text` activity inside that scope. The Microsoft Word Interop framework the container uses opens and reads both `.doc` and `.docx` seamlessly (it converts the legacy format on open).
- **Or convert up front** — if you must stay on the standalone System activity, convert the `.doc` to `.docx` first (open-and-save-as via a Word scope, or a conversion step), then read the `.docx`.

> The Interop path requires desktop Word installed on the host (see [word-scope-com-not-installed.md](./word-scope-com-not-installed.md)). The standalone System activity does not need Word but is `.docx`-only.
