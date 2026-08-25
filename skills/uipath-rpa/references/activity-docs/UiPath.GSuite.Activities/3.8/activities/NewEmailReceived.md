# NewEmailReceived

**Integration trigger** (`isTrigger: true, triggerType: "integration"` from `uip rpa activities find`; requires a `ConnectionId` to a Gmail connection). **Placement: strict** — first activity of `Main.xaml`'s root `Sequence`, never inside `ui:TriggerScope`. Orchestrator + Integration Service subscribe externally and dispatch a fresh job per email. See [trigger-pattern-guide.md](../../../../trigger-pattern-guide.md).

Fully qualified name: `UiPath.GSuite.Activities.Gmail.Triggers.NewEmailReceived`

Key attributes:
- `Filter` — child element with `LogicalOperator` and `Criteria`/`StringValue` conditions
- `IncludeAttachments` — `"True"` / `"False"`
- `MarkAsRead` — `"True"` / `"False"`
- `WithAttachmentsOnly` — `"True"` / `"False"`
- Output: `Result` as `UiPath.GSuite.Models.GmailMessage`, `JobData` as `UiPath.GSuite.Activities.Utilities.JobInformation`
