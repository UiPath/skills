# Files & Base64 in API Workflows

How an API workflow handles files, and how the **File to Base64** / **Base64 to File** activities work — the JSON to write, the runtime behavior to expect, and how to run such a workflow from the CLI.

## 1. A file is a reference, not bytes

Every file an API workflow touches is a `JobAttachment`: a small object pointing at a blob in Orchestrator storage.

```json
{
  "ID": "6f1c0d2e-8a1b-4c3d-9e0f-123456789abc",
  "FullName": "invoice.pdf",
  "MimeType": "application/pdf",
  "Metadata": { "Size": 48213, "Encoding": "byte-array" }
}
```

| Field | Meaning |
|---|---|
| `ID` | Attachment key in Orchestrator (GUID) |
| `FullName` | File name with extension |
| `MimeType` | Content type |
| `Metadata.Size` | Byte length, when known |
| `Metadata.Encoding` | `"byte-array"` (binary — the default) or `"base64"` (the blob's content is base64 *text*). A tag only: nothing is converted when reading |

Consequences:
- A file input declared in `input.schema` (`"$ref": "#/definitions/job-attachment"`, `x-uipath-resource-kind: "JobAttachment"`) arrives as this object: `$workflow.input.document.FullName` works; there is no `.content`.
- File bytes never enter `$context`, so context stays small no matter how big the file is.
- Everything that reads or writes files goes through Orchestrator blob storage, so it needs a signed-in session.

## 2. The two activities

Both are ordinary `run.script` tasks. What makes them *these* activities — for Studio Web's designer, for `uip api-workflow validate`, and for the engine — is `metadata.activityType` plus the `$helpers.file.*` call in the script. Studio Web restores the property panel by parsing that call, so keep the exact shape.

### File to Base64 (`FileToBase64`)

`await $helpers.file.fileToBase64(<file ref>)` → a **new** reference whose blob content *is* the base64 text: `<baseName>.base64`, `text/plain`, `Metadata.Encoding: "base64"`. Idempotent for an already-base64 reference. Input must be a reference (a string is a validation error).

```json
{
  "FileToBase64_1": {
    "run": {
      "script": {
        "code": "return { output: await $helpers.file.fileToBase64($workflow.input.document) }",
        "language": "javascript",
        "arguments": "${{ \"$context\": $context, \"$workflow\": $workflow, \"$input\": $input }}"
      }
    },
    "export": { "as": "{ ...$context, outputs: { ...$context?.outputs, \"FileToBase64_1\": $output } }" },
    "metadata": { "activityType": "FileToBase64", "displayName": "File to Base64", "fullName": "FileToBase64", "icon": "sw:convert-file-to-base64" }
  }
}
```

Downstream: `$context.outputs.FileToBase64_1.output` (a `JobAttachment`).

### Base64 to File (`Base64ToFile`)

`await $helpers.file.base64ToFile({ base64, fileName?, mimeType? })` → a **new binary** reference.
- `base64` is a base64 file reference (from File to Base64) **or** a raw base64 string (an API response field, a variable).
- `fileName` / `mimeType` apply only to a **string** input. Omitted → MIME sniffed from the bytes, unique GUID-based name, extension from the MIME type. For a reference input they are ignored: the engine strips `.base64` and sniffs the type (plain text has no signature, so a `.txt` comes back extension-less as `application/octet-stream`).
- A reference that is **not** tagged `Encoding: "base64"` (a plain binary file) is returned unchanged — there is nothing to decode. Chaining Base64 to File directly on a raw file input is therefore a no-op, not an error.
- Omit the optional keys when unset — `fileName: ` with no value is a syntax error.

```json
{
  "Base64ToFile_1": {
    "run": {
      "script": {
        "code": "return { output: await $helpers.file.base64ToFile({ base64: $context.outputs.HTTP_Request_1.content.data, fileName: 'invoice.pdf', mimeType: 'application/pdf' }) }",
        "language": "javascript",
        "arguments": "${{ \"$context\": $context, \"$workflow\": $workflow, \"$input\": $input }}"
      }
    },
    "export": { "as": "{ ...$context, outputs: { ...$context?.outputs, \"Base64ToFile_1\": $output } }" },
    "metadata": { "activityType": "Base64ToFile", "displayName": "Base64 to File", "fullName": "Base64ToFile", "icon": "sw:convert-base64-to-file" }
  }
}
```

A disabled activity gets `"if": "${false}"` on the task, like any other.

## 3. Getting a file's *content* into a request or a Response: `serializeData()`

`fileToBase64` gives you a file, not a string. To send the base64 text to an API, call `serializeData()` on the reference **inside the HTTP body or the Response expression**:

```json
"bodyParameters": { "body": "${{ name: $workflow.input.document.FullName, content: $context.outputs.FileToBase64_1.output.serializeData() }}" }
```

```json
"response": "${{ encoded: $context.outputs.FileToBase64_1.output.serializeData() }}"
```

`serializeData()` is synchronous and returns a small deferred-read marker (`{ "__uipathFileRead": { "ref": … } }`); the engine replaces it with the file's content when the request is sent / the Response leaves the run. Rules:
- Use it **only** inline in an HTTP body or a Response field.
- Do **not** assign it to a variable, return it from a script, or run logic on it — you would keep the marker, not the content.
- **Nested in a JSON body field, only a base64 reference works** (the File to Base64 output). A `serializeData()` marker on a *binary* reference nested in a body fails at send time with `Raw bytes cannot be embedded in JSON — convert the file with File to Base64 first`, and a *bare* reference nested in a body fails with `A bare file reference cannot be embedded in a nested field`. So: `content: $workflow.input.document.serializeData()` is wrong; `content: $context.outputs.FileToBase64_1.output.serializeData()` is right.
- To send a binary file **as-is**, make the bare reference the *whole* HTTP body — it is sent as the file's bytes with its `MimeType` as `Content-Type` (no `serializeData()` needed).
- In a Response, markers are resolved anywhere; bare references are returned as references.

## 4. A complete round trip

[assets/templates/file-base64-roundtrip-example.json](../assets/templates/file-base64-roundtrip-example.json): `document` file input → `FileToBase64_1` → `Base64ToFile_1` → `Response_1` returning both references. The typical real-world chain is `File to Base64 → HTTP POST (body uses .serializeData()) → Base64 to File (vendor's base64 response string, with fileName/mimeType) → Response`.

## 5. Running a workflow that uses files

<!--skill-flavor:file-inputs-cli:start-->
Files live in Orchestrator blob storage, so the run needs a session — `uip api-workflow run --no-auth` refuses a workflow that calls `$helpers.file.*` before the engine starts (and refuses `--input-file` / `--output-dir`). Rule 21 still applies: ask before running.

```bash
uip login                                  # once
uip api-workflow run ./MyApiProject/Workflow.json \
  --input-file document=./invoice.pdf \    # upload → $workflow.input.document (repeatable)
  --output-dir ./out \                     # download every reference in the output
  --output json
```

- `--input-file <name>=<path>`: the local file is uploaded (MIME type from the extension) and the reference is placed under `<name>` in the input — exactly what Studio Web's run panel produces.
- `--output-dir <dir>`: every `JobAttachment` in the output is downloaded into `<dir>`; the printed reference gains `LocalPath`. Same-named blobs get an `-<Id>` suffix.
- `--folder-key <guid>`: when the tenant's Attachments API requires a folder.
- The CLI PascalCases printed keys: `ID` → `Id`, `encoded` → `Encoded`.

Example output:

```json
{
  "Result": "Success",
  "Code": "WorkflowRun",
  "Data": {
    "Encoded": { "Id": "…", "FullName": "hello.base64", "MimeType": "text/plain", "Metadata": { "Size": 72, "Encoding": "base64" }, "LocalPath": "/abs/out/hello.base64" },
    "Decoded": { "Id": "…", "FullName": "hello", "MimeType": "application/octet-stream", "Metadata": { "Size": 54, "Encoding": "byte-array" }, "LocalPath": "/abs/out/hello" }
  }
}
```

`uip api-workflow validate` covers these activities offline: it accepts `FileToBase64` / `Base64ToFile` and rejects a task of either type whose script does not call its `$helpers.file.*` function.
<!--skill-flavor:file-inputs-cli:end-->

## 6. Limits and gotchas

- **Size:** file references have no practical size cap — a reference with a declared `Metadata.Size` above 1 MB, or with **no** declared size (common for job inputs), streams with bounded memory at any size. Only in-memory inputs are capped at 50 MB per conversion: a raw base64 *string*, or a reference small enough to be buffered.
- **Namespace:** `$helpers.fileToBase64` (no `.file.`) fails with `is not a function` and fails `validate`.
- **Invalid base64:** a `data:…;base64,` prefix and whitespace/line breaks are **tolerated** (stripped before decoding). What is rejected with `The provided value is not a valid base64 string: <task name>`: the URL-safe alphabet (`-` / `_`), other non-base64 characters, bad padding, and an empty string.
- **Names:** `fileName` / `mimeType` never rename a reference input; a decoded text file loses its extension.
- **Preview feature:** in Studio Web the two activities sit behind the `FE.EnableBase64Activities` flag and are marked "in preview".

Pitfalls with symptoms and fixes: [troubleshooting.md](troubleshooting.md#file--base64-pitfalls).
