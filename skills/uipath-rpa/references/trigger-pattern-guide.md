# Trigger Pattern Guide

Authoring and editing trigger workflows in XAML. Covers placement, lifecycle, `ui:TriggerScope` handling, and verification.

## Two Trigger Types

`uip rpa activities find` returns `isTrigger` and `triggerType` on every trigger activity. `triggerType` is the type discriminator.

### Integration triggers (`triggerType: "integration"`) — strict placement

- **MUST be the first activity** of `Main.xaml`'s root `Sequence`.
- **CANNOT be placed inside `ui:TriggerScope`.**
- **Connection asset:** required for IS-based triggers (Mail, GSuite, O365, Salesforce, Jira, Slack, ServiceNow, any `*.IntegrationService.Activities` package). Not required for Orchestrator-native triggers (`TimeTrigger`, `QueueTrigger`, `ManualTrigger`).
- **Runtime behavior:** the activity is an **unwrap routine**. Orchestrator (or the IS webhook layer) holds the subscription, dispatches a fresh job per event, and injects event payload context. The activity's `Execute` reads that context — e.g., `NewEmailReceived.ExecuteWithRetryAsync` reads `UiPathEventObjectId`, then calls `GraphServiceClient.GetEmailByIdAsync(...)` to fetch the email. It does not poll, watch, or listen.
- **Examples:** `NewEmailReceived` (O365 Outlook, GSuite Gmail), `NewFileCreated`, `NewEventCreated`, `NewEventInvitationReceived`, `RowAddedToSheetBottom`, SharePoint list-item triggers, every IS connector trigger (Salesforce / Jira / Slack / ServiceNow / Microsoft Teams CRUD events), `TimeTrigger`, `QueueTrigger`, `ManualTrigger`.

### Local triggers (`triggerType: "local"`) — flexible placement

- Place EITHER:
  - As the first activity of `Main.xaml`'s root `Sequence` → Orchestrator dispatches a fresh job per event (entry-point semantics).
  - Inside `<ui:TriggerScope.Triggers>`, handler in `<ui:TriggerScope.Action>` → the robot stays alive while the scope is active; the trigger fires in-process.
- The placement choice is a runtime-model decision (per-event jobs vs long-running robot). Both are valid.
- **Connection asset:** not required.
- **Runtime behavior:** the activity is a real in-process subscriber. `StartMonitor` installs the listener (e.g. `FileChangeTriggerV3` → `FileSystemWatcher` + a background event-loop `Task` in `UiPath.Core.Activities.FileWatcher`); events flow through `TriggerScope`'s bookmark queue when wrapped, or through entry-point dispatch when placed at root.
- **Examples:** `FileChangeTriggerV3`, `RepeatTrigger`, `GlobalVariableChangedTrigger`, UIA Next triggers (`NClickTrigger`, `NKeyboardTrigger`), classic UIA V2 triggers (`ClickTriggerV2`, `ClickImageTriggerV2`, `KeyPressTriggerV2`, `ElementStateChangeTrigger`, `ElementAttributeChangeTrigger`, `MouseTriggerV2`, `HotkeyTriggerV2`, `SystemTriggerV2`, `SapSessionTrigger`), `AppRequestTrigger`.

Integration triggers never go inside `ui:TriggerScope`. Local triggers have no equivalent restriction — both placements are valid.

## Decision Rule

1. Run `uip rpa activities find --query "<event keyword>" --output json`. Read `isTrigger` and `triggerType`.
2. Branch on the CLI signal:
   - **Both fields absent** → regular activity, not a trigger.
   - **`isTrigger: true`, `triggerType: "integration"`** → integration trigger. **Place as the first activity of root `Sequence`; never inside `ui:TriggerScope`.** Check connection requirement — IS-based packages (Mail/GSuite/O365/`*.IntegrationService.Activities`) need a `ConnectionId`; `TimeTrigger`/`QueueTrigger`/`ManualTrigger` do not.
   - **`isTrigger: true`, `triggerType: "local"`** → local trigger. **Choose placement** based on runtime model — first activity of root for per-event dispatch, inside `<ui:TriggerScope.Triggers>` for long-running in-process subscription. No connection asset.
   - **`isTrigger: true`, unknown `triggerType`** → unknown category (forward-compat — new flavors may appear). Read the bundled doc and ask the user if still ambiguous.
