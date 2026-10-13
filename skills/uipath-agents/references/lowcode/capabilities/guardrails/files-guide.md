# File and Attachment Inspection (`appliesTo`)

Built-in validators can inspect the files a run carries — `job-attachment` inputs, files tools return, and files the agent produces — in addition to text. Base schema, selector scoping, validator discovery, and actions are in [guardrails.md](guardrails.md); read its Overview and Walkthrough first. This guide owns the `appliesTo` parameter, what each scope sees, supported types and caps, and the file recipes. Custom (deterministic) guardrails never read file contents — see § What NOT to Do.

> **Important: BYO (bring-your-own) guardrails have no file support.** A guardrail pinned with `byoValidatorName` sends the text payload only, whatever `appliesTo` says, and BYO entries in `uip agent guardrails list` carry no `appliesTo` parameter. File inspection applies to UiPath's built-in implementations only.

## The `appliesTo` parameter

Optional `validatorParameters` entry on file-capable built-in validators:

```json
{ "$parameterType": "enum", "id": "appliesTo", "value": "Files" }
```

| `value` | Studio Web label | Provider receives |
|---|---|---|
| `Text` | Text only | Text payload only; no files |
| `Files` | Files only | Files only; the text payload is dropped server-side |
| `Both` | Text and files | Text payload plus files |

1. Set `appliesTo` only when the validator's entry in `uip agent guardrails list --output json` has a `Parameters[]` item with `Id: "appliesTo"`. Absent means file inspection is not enabled for that validator on this tenant (the Studio Web card reads "Text prompts only"); the runtime evaluates text only. Do not add the parameter anyway.
2. Omitted `appliesTo` defaults to `Text` for `pii_detection`, `prompt_injection`, `harmful_content`, `intellectual_property`, `user_prompt_attacks`, and to `Both` for `llm_as_judge`. Any unrecognised value narrows to `Text`.
3. `appliesTo` changes nothing about scopes or stages: `prompt_injection` and `user_prompt_attacks` stay Llm · Pre; `intellectual_property` stays Agent/Llm · Post; the others stay Agent/Llm/Tool · Pre+Post. There is no stage picker — the runtime decides per validator.
4. `appliesTo` is not `applyTo`. `applyTo` (`input` | `output` | `inputAndOutput`) belongs to the custom `always` rule in [custom-rules-guide.md](custom-rules-guide.md); custom guardrails have no `validatorParameters`.
5. Values are exact: `Text`, `Files`, `Both` — never lowercase.

## Choosing Text, Files, or Both

| Situation | Use |
|---|---|
| No `job-attachment` input or output and no file tool | omit (`Text`) |
| Guard the contents of attached input files; surrounding text is irrelevant or could sway a judge | `Files` |
| Guard a file the agent produces (`job-attachment` output) | `Files` at Agent scope — Recipe 3 |
| Text and files are both threat surfaces and one guardrail should cover both | `Both` |
| `llm_as_judge` on a file-taking agent | `Files` unless the rule needs the text — its default `Both` feeds text that can change the verdict |

## What each scope and stage inspects

Files sent to the provider when `appliesTo` is `Files` or `Both`:

| Scope · stage | Files evaluated |
|---|---|
| Agent · Pre | The run's job attachments: input files plus files tools already returned (max 5) |
| Agent · Post | Files the agent's result references (`job-attachment` outputs) |
| Llm · Pre | Every file registered in the run so far |
| Llm · Post | Files referenced by the model's tool-call arguments |
| Tool · Pre | Only files named in that tool call's arguments (for example Analyze Files `attachments[]`) |
| Tool · Post | Only files the tool result references; a prose result (Analyze Files `analysis`) carries none |

<!-- transitional: remove when output-file verification is generally available -->
> Runtimes that predate output-file verification send every registered file at Agent · Post and Llm · Post, and a `Files` guardrail with nothing to read falls back to evaluating the text payload. Current runtimes pass that evaluation without a provider call (`Allowed: no files were supplied to evaluate.`).

## How each validator consumes files

| Validator | File handling |
|---|---|
| `llm_as_judge` | Text files inlined into the judge prompt; PDF and images sent as vision parts — images are judged only when `model` is vision-capable |
| `user_prompt_attacks` | Each file is a `documents[]` entry (indirect-injection check) |
| `pii_detection` | One document per file; entity thresholds apply per document |
| `harmful_content`, `intellectual_property`, `prompt_injection` | Extracted text appended to the input as `[file: <FILE_NAME>] …` |

## Supported types and caps

| Category | Types |
|---|---|
| Decoded directly | `txt`, `csv`, `md`, `tsv`, `json`, `xml` |
| Text extraction (when enabled on the tenant) | `pdf`, `jpeg` / `png` / `bmp` / `tiff` / `heif`, `docx` / `xlsx` / `pptx`, `html` |
| Unsupported | Legacy `doc` / `xls`; files whose content is binary |

