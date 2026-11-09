# Public safety — what may appear in a file that leaves the project

The user's own project takes real values; everything else takes synthetic ones.
Real connection and folder ids belong in the user's `<Name>.bpmn.ts`, the compiled `<Project>/<Name>.bpmn` and the CLI-generated `bindings_v2.json`.
Notes, summaries, examples, fixtures, and any file the user asks to make safe to share or commit stay synthetic.

## Use instead

- Synthetic names and ids: process `InvoiceApproval`, element `Task_ValidateRequest`, a person as `the approver`.
- Angle-bracket placeholders where the user must supply a real value: `<TENANT_URL>`, `<FOLDER_KEY>`, `<CONNECTION_NAME>`, `<PROCESS_NAME>`.
- A summary of what the process does, rather than its copied private source or XML.

## Sanitizing a process

Replace each private value in the `.bpmn.ts`, not in the XML.
A placeholder is a plain string in the source, and `compile` escapes it where XML needs it: `value: '<FOLDER_KEY>'` becomes `default="&lt;FOLDER_KEY&gt;"`, so the file stays well-formed.
An unescaped `<FOLDER_KEY>` typed into an XML attribute by hand breaks the file.

- **The project has `<Name>.bpmn.ts`:** edit the source and run the [validation loop](../SKILL.md#validation-loop).
- **Only a `.bpmn` (an export):** scrub it as a [brownfield edit](bpmn-runtime.md#brownfield-editing): decompile, edit the source, merge and validate as that section says, so every id, flow and diagram shape stays as it was.

The scrub-specific parts of that edit:

- **Decompile with `--keep-unused-bindings --connectors verbatim`**, and give the same two flags to every later brownfield step that takes decompile options.
  `--keep-unused-bindings` keeps the binding rows nothing reads, so you scrub them instead of losing them; `--connectors verbatim` keeps every connector task as written, so the scrub changes only the values you replace.
  `uip` 1.205.0, 1.206.0-preview.294 and earlier refuse both flags with `unknown option`, and so does `@uipath/maestro-builder-sdk` 6.91.2 behind any `uip` (builder-sdk#1916).
  On a `uip` that answers `unknown option`, drop both flags and run the rest of the steps.
  An unused binding that `decompile` drops is then gone from the merged file too, private value and all.
- **Keep private copies outside the workspace.** Write every intermediate `.bpmn` the brownfield steps produce, such as the compiled baseline, into a scratch directory, `S=$(mktemp -d)`. A baseline is compiled before the edit, so it holds the private values.
- **Write the result over the export,** because a scrub request usually asks for the file in place. If the user wants to keep the original, copy it first (`cp Export.bpmn Export.public.bpmn`) and run every step on the copy.
- **Stop at the first step that fails,** fix it through the [validation loop](../SKILL.md#validation-loop), and go on only when that step passes.
  Keep `$S` until `validate` has passed and the check below finds nothing; a fix may need its baseline again.

### Check that no private value is left

`merge` copies from the original every part the `.bpmn.ts` does not carry, so a private value there comes back unchanged.
These parts are:

- data objects and data stores, which the `.bpmn.ts` lists only in its `// DATA ELEMENTS LEFT TO THE ORIGINAL` header comment;
- extension content the builder does not model, such as `caseManagement`;
- the diagram section, `bpmndi:BPMNDiagram`, including its labels.

Build the list of values to search for in two steps:

1. Take every private value you replaced in the `.bpmn.ts`.
2. Read those kept parts of the original export and add each private value you find there. You never saw these values in the `.bpmn.ts`, so step 1 misses them.

The XML stores some characters escaped, so a raw search misses them: `Smith & Co` is `Smith &amp; Co` in the file, and `"x"` in an attribute is `&quot;x&quot;`.
For each value, search the raw form and the XML-escaped form, with `&` as `&amp;`, `<` as `&lt;`, `>` as `&gt;`, `"` as `&quot;` and `'` as `&apos;`.
Search both files that hold process text, the merged `Export.bpmn` and the left-behind `Export.bpmn.ts` with its header comment:

```bash
grep -n -F -e 'Smith & Co' -e 'Smith &amp; Co' Export.bpmn Export.bpmn.ts   # one -e per form of each value
```

No output means the check passed.
For each hit:

- **In `Export.bpmn.ts`:** replace the value in the source or the header comment.
- **In `Export.bpmn`, in a part the source carries:** fix it in the source, then run the brownfield steps after the edit again, through `validate`.
- **In `Export.bpmn`, in a part `merge` kept from the original:** edit that value in `Export.bpmn` directly, XML-escaped (`&lt;FOLDER_KEY&gt;`), then run `uip maestro bpmn validate Export.bpmn --output json` again.

Run the search again until it prints nothing. Only then delete the scratch directory, which still holds the private values:

```bash
rm -rf "$S"
```
