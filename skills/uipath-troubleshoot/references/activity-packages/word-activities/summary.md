# Word Activities Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and testing prerequisites for Word Activities investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Save Document as PDF — COM Wrong-Thread (0x8001010E) | Medium | `Save Document as PDF` (`WordExportToPdf`) or another child of `Word Application Scope` faults casting the document to `Microsoft.Office.Interop.Word._Document` (IID `{0002096B-...}`) with `RPC_E_WRONG_THREAD`. Causes: scope attached to an already-open external Word, that external Word closed mid-run, an off-STA / Session-0 / background runtime, or a non-creator thread (Parallel/Pick/Invoke/coded). `Word Application Scope` exposes no isolated-instance control | [word-export-pdf-com-wrong-thread.md](./playbooks/word-export-pdf-com-wrong-thread.md) |
