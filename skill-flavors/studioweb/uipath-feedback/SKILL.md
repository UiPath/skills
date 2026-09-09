<!--skill-flavor:feedback-description-budget:start-->
Truncate the full description to 16000 characters max. Note if content was truncated. Studio Web feedback carries no attachments, so key file excerpts ride inline in the description — that is why the budget is larger here.
<!--skill-flavor:feedback-description-budget:end-->

<!--skill-flavor:feedback-prepare-attachments:start-->
#### Inline key file excerpts (no attachments in Studio Web)

`uip feedback send` does not support `--attachment` in Studio Web. Instead, inline the most relevant sanitized excerpts directly in the description under a final `## Key file excerpts` section, based on the detected area:

- Flow: the `.flow` file
- RPA: `project.json`, the failing workflow file (`.cs` or `.xaml`)
- Agents: `pyproject.toml`, `bindings.json` (redacted)
- CodedApps: `package.json`

Put each excerpt in a fenced code block headed by its file path. Apply the Sanitization Rules and truncation limits (first 100 + last 30 lines per file) before inlining, and keep the whole description within the character budget — prefer the failing region of a file over its beginning when trimming.
<!--skill-flavor:feedback-prepare-attachments:end-->

<!--skill-flavor:feedback-preview:start-->
```
**Type:** bug
**Priority:** normal
**Title:** [Flow] [CLI] Expression error in nested loop currentItem
**Description:** (first 3 lines...)
**Inlined excerpts:** MyFlow.flow, project.json

Send this to UiPath? (yes/no)
```
<!--skill-flavor:feedback-preview:end-->

<!--skill-flavor:feedback-send-command:start-->
```bash
uip feedback send \
  --type "<bug|improvement>" \
  --title "<TITLE>" \
  --description-file "/tmp/uip-feedback/description.md" \
  --priority "<critical|normal|minor>" \
  --output json
```

Do not pass `--attachment` — Studio Web rejects it before anything is sent.
<!--skill-flavor:feedback-send-command:end-->

<!--skill-flavor:feedback-cleanup-attachments:start-->
Clean up the temp description file:

```bash
rm -rf /tmp/uip-feedback
```
<!--skill-flavor:feedback-cleanup-attachments:end-->

<!--skill-flavor:feedback-cleanup-note:start-->
Always clean up the temp description file regardless of success or failure.
<!--skill-flavor:feedback-cleanup-note:end-->
