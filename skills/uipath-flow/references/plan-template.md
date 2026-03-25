# Flow Plan: {{PROJECT_NAME}}

{{SUMMARY}}

## Flow Diagram

```mermaid
{{MERMAID_DIAGRAM}}
```

<!--
    MERMAID TIPS for large flows (20+ nodes):
    - Use subgraph blocks to group related nodes:
        subgraph Ingestion
            A[Read Emails] --> B[Parse Body]
        end
    - Prefer direction TB (top-bottom) — it uses page width better and is more readable
    - Use LR (left-right) only for very linear flows with few branches
    - Node shapes: [rectangle], {diamond/decision}, ([rounded]), [[subroutine]]
    - Edge labels: A -->|"label"| B
    - Style subgraphs: style Ingestion fill:#fff7f5,stroke:#FA4616
-->

## Nodes

| # | Name | Category | Node Type | Description |
|---|------|----------|-----------|-------------|
{{NODE_ROWS}}

<!--
    EXAMPLE ROWS:
    | 1 | Read Emails | connector | `uipath.outlook.mail.read` | Reads unread emails from the configured Outlook inbox |
    | 2 | Parse Body | script | `uipath.script.js` | Extracts sender and subject from email payload |
    | 3 | Check Priority | control | `uipath.if` | Routes high-priority emails to fast track |

    Category labels: connector, script, control, trigger, agent
-->

<!--
    OMIT THIS ENTIRE SECTION (heading + table) if the flow has no connector nodes.
-->

## Connector Details

| Node | Connector Key | Operation | Required Inputs | Connection |
|------|--------------|-----------|-----------------|------------|
{{CONNECTOR_ROWS}}

<!--
    EXAMPLE ROWS:
    | Read Emails | `uipath-microsoft365-mail` | List Messages | folderId, maxResults | Found (id: abc-123) |
    | Post to Slack | `uipath-slack-connector` | Send Message | channel, text | **Not found — user must create** |
-->

## Inputs & Outputs

| Direction | Name | Type | Description |
|-----------|------|------|-------------|
{{IO_ROWS}}

<!--
    EXAMPLE ROWS:
    | Input | triggeredBy | Timer (5 min) | Scheduled trigger |
    | Output | processedCount | number | Number of emails processed |
-->

<!--
    OMIT THIS ENTIRE SECTION (heading + list) if there are no open questions.
-->

## Open Questions

{{OPEN_QUESTIONS}}

<!--
    EXAMPLE:
    - **[REQUIRED]** Which Slack channel should notifications be posted to?
    - **[REQUIRED]** Should the flow filter by email sender or subject line?
-->