3. For trigger activities, read **both** docs (per SKILL.md Rule 21): the bundled `references/activity-docs/<packageName>/<closest-version>/activities/<ClassNameTail>.md` **and** the project-local `{PROJECT_DIR}/.local/docs/packages/<packageName>/activities/<ClassNameTail>.md` if present. The bundled doc carries placement guidance, deployment context, and cross-cutting namespace/assembly gotchas the auto-generated `.local/docs` extractor omits; the `.local/docs` version reflects the exact installed package version. Also read the package's bundled `overview.md`.

## Entry-Point Worked Example — Office 365 New Email Received

A workflow that fires when an Outlook email arrives in INBOX with attachments.

```xml
<Activity mc:Ignorable="sap sap2010" x:Class="Main"
    xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
    xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
    xmlns:sap="http://schemas.microsoft.com/netfx/2009/xaml/activities/presentation"
    xmlns:sap2010="http://schemas.microsoft.com/netfx/2010/xaml/activities/presentation"
    xmlns:sco="clr-namespace:System.Collections.ObjectModel;assembly=System.Private.CoreLib"
    xmlns:ui="http://schemas.uipath.com/workflow/activities"
    xmlns:umamt="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail.Triggers;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umm="clr-namespace:UiPath.MicrosoftOffice365.Models;assembly=UiPath.MicrosoftOffice365"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
  <Sequence DisplayName="Main Sequence">
    <Sequence.Variables>
      <Variable x:TypeArguments="umm:Office365Message" Name="email" />
    </Sequence.Variables>

    <umamt:NewEmailReceived
        DisplayName="New Email Received"
        ConnectionId="<CONNECTION_GUID>"
        UseConnectionService="True"
        AuthScopesInvalid="False"
        BrowserFolderId="INBOX"
        BrowserFolderName="Inbox"
        FilterExpression="(parentFolderId=='INBOX')&amp;&amp;(hasAttachments==`true`)"
        IncludeAttachments="True"
        MarkAsRead="True"
        WithAttachmentsOnly="True"
        Result="[email]" />

    <!-- Handler: rest of the Sequence acts on `email` -->
    <ui:LogMessage Level="Info" Message="[&quot;Got email from &quot; + email.From.Address]" />
  </Sequence>
</Activity>
```

Three critical shape rules:

1. The trigger is the **first child** of the root `Sequence`. There is no `ui:TriggerScope` wrapping it.
2. `Result="[email]"` binds the activity's `Office365Message` output to a workflow-scope variable. The rest of the `Sequence` is the handler.
3. `FilterExpression` runs **server-side** (free) before the trigger fires — never re-implement the filter as an `If` inside the handler. Boolean literals use backticks; AND uses XML-escaped `&amp;&amp;`. Full syntax: [activity-docs/UiPath.MicrosoftOffice365.Activities/3.8/activities/NewEmailReceived.md](activity-docs/UiPath.MicrosoftOffice365.Activities/3.8/activities/NewEmailReceived.md).

## Local Trigger Worked Example — UI Click

A workflow that runs while a desktop app is open and reacts to clicks. The exact `xmlns` prefix and args type vary by package — always start from `uip rpa activities get-default-xaml --activity-class-name <FullClassName>` rather than hand-writing the namespace.

Structural shape (placeholders in angle brackets — fill from `get-default-xaml`):

```xml
<Activity x:Class="Main" ...>
  <Sequence DisplayName="Main Sequence">
    <ui:TriggerScope DisplayName="Trigger Scope"
                     SchedulingMode="Sequential"
                     xmlns:ui="http://schemas.uipath.com/workflow/activities">
      <ui:TriggerScope.Triggers>
        <!-- One or more local trigger activities. Get full XAML via:
               uip rpa activities get-default-xaml \
                 --activity-class-name <FullClassName> \
                 --project-dir "<PROJECT_DIR>" --output json -->
        <<TriggerPrefix>:<TriggerClassName> DisplayName="..." ... />
      </ui:TriggerScope.Triggers>
      <ui:TriggerScope.Action>
        <ActivityAction x:TypeArguments="<TriggerArgsType>">
          <Sequence>
            <!-- handler -->
          </Sequence>
        </ActivityAction>
      </ui:TriggerScope.Action>
    </ui:TriggerScope>
  </Sequence>
</Activity>
```

