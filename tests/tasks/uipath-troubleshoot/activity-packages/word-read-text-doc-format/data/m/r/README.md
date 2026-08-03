# Read Text Failure - Standalone System Activity Fails on Legacy .doc

This scenario reproduces a `Read Text` failure where the standalone
`System > File > Word Document` `Read Text` activity (OpenXML, `.docx`-only)
faults on a legacy binary `.doc` file with a `FileFormatException`.

## What this scenario uncovers

**Root Cause:** The standalone System Read Text parses via OpenXML, which
understands `.docx` only. The input `Contract.doc` is a legacy binary `.doc`,
so it throws `FileFormatException` ("not a valid Office Open XML document").
Newer `.docx` files work; older `.doc` files fail. The file exists and the
path is correct — it's the format the OpenXML reader can't parse.

This maps to:
`references/activity-packages/word-activities/playbooks/read-text-doc-format.md`

The correct agent behavior is to tie the fault to the `.doc`-vs-`.docx`
limitation of the standalone activity and recommend reading through a
`Use Word File` (Interop opens both) or converting to `.docx` first — not
blaming a missing/corrupt file, the path, or the Word install.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; standalone `Read Text` with its own `FileName="data\Contract.doc"`, project depends only on `UiPath.System.Activities` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** The faulted job's `FileFormatException` explicitly
> says only `.docx` is supported and names `Contract.doc`; the project's
> dependency on `UiPath.System.Activities` only (no `UiPath.Word.Activities`)
> confirms the standalone OpenXML surface with no Interop path.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `read-text-doc-format.md`
- Agent identified the standalone System Read Text being `.docx`-only failing
  on a legacy `.doc` as the cause and recommended reading via `Use Word File`
  (Interop) or converting to `.docx` first — without blaming a
  missing/corrupt file, the path, or the install
