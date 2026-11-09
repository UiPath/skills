# Public safety — what may appear in a file that leaves the project

The user's own project takes real values; everything else takes synthetic ones.
Real connection and folder ids belong in the user's `<Name>.bpmn.ts`, the compiled `<Project>/<Name>.bpmn` and the CLI-generated `bindings_v2.json`.
Notes, summaries, examples, fixtures, and any file the user asks to make safe to share or commit stay synthetic.

## Never include

- Raw exported BPMN or `.bpmn.ts` from customers, tenants, demos, or operator-supplied examples.
- Tenant URLs, organization names, folder keys, connection ids, release keys, queue ids, process ids, user ids, or email addresses.
- Real person names, private process names, business payloads, screenshots, package contents, or traces.
- Local absolute paths from a developer machine, task transcripts, or internal-only repository paths.

## Use instead

- Synthetic names and ids: process `InvoiceApproval`, element `Task_ValidateRequest`, a person as `the approver`.
- Angle-bracket placeholders where the user must supply a real value: `<TENANT_URL>`, `<FOLDER_KEY>`, `<CONNECTION_NAME>`, `<PROCESS_NAME>`.
- A summary of what the process does, rather than its copied private source or XML.

## Sanitizing a process

Replace each private value in the `.bpmn.ts`, not in the XML.
A placeholder is a plain string in the source, and `compile` escapes it where XML needs it: `value: '<FOLDER_KEY>'` becomes `default="&lt;FOLDER_KEY&gt;"`, so the file stays well-formed.
An unescaped `<FOLDER_KEY>` typed into an XML attribute by hand breaks the file.

- **The project has `<Name>.bpmn.ts`:** edit the source and run the [validation loop](../SKILL.md#validation-loop).
- **Only a `.bpmn` (an export):** scrub it as a [brownfield edit](bpmn-runtime.md#brownfield-editing), so every id, flow and diagram shape stays as it was.
  The baseline still holds the private values, so compile it into a scratch directory outside the workspace and delete that directory after the merge.

```bash
S=$(mktemp -d)
uip maestro bpmn decompile Export.bpmn -o Export.bpmn.ts --style nested --keep-unused-bindings --connectors verbatim
uip maestro bpmn compile Export.bpmn.ts -o "$S/baseline.bpmn"     # before editing
# edit Export.bpmn.ts: each private value becomes a placeholder or a synthetic label
uip maestro bpmn check Export.bpmn.ts --source
uip maestro bpmn compile Export.bpmn.ts -o "$S/edited.bpmn"
uip maestro bpmn merge "$S/edited.bpmn" --original Export.bpmn --baseline "$S/baseline.bpmn" -o Export.bpmn
uip maestro bpmn validate Export.bpmn --output json
rm -rf "$S"
```

`--keep-unused-bindings` keeps binding rows nothing reads, so you scrub them rather than lose them.
Before you report done, search the result for every value you replaced: none may remain.
