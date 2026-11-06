# File Inspection for Coded-Agent Guardrails (`detection_scope`)

Built-in guardrails in a coded agent can inspect the files a run carries — `Attachment` inputs, files tools return, and files the agent produces — in addition to text. Writing patterns (imports, middleware spread, decorator placement, wiring checks) are in [guardrails.md](guardrails.md); this guide covers only what changes for files. Low-code equivalent: [../../../lowcode/capabilities/guardrails/files-guide.md](../../../lowcode/capabilities/guardrails/files-guide.md).

> **Important: BYO (bring-your-own) guardrails have no file support.** `UiPathByoGuardrailMiddleware` and `ByoValidator` accept `detection_scope`, but BYO guardrails evaluate text only; the files are never read. Do not set it on them.

## The `detection_scope` argument

```python
from uipath_langchain.guardrails import DetectionScope   # non-LangChain agents: uipath.platform.guardrails
```

| Value | Evaluates |
|---|---|
| `DetectionScope.TEXT` (`"Text"`) | Text only; no files |
| `DetectionScope.FILES` (`"Files"`) | Files only; the text is not evaluated |
| `DetectionScope.BOTH` (`"Both"`) | Text and files |

1. Pass it on `@guardrail(...)` or on the middleware constructor (`UiPathPIIDetectionMiddleware`, `UiPathHarmfulContentMiddleware`, `UiPathUserPromptAttacksMiddleware`, `UiPathIntellectualPropertyMiddleware`, `UiPathLLMAsJudgeMiddleware`). Validator constructors (`PIIValidator(...)` and the rest) have no such argument.
2. The default is always text only: omitting `detection_scope` (or passing `None`) inspects no files, for every validator.
3. Set it only when the validator's entry from the tenant check in [guardrails.md](guardrails.md#check-tenant-availability-mandatory-for-built-in-ai-validators) lists `detectionScope` in `Parameters`. Absent means file inspection is not enabled for that validator on this tenant, and a `Files` guardrail there silently evaluates the text instead. Tell the user rather than adding it.
4. Use the enum or the exact strings `"Text"`, `"Files"`, `"Both"`; any other value raises `ValueError` when the module is imported.
5. `UiPathDeterministicGuardrailMiddleware` has no `detection_scope` (passing it raises `TypeError`); `CustomValidator` ignores it. Deterministic rules never read file contents.
6. Scopes and stages do not change: intellectual property stays Agent / LLM · POST; user prompt attacks stays LLM · PRE. `@guardrail` defaults to `PRE_AND_POST`, so pass `stage=` for those validators.
7. Requires `uipath-langchain>=0.18.53`. A non-LangChain agent that uses `@guardrail` from `uipath.platform.guardrails` needs `uipath-platform>=0.2.43` in its own dependencies.

## Make the file visible to the guardrails

Guardrails only inspect files that appear in the run in one of these shapes:

| Where the file is | What to write |
|---|---|
| Typed input `file: Attachment` | Render it into the user message with `render_attachments_block` (below). A typed input that is not rendered is never inspected |
| Tool arguments and results | An `Attachment` or a `{"ID", "FullName", "MimeType"}` object — never a bare id string |
| Conversational agent | Nothing; the runtime attaches each user file to its message |

```python
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from uipath.platform.attachments import Attachment
from uipath_langchain.guardrails import render_attachments_block


class Input(BaseModel):
    file: Attachment


async def main(state: Input):
    attachment = state.file.model_dump(mode="json", exclude_none=True)
    prompt = f"Review the attached file.\n{render_attachments_block([attachment])}"
    result = await agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
    return result["structured_response"]
```

Never inspected: base64 content blocks you build yourself, URLs, and files mentioned only in the system prompt. At most 5 files per check.

## What each check reads

| Guardrail | Reads |
|---|---|
| Middleware · Agent or LLM · PRE | Every file the run holds |
| Middleware · Tool · PRE | Only the files the tool arguments name, and only if the run already holds them |
| Middleware · any POST | The files the output names (the model message, tool result, or structured response) |
| Decorator on a tool | The files its arguments describe, taken as given (the run is not checked) |
| Decorator on the LLM factory | Every file in the messages |
| Decorator on an agent factory or graph | The files in the input messages; an input without a `messages` key is not checked |

