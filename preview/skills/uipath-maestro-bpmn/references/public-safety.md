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
  The baseline still holds the private values, so compile it into a scratch directory outside the workspace and delete that directory at the end.

The command below writes the result back over `Export.bpmn`, because a scrub request usually asks for the file in place.
If the user wants to keep the original, give `merge` a separate `-o`, such as `-o Export.public.bpmn`, and run the later steps on that file.

Stop at the first step that fails, fix it through the [validation loop](../SKILL.md#validation-loop), and go on only when that step passes.
Keep the scratch directory `$S` until `validate` has passed and the check below finds nothing; a fix may need its baseline again.

```bash
S=$(mktemp -d)
uip maestro bpmn decompile Export.bpmn -o Export.bpmn.ts --style nested --keep-unused-bindings --connectors verbatim
uip maestro bpmn compile Export.bpmn.ts -o "$S/baseline.bpmn"     # before editing
# edit Export.bpmn.ts: each private value becomes a placeholder or a synthetic label
uip maestro bpmn check Export.bpmn.ts --source
uip maestro bpmn compile Export.bpmn.ts -o "$S/edited.bpmn"
uip maestro bpmn merge "$S/edited.bpmn" --original Export.bpmn --baseline "$S/baseline.bpmn" -o Export.bpmn
uip maestro bpmn validate Export.bpmn --output json
```

`--keep-unused-bindings` keeps binding rows nothing reads, so you scrub them rather than lose them.

### Check that no private value is left

`merge` copies from the original every part the `.bpmn.ts` does not carry, so a private value there comes back unchanged.
These parts are:

- data objects and data stores, which the `.bpmn.ts` lists only in its `// DATA ELEMENTS LEFT TO THE ORIGINAL` header comment;
- extension content the builder does not model, such as `caseManagement`;
- the diagram section, `bpmndi:BPMNDiagram`.

Search both files that hold process text, the merged `Export.bpmn` and the left-behind `Export.bpmn.ts` with its header comment, for every value you replaced:

```bash
grep -n -F -e '<PRIVATE_VALUE_1>' -e '<PRIVATE_VALUE_2>' Export.bpmn Export.bpmn.ts   # one -e per real value you replaced
```

No output means the check passed.
For each hit:

- **In `Export.bpmn.ts`:** replace the value in the source or the header comment.
- **In `Export.bpmn`, in a part the source carries:** fix it in the source, then compile, merge and validate again.
- **In `Export.bpmn`, in a part `merge` kept from the original:** edit that value in `Export.bpmn` directly, XML-escaped (`&lt;FOLDER_KEY&gt;`), then run `uip maestro bpmn validate Export.bpmn --output json` again.

Run the search again until it prints nothing. Only then delete the scratch directory, which still holds the private values:

```bash
rm -rf "$S"
```
