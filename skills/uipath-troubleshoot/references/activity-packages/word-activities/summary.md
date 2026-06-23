# Word Activities Playbooks

**Overview:** [overview.md](./overview.md) — `UiPath.Word.Activities` package, `Add Picture` execution model, and common failure patterns

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Word COM / Office Interop Failures & Word Process Crashes | Medium | Environmental/host-level COM failures common to **all** Word activities (the scope and any COM-driven activity), not just `Add Picture`: (E1) type library / class not registered (`0x8002801D` / `0x80040154`); (E2) 32/64-bit mismatch between Studio/Robot and Office; (E3) Word busy or blocked (`0x8001010A` / `0x80010001`) from orphaned `WINWORD.EXE` or a modal/Protected-View dialog; (E4) `WINWORD.EXE` crashes mid-operation and the activity then throws `RPC_E_WRONG_THREAD` (`0x8001010E`) on its async-completion path (a known `Add Picture` trigger: inserting a very large image, which the activity cannot resize) | [word-com-interop-failures.md](./playbooks/word-com-interop-failures.md) |
| Add Picture (WordAddImage) Failures | Medium | `Add Picture` fails to insert an image. Four categories: (C1) activity placed outside a `Use Word File` / `Word Application Scope`; (C2) Word COM interop exception or Word process crash — environmental/host, see [word-com-interop-failures.md](./playbooks/word-com-interop-failures.md); (C3) insertion target (text/bookmark) not found in the open document; (C4) invalid path or an in-memory `UiPath.Core.Image` bound to `Picture to insert` instead of a path string | [add-picture-failures.md](./playbooks/add-picture-failures.md) |
