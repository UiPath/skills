# SendEmailConnections

Key attributes:
- `To`, `Cc`, `Bcc` — `IEnumerable<string>` (use `new string[]{"a@b.com"}` in CSharpValue)
- `Subject`, `Body` — string values
- `InputType` — `"HTML"` or `"PlainText"`
- `Importance` — enum (Normal / High / Low)
- `SaveAsDraft` — `"True"` / `"False"`
- `AttachmentInputMode` — `"Existing"` or other modes
