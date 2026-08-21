# Planned Configuration — Outlook Connection

## Open Question: Microsoft Outlook 365 Connection

Nodes `emailReceived1`, `replyUrgentAck1`, and `replyTicketConfirmation1` use
connector type `uipath-mock-outlook` (Microsoft Mocked Outlook 365 for webhooks).

**No Integration Service connection exists for this connector yet.**

All three nodes are currently configured with the placeholder connection ID
`00000000-0000-0000-0000-000000000000`. This is intentional — the flow is
structurally valid and will pass `validate`, but **the three Outlook nodes will
fail at runtime** until you replace the placeholder with a real connection.

## Steps to Complete Configuration

1. **Create an Outlook connection** in Integration Service:
   - Go to Integration Service → Connections → New Connection
   - Search for "Microsoft Outlook 365" (or "uipath-mock-outlook" for the mocked version)
   - Authenticate and save the connection. Note the returned Connection ID.

2. **Get the FolderKey** for the Orchestrator folder where the connection lives:
   ```bash
   uip or folders list --output json
   # or: uip is connections list --output json | jq '.Data[] | select(.connector=="uipath-mock-outlook")'
   ```

3. **Re-configure the three Outlook nodes** with the real connection:
   ```bash
   cd CustomerSupportTriage/

   # Trigger node
   uip maestro flow node configure CustomerSupportTriage.flow emailReceived1 \
     --detail '{
       "connectionId": "<REAL_CONNECTION_ID>",
       "folderKey": "<REAL_FOLDER_KEY>",
       "eventMode": "polling"
     }'

   # Urgent acknowledgment reply
   uip maestro flow node configure CustomerSupportTriage.flow replyUrgentAck1 \
     --detail '{
       "connectionId": "<REAL_CONNECTION_ID>",
       "folderKey": "<REAL_FOLDER_KEY>",
       "method": "POST",
       "endpoint": "/ReplyToEmail",
       "queryParameters": { "id": "=js:$vars.emailReceived1.output.id" },
       "bodyParameters": {
         "comment": "=js:\"Dear customer,\\n\\nThank you for contacting us. We have received your email regarding: \" + $vars.classify.output.subject + \"\\n\\nThis has been flagged as urgent and a member of our support team will be in touch with you very shortly.\\n\\nBest regards,\\nCustomer Support Team\""
       }
     }'

   # Ticket confirmation reply
   uip maestro flow node configure CustomerSupportTriage.flow replyTicketConfirmation1 \
     --detail '{
       "connectionId": "<REAL_CONNECTION_ID>",
       "folderKey": "<REAL_FOLDER_KEY>",
       "method": "POST",
       "endpoint": "/ReplyToEmail",
       "queryParameters": { "id": "=js:$vars.emailReceived1.output.id" },
       "bodyParameters": {
         "comment": "=js:\"Dear customer,\\n\\nThank you for contacting us. We have created a support ticket for your request.\\n\\nTicket Reference: \" + $vars.createJiraTicket1.output.key + \"\\nSubject: \" + $vars.classify.output.subject + \"\\n\\nOne of our agents will review your request and follow up with you soon.\\n\\nBest regards,\\nCustomer Support Team\""
       }
     }'
   ```

4. **Validate and format** after re-configuration:
   ```bash
   uip maestro flow validate CustomerSupportTriage.flow
   uip maestro flow format CustomerSupportTriage.flow
   ```

## Connections Already Configured (No Action Needed)

| Node | Connector | Connection ID | Status |
|---|---|---|---|
| `slackAlertToTeam1` | Slack | `849e85d8-1aa9-4d52-8bbd-20041c8f05d8` | ✅ Live |
| `createJiraTicket1` | Jira | `f5273a4d-d492-4bcd-a106-5a20bf89a3ef` | ✅ Live |
| `emailReceived1` | Outlook (trigger) | `00000000-0000-0000-0000-000000000000` | ⚠️ Placeholder |
| `replyUrgentAck1` | Outlook (reply) | `00000000-0000-0000-0000-000000000000` | ⚠️ Placeholder |
| `replyTicketConfirmation1` | Outlook (reply) | `00000000-0000-0000-0000-000000000000` | ⚠️ Placeholder |
