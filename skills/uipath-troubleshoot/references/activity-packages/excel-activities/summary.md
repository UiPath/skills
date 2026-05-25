# Excel Activities Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and testing prerequisites for Excel Activities investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Execute Macro / Run Spreadsheet Macro Failures | Medium | VBA macro invoked via `ExecuteMacro` (classic) or `Run Spreadsheet Macro` (modern) fails — most commonly `System.Runtime.InteropServices.COMException` with HRESULTs `0x80020009 DISP_E_EXCEPTION`, `0x800AC472`, or `0x80010108 RPC_E_DISCONNECTED`; sometimes a job hang with no exception when Excel surfaces a modal dialog. Causes: macro name not in workbook, VBA error inside the macro, macro tears down Excel (Workbooks.Close / Application.Quit), modal dialog (MsgBox / InputBox / debug break) blocking COM, macros disabled by Trust Center policy on the Robot host, concurrent COM access (STA apartment violation), or missing add-in / ActiveX dependency. Includes anti-patterns section rejecting Delay-as-fix and bare-Try-Catch suppression | [execute-macro-failures.md](./playbooks/execute-macro-failures.md) |