Shape rules:

1. `ui:TriggerScope` (`UiPath.Core.Activities.TriggerScope`, in package `UiPath.System.Activities`) is the container. `Triggers` is a collection — one or more child trigger activities.
2. `ui:TriggerScope.Action` is the handler. It is an `ActivityAction` typed on the trigger's args type (e.g. `MonitorClickEventArgs` for `NClickTrigger`, `FileSystemArgs` for file-change variants). Use `get-default-xaml` on the trigger to discover the exact args type.
3. **`SchedulingMode`** controls handler queueing (source: `Triggers/TriggerScope.cs`):
   - `Concurrent` — fire all handler instances in parallel.
   - `Sequential` *(default in most templates)* — queue events; run one handler at a time in arrival order. Filterable triggers can drop duplicate queued events.
   - `SequentialCollapse` — sequential, but collapse repeated events to the latest.
   - `SequentialDrop` — sequential, but cancel the running handler when a new event arrives.
   - `OneTime` — fire once and cancel the scope's child triggers.
4. **`ContinueOnError`** — when `true`, a faulted handler logs and the scope keeps running. When `false` (default), a fault stops the scope.
5. **`Break`** activity (from `UiPath.System.Activities`) inside the handler exits the `TriggerScope` cleanly.
6. The job remains alive for as long as `TriggerScope` is active. This is the wrong choice for events that arrive over hours/days; place the trigger at the workflow root instead, so Orchestrator owns the subscription and dispatches per event.

## Reading and Editing Existing TriggerScope XAML

Existing projects routinely use `ui:TriggerScope`. When you encounter one, treat it as a valid local-trigger pattern — do not flatten it. The choice between scoped and root placement for a local trigger is a runtime-model decision (long-running robot vs per-event jobs); changing it without the user's intent is wrong.

**How to identify:** any XAML containing `<ui:TriggerScope ...>` is a local-trigger workflow. The robot is expected to stay alive while this scope is active.

**Safe edits:**

- Adding another local trigger to the same scope → append to `<ui:TriggerScope.Triggers>`. Confirm the new trigger's args type matches (or the scope's `Action` `x:TypeArguments` is the common base — typically `TriggerArgs`). Integration triggers cannot be added here.
- Modifying the handler → edit inside `<ui:TriggerScope.Action>`. Do not move handler activities outside the scope.
- Changing `SchedulingMode` → safe; pick from the values above. Default unset value behaves as `Sequential`.

**Unsafe edits — these break the workflow:**

