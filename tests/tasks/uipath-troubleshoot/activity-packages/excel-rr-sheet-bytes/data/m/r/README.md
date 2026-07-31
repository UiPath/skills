# Excel Read Range — Sheet Name Visually Identical But Byte-Different

This scenario reproduces a Read Range failure where the configured
`SheetName` and the workbook's actual sheet name **look identical
in every UI surface** but differ at the byte level — non-breaking
space `U+00A0` vs regular space `U+0020`. The job ends with:

```
UiPath.Excel.BusinessException: The sheet with the name 'Quarterly Data' does not exist.
```

## What this scenario uncovers

**Expected outcome:** The agent matches the playbook AND either
(a) identifies the `U+00A0` vs `U+0020` mismatch from the byte
content of the `Get Workbook Sheets` log evidence — the JSON tool
output preserves the real code points, and an LLM agent reads
bytes, not pixels — or (b) narrows to the whitespace/look-alike
branches and recommends the host-side byte-compare (the PowerShell
snippet from the playbook) to identify the code point. The agent
must NOT assert a specific code point without byte-level evidence,
and must NOT pick a branch (typo, case, rename) the CLI evidence
rules out.

**The branches that COULD apply** without further evidence:

- Leading/trailing whitespace (branch 5) — visible only when
  inspecting byte-by-byte.
- Look-alike Unicode character (branch 6) — NBSP, Cyrillic vs
  Latin letters, curly vs straight quotes; visually identical in
  every UI surface.

**The branches that are ruled OUT by the CLI evidence:**

- Typo (branch 1) — configured and logged names are visually
  identical.
- Case mismatch (branch 2) — visually identical, same case.
- Sheet renamed (branch 3) — the configured name appears in the
  Get Workbook Sheets log output.
- Sheet deleted (branch 4) — the configured name appears in the
  Get Workbook Sheets log output.
- Dynamic expression resolved wrong (branch 7) — workflow source
  shows a literal `SheetName: "Quarterly Data"`.

The agent may resolve between the remaining branches by inspecting
the bytes the job-log evidence already carries; what it must NOT do
is assert a specific code point it never inspected. Unsupported
confident guessing is the failure mode this test catches.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `ExcelDailyImport` project — `Use Excel File` → `Get Workbook Sheets` (logs result) → `Read Range "Quarterly Data"` (fails). Configured name uses regular space `U+0020` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses. The job logs surface the actual sheet name with `U+00A0` between the words; visible only via byte-inspection |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The expected investigation chain: `folders list-current-user` →
`jobs list --state Faulted` → `jobs get` → `jobs logs` → workflow
source review → recognize that all visible names match → identify
the NBSP from the log bytes, or recommend the host-side
byte-compare command from the playbook.

> **Note on fixtures.** Synthetic. The actual sheet name in the
> fixture log message is stored as a real non-breaking space byte
> in the mock response. It renders identically to a regular space
> for a human reader, but the bytes reach the agent's tool output
> intact — so byte-level identification is a legitimate diagnosis
> path. Keep the raw NBSP byte in the mock (a six-character
> backslash-u escape would disclose the answer as plain ASCII).