The SDK docs carry the full tables: [middleware](https://uipath.github.io/uipath-python/langchain/guardrails/#files-attachments), [decorator](https://uipath.github.io/uipath-python/langchain/guardrails/#files).

## Choosing Text, Files, or Both

| Situation | Use |
|---|---|
| No `Attachment` input or output and no tool that takes or returns a file | omit (text only) |
| A Tool-scope guardrail whose tools neither take nor return a file | omit at that guardrail; Tool · PRE reads only the files the arguments name |
| Guard the contents of uploaded files; the surrounding text is irrelevant or could sway a judge | `Files` |
| Guard a file the agent produces | `Files` at Agent scope — Recipe 3 |
| Text and files are both threat surfaces and one guardrail should cover both | `Both` |

## Recipes

### Recipe 1 — Uploaded files, middleware

Agent · PRE stops a harmful file before the model runs; user prompt attacks checks every model call.

```python
from langchain.agents import create_agent
from uipath.core.guardrails import GuardrailScope
from uipath_langchain.guardrails import (
    BlockAction,
    DetectionScope,
    GuardrailExecutionStage,
    HarmfulContentEntity,
    UiPathHarmfulContentMiddleware,
    UiPathUserPromptAttacksMiddleware,
)
from uipath_langchain.guardrails.enums import HarmfulContentEntityType

agent = create_agent(
    model=llm,
    tools=[...],
    middleware=[
        *UiPathHarmfulContentMiddleware(
            name="Harmful content in attached files",
            scopes=[GuardrailScope.AGENT],
            stage=GuardrailExecutionStage.PRE,
            action=BlockAction(detail="An attached document contains harmful content."),
            entities=[HarmfulContentEntity(HarmfulContentEntityType.VIOLENCE, threshold=2)],
            detection_scope=DetectionScope.FILES,
        ),
        *UiPathUserPromptAttacksMiddleware(
            name="Prompt attacks in attached files",
            action=BlockAction(detail="An attached document contains hidden instructions."),
            detection_scope=DetectionScope.FILES,
        ),
    ],
)
```

### Recipe 2 — A tool that takes a file, decorator

```python
# standard imports omitted
from uipath_langchain.guardrails import LLMAsJudgeValidator, guardrail


@guardrail(
    validator=LLMAsJudgeValidator(
        guardrail_text="Fail if the file <CONDITION_TO_BLOCK>.",
        model="<JUDGE_MODEL_ID>",
    ),
    action=BlockAction(detail="<REASON_SHOWN_ON_BLOCK>"),
    name="<GUARDRAIL_NAME>",
    stage=GuardrailExecutionStage.PRE,
    detection_scope=DetectionScope.FILES,
)
@tool
def screen_invoice(invoice: Attachment) -> str:
    """Screen the uploaded invoice."""
    ...
```

`<JUDGE_MODEL_ID>` comes from `uip agent guardrails llm-as-judge-models --output json`. A tool created by a factory instead of `@tool` is decorated by calling the decorator: `guardrail(...)(create_analyze_file_tool(...))`.

### Recipe 3 — A file the agent produces

Declare the file in the output (`file: Attachment | None` on the `Output` model), fill it with the object a tool returned for the created file, and guard it at Agent scope; Agent · POST reads the files the structured response names.

```python
# standard imports omitted
from uipath_langchain.guardrails import UiPathIntellectualPropertyMiddleware
from uipath_langchain.guardrails.enums import IntellectualPropertyEntityType

*UiPathIntellectualPropertyMiddleware(
    name="Protected code in output files",
    scopes=[GuardrailScope.AGENT],
    action=BlockAction(detail="A file the agent produced contains protected code."),
    entities=[IntellectualPropertyEntityType.CODE],
    detection_scope=DetectionScope.FILES,
),
```

Prove it in a job run (for example a robot debug run): under a plain local `uipath run`, a created file stays in local storage the guardrail cannot read.

## Behaviour to expect

- Files never fail the run: an unreadable, oversize, or unsupported file is skipped and the guardrail evaluates what remains.
- A `Files` guardrail with no file to read passes; a `Both` guardrail still evaluates the text.
- If the platform rejects the file references, the check runs once more on the text only and logs a warning.
- Filter and redact actions rewrite text only; for `Files` use `BlockAction`, `LogAction`, or `EscalateAction`.
- A tool that reads file contents with a model (such as Analyze Files) needs `UiPathChatOpenAI` today: the normalized `UiPathChat` fails with `Missing required parameter … file`. The agent's own model can stay `UiPathChat`.
- File types, size caps, and page limits are the same as for low-code agents: [Supported types and caps](../../../lowcode/capabilities/guardrails/files-guide.md#supported-types-and-caps).

## Testing with files

A live test uploads a file to the tenant. Run one only when the user wants it, never after they said not to upload or publish.

1. Upload a real file with the SDK — `uip` has no upload verb:

   ```python
   from uipath.platform import UiPath

   attachment_id = await UiPath().attachments.upload_async(name="<FILE_NAME>", source_path="<FILE_PATH>")
   ```

2. Run the agent with the file reference as input:

   ```bash
   uv run uipath run agent '{"file": {"ID": "<ATTACHMENT_ID>", "FullName": "<FILE_NAME>", "MimeType": "<MIME_TYPE>"}}'
   ```

   The placeholder-attachment pattern in [../file-attachments.md](../file-attachments.md) § Local Testing does not exercise file guardrails: the guardrail reads the file from the platform by its id.
3. Upload again for every run you compare; file content is cached by id for a few minutes.
4. Prove a verdict with a control run: the same file with `detection_scope=DetectionScope.TEXT`.

## What NOT to Do

1. **Do not set `detection_scope` on BYO, deterministic, or `CustomValidator` guardrails** — BYO reads no files, deterministic middleware raises `TypeError`, and `CustomValidator` ignores it.
2. **Do not pass `detection_scope` to a validator constructor** — it belongs on `@guardrail(...)` or the middleware.
3. **Do not add it when `uip agent guardrails list` does not offer `detectionScope` for that validator** — the guardrail silently checks text only.
4. **Do not expect a typed `Attachment` input to be inspected on its own** — render it into the user message with `render_attachments_block`.
5. **Do not pass bare id strings where a file belongs** — tool arguments and results need the `{"ID", "FullName", "MimeType"}` object.
6. **Do not use Filter or redact actions for `Files`** — they cannot rewrite a file.
7. **Do not test a file guardrail with a placeholder attachment** — upload a real file.

## References

- [guardrails.md](guardrails.md) — imports, middleware and decorator patterns, wiring checks
- [guardrails-recommend.md](guardrails-recommend.md) — when to recommend `detection_scope`, validate-mode checks
- [../file-attachments.md](../file-attachments.md) — `Attachment` input and output, reading file bytes
- SDK docs: [langchain/guardrails](https://uipath.github.io/uipath-python/langchain/guardrails/#files-attachments), [core/guardrails](https://uipath.github.io/uipath-python/core/guardrails/#files-attachments)
- Runnable sample: [samples/cv-screener-agent](https://github.com/UiPath/uipath-langchain-python/tree/main/samples/cv-screener-agent) in the uipath-langchain repo