- Moving a local trigger out of `ui:TriggerScope` to root placement when the user only asked you to "modernize" the workflow. The two placements have different deployment models (per-event jobs vs long-running robot); ask the user first.
- Removing `<ui:TriggerScope.Triggers>` while keeping `<ui:TriggerScope.Action>` — `CacheMetadata` validation fails (`TriggerScope_NoTrigger`).
- Inserting an integration trigger (`triggerType: "integration"`) inside `<ui:TriggerScope.Triggers>` — see [Anti-patterns](#anti-patterns).

**When to question a TriggerScope you find:** if `<ui:TriggerScope.Triggers>` contains an activity whose bundled doc labels it **Integration trigger** (e.g. `NewEmailReceived`, `TimeTrigger`, `QueueTrigger`), the prior author placed an integration trigger inside a `TriggerScope`. The workflow compiles but does not get registered as an Orchestrator trigger. Flag this to the user — the fix is to move that trigger to the workflow root.

## Catalog of Trigger Activities

### Integration (root placement, never inside `ui:TriggerScope`)

Every activity whose bundled doc labels it **Integration trigger**, plus every Integration Service connector trigger (its `namespace` will contain `.Triggers`). The bundled hand-written docs cover these:

| Package | Activity | Bundled doc |
|---|---|---|
| `UiPath.System.Activities` | `TimeTrigger` (Time Trigger) | [activity-docs/UiPath.System.Activities/26.4/activities/TimeTrigger.md](activity-docs/UiPath.System.Activities/26.4/activities/TimeTrigger.md) |
| `UiPath.System.Activities` | `QueueTrigger` (New Item Added to Queue) | [activity-docs/UiPath.System.Activities/26.4/activities/QueueTrigger.md](activity-docs/UiPath.System.Activities/26.4/activities/QueueTrigger.md) |
| `UiPath.System.Activities` | `ManualTrigger` (Manual Trigger) | [activity-docs/UiPath.System.Activities/26.4/activities/RuntimeContext.md](activity-docs/UiPath.System.Activities/26.4/activities/RuntimeContext.md) |
| `UiPath.MicrosoftOffice365.Activities` | `NewEmailReceived` | [activity-docs/UiPath.MicrosoftOffice365.Activities/3.8/activities/NewEmailReceived.md](activity-docs/UiPath.MicrosoftOffice365.Activities/3.8/activities/NewEmailReceived.md) |
| `UiPath.GSuite.Activities` | `NewEmailReceived` (Gmail), `NewFileCreated`, `NewEventCreated`, `NewEventInvitationReceived`, `RowAddedToSheetBottom` | `activity-docs/UiPath.GSuite.Activities/3.8/activities/` |

Beyond the bundled set: every Integration Service connector trigger qualifies — Salesforce CREATED/UPDATED/DELETED, Jira issue triggers, ServiceNow record triggers, Slack message triggers, Microsoft Teams triggers, SharePoint list-item triggers, etc. For IS trigger semantics (`eventMode`, webhook URL retrieval, filter trees), query the CLI: `uip is activities list "<connector-key>" --triggers --output json` and `uip is triggers describe "<connector-key>" "<OPERATION>" "<object>" --output json`.

### Local (flexible placement — first activity of root, or wrapped in `<ui:TriggerScope.Triggers>`)

Concrete authorable activities. Listed by package. For full property surface, run `uip rpa activities get-default-xaml --activity-class-name <FullClassName>` — namespaces and args types vary.

| Package | Concrete activities | Notes |
|---|---|---|
| `UiPath.System.Activities` | `RepeatTrigger`, `GlobalVariableChangedTrigger`, `FileChangeTriggerV3` | Interval, global-variable change, filesystem watcher. |
| `UiPath.UIAutomationNext.Activities` | `NClickTrigger`, `NKeyboardTrigger` | UIA Next click and keyboard events. Args types: `MonitorClickEventArgs`, `MonitorKeyboardEventArgs`. Both derive from UIA Next's `TriggerBase<T>` → `Platform.InterruptibleTriggerBase<T>`. |
| `UiPath.UIAutomation.Activities` (Classic V2) | Selector-bound: `ClickTriggerV2`, `ClickImageTriggerV2`, `KeyPressTriggerV2`, `ElementStateChangeTrigger`, `ElementAttributeChangeTrigger`. System-level: `MouseTriggerV2`, `HotkeyTriggerV2`, `SystemTriggerV2`, `SapSessionTrigger`. | All share `EventInfoTriggerArgs`. Selector-bound triggers require a target descriptor; system-level triggers monitor process-wide events. `SelectorTriggerActivityV2` and `MouseAndKeyTriggerActivityBase` are abstract bases — not directly authorable. |
| `UiPath.WorkflowEvents.Activities` | `AppRequestTrigger` | Cross-workflow request bus inside a running job. |

If the activity is not in this table: run `uip rpa activities find --query Trigger` against the installed package and read `triggerType`. `"local"` activities can be placed at root or wrapped in `TriggerScope` — choose per runtime model.

## Connection Handling (IS Triggers)

Integration triggers from Integration Service packages require a `ConnectionId`. A placeholder GUID (`00000000-0000-0000-0000-000000000000`) passes `uip rpa validate` and `uip rpa build` but fails at runtime when Orchestrator tries to subscribe. Resolve a real connection scoped to the connector and across all folders (active-folder-only scans miss connections owned by other folders):

```bash
uip is connections list "<connector-key>" --all-folders --output json
```

For example, `uip is connections list "uipath-microsoft-outlook365" --all-folders --output json` for the O365 Mail triggers. Copy the connection's GUID into `ConnectionId`. If no connection exists, create one (`uip is connections create <connector-key>`) and verify it's active (`uip is connections ping <connection-id>`).

## Server-Side Filtering

Integration triggers from IS packages typically expose a filter property — an OData-style boolean predicate (or structured tree) that runs on the connector side **before** the trigger fires. Use it for any "fire only if X" logic. Re-implementing the filter inside the handler wastes Orchestrator dispatch and robot time on events you would discard.

Per-package conventions (read each package's bundled `overview.md` for canonical syntax):

- **O365 Mail** (`umm:` prefix family): `FilterExpression` as a string attribute. OData-like: `(parentFolderId=='INBOX')`, `(hasAttachments==`true`)`. AND uses `&amp;&amp;`; booleans use backticks. See [activity-docs/UiPath.MicrosoftOffice365.Activities/3.8/activities/overview.md](activity-docs/UiPath.MicrosoftOffice365.Activities/3.8/activities/overview.md).
- **GSuite Gmail**: `Filter` as a structured child element with `LogicalOperator` + `Criteria` leaves, not a string. See [activity-docs/UiPath.GSuite.Activities/3.8/activities/NewEmailReceived.md](activity-docs/UiPath.GSuite.Activities/3.8/activities/NewEmailReceived.md).
- **IS connector triggers** (Salesforce, Jira, Slack, …): authored as a structured filter tree, not a string. Discover the filterable field names via `uip is triggers describe "<connector>" "<OPERATION>" "<object>" --output json` → read `Data.FilterFields[*].Name`. The CLI compiles the tree into the runtime expression; do not pass the compiled form directly.

## Lifecycle and Verification

Lifecycle depends on placement, not type. Two paths:

### Entry-point lifecycle (trigger at workflow root)

Applies to all integration triggers, and to local triggers placed at root.

1. **Author** — place trigger as the first activity of root `Sequence`, bind output to variable, write handler. Per-file `validate` clean.
2. **Build** — `uip rpa build "<PROJECT_DIR>" --output json` clean.
3. **Publish** — `.nupkg` to Orchestrator (see [publishing-guide.md](publishing-guide.md)). On publish, Orchestrator detects the trigger from the workflow's activity registration and exposes it as a Process/Time/Queue Trigger candidate.

**`uip rpa run` is NOT a meaningful smoke test for entry-point triggers.** The CLI executes the workflow once in-process, which does not exercise Orchestrator subscription or the connector's webhook/polling lifecycle. A clean `run` only proves the handler XAML compiles and the trigger activity can be instantiated.

### In-process lifecycle (local trigger inside `ui:TriggerScope`)

Applies only to local triggers wrapped in `ui:TriggerScope`.

1. **Author** — `ui:TriggerScope` with `Triggers` (one or more local trigger activities) and `Action` (the handler). Per-file `validate` clean.
2. **Build** — `uip rpa build` clean.
3. **Run** — `uip rpa run --file-path Main.xaml --project-dir "<PROJECT_DIR>" --output json`. The robot stays alive; trigger events fire while the run is active. Generate an event (click, file change, etc.) and confirm the handler executes.
4. **Deploy** — publish to Orchestrator and start as a long-running attended/unattended job. The job remains active and consumes a robot slot for the duration.

## Anti-patterns

1. **Integration trigger wrapped in `ui:TriggerScope`.** Re-author by removing the `ui:TriggerScope` wrapper and placing the trigger at the root.
2. **Re-implementing the filter as an `If` in the handler.** Robot pays dispatch cost on every event the filter would have rejected. Move the predicate into the trigger's filter property.
3. **Calling `uip rpa run` to "test" an O365/Gmail/Salesforce/queue/schedule trigger.** See entry-point lifecycle above — `run` does not exercise Orchestrator subscription.
4. **Moving a local trigger out of `ui:TriggerScope` to root placement without intent.** Both placements are valid for local triggers; the choice is a runtime-model decision (per-event jobs vs long-running robot). Confirm with the user before changing it.
5. **Hand-editing the auto-generated `.local/docs/.../<Trigger>.md`.** That file is regenerated on package restore. Treat it as read-only; the bundled doc in `references/activity-docs/` is the editable source of placement and example guidance.
6. **Inventing an `xmlns:` prefix for an unfamiliar trigger.** Always pull the namespace from `uip rpa activities get-default-xaml --activity-class-name <FullClassName>`; do not infer it from the class's logical hierarchy.
