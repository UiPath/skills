# NewEventCreated

**Integration trigger** (`isTrigger: true, triggerType: "integration"` from `uip rpa activities find`; requires a `ConnectionId` to a Google Calendar connection). **Placement: strict** — first activity of `Main.xaml`'s root `Sequence`, never inside `ui:TriggerScope`. Orchestrator + Integration Service subscribe externally and dispatch a fresh job per calendar event. See [trigger-pattern-guide.md](../../../../trigger-pattern-guide.md).

Fully qualified name: `UiPath.GSuite.Activities.Calendar.Triggers.NewEventCreated`

Key attributes:
- `BrowserCalendarFriendlyName` — display name of the calendar to watch
- Output: `Result` as `UiPath.GSuite.Calendar.Models.GSuiteEventItem`, `JobData` as `UiPath.GSuite.Activities.Utilities.JobInformation`