Caps per evaluation: 5 files; 5 MB per text file, 10 MB of binaries in total; 100,000 extracted characters in total; 20 pages per document. Hidden text (white-on-white PDF text) is dropped by extraction; images embedded in Office files are not read.

Files never fail the run. An unreadable, oversize, or unsupported file is skipped and the guardrail evaluates what remains. When the provider can attribute a hit, the Block reason ends with `Flagged files: <FILE_NAME>, <FILE_NAME>`.

## Recipes

### Recipe 1 — Guard attached input files

Shape: a `job-attachment` input field ([../../agent-definition.md](../../agent-definition.md) § File Attachments) plus a `Files` guardrail at Agent scope. Agent · Pre blocks before the model or any tool runs.

```json
{
  "$guardrailType": "builtInValidator",
  "id": "<UUID>",
  "name": "PII in uploaded documents",
  "description": "Blocks runs whose attached files contain customer identifiers",
  "validatorType": "pii_detection",
  "validatorParameters": [
    { "$parameterType": "enum-list", "id": "entities", "value": ["Email", "CreditCardNumber"] },
    { "$parameterType": "map-enum", "id": "entityThresholds", "value": { "Email": 0.5, "CreditCardNumber": 0.5 } },
    { "$parameterType": "enum", "id": "appliesTo", "value": "Files" }
  ],
  "action": { "$actionType": "block", "reason": "An attached file contains personal data." },
  "enabledForEvals": true,
  "selector": { "scopes": ["Agent"] }
}
```

1. Run `uip agent guardrails list --output json`; confirm `Status: "Available"` and an `appliesTo` entry in `Parameters` for the validator.
2. Reference the file field in the user message — `{{input.<FILE_FIELD>}}` in `content` with the matching `variable` token in `contentTokens` (Studio Web inserts it with `@`). The token renders metadata only; an unreferenced input still reaches an Agent-scope guardrail, but the model never knows the file exists.
3. In the system prompt, instruct the model to read files with Analyze Files and never to judge a file by its name.
4. Add the guardrail to the `agent.json` root `guardrails[]`, then run `uip agent refresh "<AGENT_NAME>" --output json` and `uip agent validate "<AGENT_NAME>" --output json`.

### Recipe 2 — Tool scope on Analyze Files

Use when only the files handed to Analyze Files matter (for example the agent also receives files it must not read, or the rule is about what the tool is asked to read).

```json
{
  "$guardrailType": "builtInValidator",
  "id": "<UUID>",
  "name": "Non-compete judge",
  "description": "Blocks contracts with a non-compete longer than 12 months",
  "validatorType": "llm_as_judge",
  "validatorParameters": [
    { "$parameterType": "enum", "id": "model", "value": "<MODEL_ID>" },
    { "$parameterType": "text", "id": "guardrailText", "value": "Fail if the contract in {{content}} contains a non-compete clause longer than 12 months. A summary or analysis of a contract passes." },
    { "$parameterType": "enum", "id": "appliesTo", "value": "Files" }
  ],
  "action": { "$actionType": "block", "reason": "Non-compete exceeds 12 months." },
  "enabledForEvals": true,
  "selector": { "scopes": ["Tool"], "matchNames": ["Analyze Files"] }
}
```

1. `matchNames` carries the tool's `resource.json` → `name` (`"Analyze Files"`), not the folder name. Confirm with `uip agent tool list --output json`.
2. Pre evaluates the files in `attachments[]`; Post evaluates only the prose `analysis`. For `llm_as_judge` rules written for files, keep a PASS clause for plain-text summaries (as above) so the Post pass does not block the tool's own output.
3. `model` comes from `uip agent guardrails llm-as-judge-models --output json` ([guardrails.md](guardrails.md) § Validators Quick Reference); PDF and image files need a vision-capable model.
4. Keep the guardrail in the root `guardrails[]`; leave the tool's `guardrail.policies` empty on autonomous agents ([guardrails.md](guardrails.md) § Conversational Support is the only mirroring case).

### Recipe 3 — Guard a file the agent produces

Checks the content of an output file (generated code, a report), not the agent's text answer.

1. Declare an output field as `$ref: "#/definitions/job-attachment"` with the canonical block in `outputSchema.definitions` ([../../agent-definition.md](../../agent-definition.md) § File Attachments).
2. Add the **Create File** built-in tool ([../built-in-tools/create-file.md](../built-in-tools/create-file.md)) unless another tool on the agent already returns a `job-attachment`, and name the deliverable file and its output field in the system prompt (the runtime adds the how-to-fill-a-file-field instructions itself). If `uip agent tool list` and the Studio Web tool picker offer no Create File tool, or the run fails at startup with `The Create File tool is not supported in this environment`, output files are not available on this tenant — remove the tool and guard the text output instead.
3. Add a Post-capable validator at **Agent** scope with `appliesTo: "Files"`. Prefer Agent over Llm: at Llm scope the file is still the Create File `content` argument — plain text, not a file.

