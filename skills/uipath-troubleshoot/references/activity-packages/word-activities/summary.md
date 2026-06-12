# Word Activities Playbooks

**Overview:** [overview.md](./overview.md) — `UiPath.Word.Activities` package, `Add Picture` execution model, and common failure patterns

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Add Picture (WordAddImage) Failures | Medium | `Add Picture` fails to insert an image. Four categories: (C1) activity placed outside a `Use Word File` / `Word Application Scope`; (C2) Word COM interop exception — `Unable to cast COM object` (`0x8002801D`, type library not registered) or `The application is busy` (`0x8001010A`), from orphaned `WINWORD.EXE`, bitness mismatch, or unregistered Office COM libraries; (C3) insertion target (text/bookmark) not found in the open document; (C4) invalid path or an in-memory `UiPath.Core.Image` bound to `Picture to insert` instead of a path string | [add-picture-failures.md](./playbooks/add-picture-failures.md) |
