# Complex Connector Activity Inputs

## Activation gate

Read this guide only when the resolved activity schema or SDD reveals at least one of:

- an `inputs.bodyFields[].name` containing `[*]`;
- a non-null `inputs.multipart` / file parameter; or
- a requested server-side filter on an operation with `spec.filter`.

Do not load it for a scalar connector activity without a server-side filter. The ordinary discovery, input mapping, spec-cache, and task-envelope procedures remain in `planning.md` and `impl-json.md`.

## Array-of-object body fields

### Planning translation

In a spec field such as `recipients[*].address`, `[*]` is schema notation for an array element, not a legal `bodyParameters` key. Group fields by the prefix before `[*]`, then translate each SDD value:

| Fields under one parent | SDD value | `tasks.md input-values.bodyParameters[parent]` |
|---|---|---|
| One leaf `<parent>[*].<leaf>` | Scalar list matching the leaf `dataType` | One nested object per scalar: `[nestUnder(<leaf>, value), ...]` |
| One or more leaves | Object list already matching the element shape | Preserve the list unchanged |
| Two or more leaves | Scalar list | Halt and ask which leaf receives each scalar; require an object list |
| Any | Single non-list value | Halt and ask whether to wrap it as a one-element list |

The lean spec's `name`, `dataType`, and `description` are authoritative. For example, `recipients[*].address` plus `['a@x','b@y']` becomes:

```json
{"recipients":[{"address":"a@x"},{"address":"b@y"}]}
```

Never emit a literal `[*]` key. Keep the real array under its parent name.

### Step 1.b — Array-of-object body fields: pre-input scan (MANDATORY)

Before `case spec --input-details`, recursively scan the keys in `bodyParameters`. If any key contains literal `[*]`, halt:

```text
ERROR: bodyParameters key '<key>' contains literal '[*]'.
       Spec field: <spec field>. Expected parent '<parent>' with a real array value.
       Fix tasks.md input-values; do not pass [*] keys to case spec.
```

The CLI can accept that JSON and validation can pass, but the runtime request body is malformed. Repeat the key scan against the normalized `data.inputs` subtree after the raw-cache splice.

## Server-side FilterTree

### Filter planning

Only `spec.filter` with `builder: "ceql"` authorizes a server-side activity filter. Choose every leaf `id` from `spec.filter.fields[].name` and, when supplied, its operator from that field's `searchableOperators`. Author the structured tree under the T-entry's `filter:` field using the Case-local [FilterTree schema and validation rules](../../../case-spec-input-details.md#filtertree-shape). Emit `groupOperator` even for one clause.

If `spec.filter` is absent, do not invent a server filter; filter downstream. Do not write raw CEQL into `queryParameters` and do not pass derived `ceqlExpression` in `--input-details`.

### Step 4 — FilterBuilder detection

When the T-entry has `filter:`, re-check that the resolved spec exposes `builder: "ceql"`, then pass the complete structured tree as `--input-details.filter`. The CLI authors both the runtime CEQL sink in the query-parameter input and the design-time `savedFilterTrees` entry inside the metadata configuration. Preserve both from the raw cache; never patch either sink after the spec call or parse/rewrite the `=jsonString:` configuration value.

## Multipart file inputs

### Multipart planning

For every `inputs.multipart.parameters[]` entry with `isFile: true`, use its exact case-sensitive `name` as a `file-inputs` key and map it only to the complete `=vars.<id>` reference of an existing file-typed Case variable. Record the mapping outside `input-values` so it survives planning without being mistaken for an HTTP body/query/path parameter:

```markdown
- file-inputs: {"file":"=vars.evidenceDoc"}
```

Emit one mapping per file parameter. Do not map a file subfield, literal, URL, path, or free-form expression. Halt if the referenced Case variable is absent or is not `type: file`.

### Step 7.a — Multipart file binding

After reading the activity's raw cache and normalizing `Data.CaseShape.Inputs`, resolve every `file-inputs` key to exactly one emitted input whose preserved `name` equals that key and whose `target` is the literal string `"file"`. Halt on a missing, duplicate, or extra `target: "file"` entry; never match by array position. For each match:

- preserve `target: "file"`; never prefix it with `=`;
- copy the mapped whole-record `=vars.<id>` reference unchanged into `value`;
- mint only the normal activity input `var`, `id`, and task `elementId`; and
- preserve every CLI-emitted key. Do not synthesize `source`, `body`, or `displayName` when absent.

The full JobAttachment record is the multipart value; `=vars.<id>.FullName` and other subfield references are invalid for the file sink.

## Branch verification

- Array branch: no object key in the final activity input subtree contains literal `[*]`.
- Filter branch: the T-entry carried a structured FilterTree, the spec supported CEQL, and both CLI-authored sinks were preserved.
- Multipart branch: `file-inputs` and emitted `target: "file"` entries match one-to-one by exact name; each carries its recorded whole-record `=vars.<id>` value and no invented schema fields.