```json
{
  "$guardrailType": "builtInValidator",
  "id": "<UUID>",
  "name": "Protected code in output files",
  "description": "Blocks the run when a produced file contains licensed code",
  "validatorType": "intellectual_property",
  "validatorParameters": [
    { "$parameterType": "enum-list", "id": "ipEntities", "value": ["Code"] },
    { "$parameterType": "enum", "id": "appliesTo", "value": "Files" }
  ],
  "action": { "$actionType": "block", "reason": "A file the agent produced contains protected code." },
  "enabledForEvals": true,
  "selector": { "scopes": ["Agent"] }
}
```

### Recipe 4 — Flow inline agents

An inline agent in a Flow carries the same `guardrails[]` (its sidecar is a projected `agent.json`); `appliesTo`, the scope × stage table, and the caps apply unchanged. Author it in the Flow's `guardrails` array with the `uipath-maestro-flow` skill.

## Testing with files

1. Calibrate first with the file's text pasted as plain input (`appliesTo` omitted) to confirm the validator and thresholds fire; then switch to `Files` and run with the real file.
2. Run with a file bound to the input field — [../../debug.md](../../debug.md) § Attachments. To reuse an already-uploaded file, pass its reference in `--inputs` (`{"<FILE_FIELD>":{"ID":"<ATTACHMENT_ID>"}}`).
3. Read the verdict from the guardrail evaluation span (`reason`, `Flagged files:`) with `uip traces spans get <TRACE_ID> --output json`.
4. Evaluation sets and bulk validation run without attachments — a `Files` guardrail cannot be exercised there.

## Availability

| Environment | File inspection |
|---|---|
| Automation Cloud, Unified Runtime | Per validator, when `appliesTo` appears in the validator's `Parameters` in `uip agent guardrails list` |
| Automation Suite | Not available — guardrails evaluate text only |
| Legacy (non-Unified) agent runtime, eval runs, bulk validate | No files carried |
| BYO (`byoValidatorName`) guardrails | **Not available** — external providers receive no attachments |
| Advanced agents, coded agents | Not covered by this guide |

A tenant-wide AI Trust Layer policy (`uip gov aops-policy`, product `AITrustLayer`) has its own per-guardrail detection scope (`Text` / `Files` / `Both`), evaluated at the LLM Gateway on files carried inline in the model request. It is independent of the agent's `appliesTo` — both layers run and either can block. Author it with the `uipath-governance` skill.

## What NOT to Do

1. **Do not add `appliesTo` when the validator's `Parameters` lacks it** — `uip agent validate` passes, the runtime ignores it, and the guardrail silently checks text only.
2. **Do not set `appliesTo` on `$guardrailType: "custom"` or on validators that do not list it** — invalid parameter.
3. **Do not set `appliesTo: "Files"` or `"Both"` on a guardrail pinned with `byoValidatorName`** — BYO guardrails have no file support; the provider receives text only.
4. **Do not expect `Text` (the default outside `llm_as_judge`) to catch content inside an attachment** — file contents never reach the provider.
5. **Do not rely on a `Files` guardrail at Llm scope to inspect a produced file** — the model emits it as text until Create File stores it; use Agent scope.
6. **Do not put a `Files` guardrail at Tool scope on a tool whose arguments carry no files** — Tool · Pre sends only files named in the call, so it evaluates nothing.
7. **Do not let the model judge by file name** — require Analyze Files in the system prompt; `{{input.<FILE_FIELD>}}` is metadata only.
8. **Do not write `files` / `both` in lowercase** — the enum values are `Text`, `Files`, `Both`.

## References

- [guardrails.md](guardrails.md) — base schema, selector scoping, Validators Quick Reference, Example 6
- [guardrails-recommend.md](guardrails-recommend.md) — when to recommend `appliesTo`, validate-mode checks
- [custom-rules-guide.md](custom-rules-guide.md) — `always` rule `applyTo`
- [../../agent-definition.md](../../agent-definition.md) § File Attachments — `job-attachment` schema
- [../built-in-tools/analyze-attachments.md](../built-in-tools/analyze-attachments.md) — Analyze Files tool resource
- [../built-in-tools/create-file.md](../built-in-tools/create-file.md) — Create File tool resource (produced files)
- [../../debug.md](../../debug.md) § Attachments — running with files
- [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Critical Rules 17–19
