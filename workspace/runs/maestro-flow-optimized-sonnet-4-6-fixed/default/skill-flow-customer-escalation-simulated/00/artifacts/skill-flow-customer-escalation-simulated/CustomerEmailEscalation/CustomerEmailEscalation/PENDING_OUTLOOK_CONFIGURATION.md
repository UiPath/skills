# Pending Outlook Configuration

Three nodes in this flow require an Outlook connection that does not yet exist on the tenant.
Once you create a `uipath-mock-outlook` connection in Integration Service, run the three
`uip maestro flow node configure` commands below to bind and fully populate each node.

---

## Step 1 — Create the connection

1. Open **Integration Service → Connections → Add connection**
2. Choose connector: **uipath-mock-outlook**
3. Complete OAuth/credentials and save
4. Note the connection ID (`<OUTLOOK_CONN_ID>`) and the folder key it was created in (`<OUTLOOK_FOLDER_KEY>`)

---

## Step 2 — Configure the trigger node (`emailReceived1`)

```bash
uip maestro flow node configure CustomerEmailEscalation.flow emailReceived1 \
  --detail '{
    "connectionId": "<OUTLOOK_CONN_ID>",
    "folderKey": "<OUTLOOK_FOLDER_KEY>",
    "triggerEvent": "email-received",
    "filters": {}
  }'
```

Outputs consumed by downstream nodes: `subject`, `body`, `from`, `id`

---

## Step 3 — Configure the VIP acknowledgment reply (`replyAcknowledgmentToSender1`)

```bash
uip maestro flow node configure CustomerEmailEscalation.flow replyAcknowledgmentToSender1 \
  --detail '{
    "connectionId": "<OUTLOOK_CONN_ID>",
    "folderKey": "<OUTLOOK_FOLDER_KEY>",
    "method": "POST",
    "endpoint": "/reply-to-email",
    "bodyParameters": {
      "emailId": "=js:$vars.emailReceived1.output.id",
      "body": "Thank you for reaching out. We have received your message and a member of our team will be with you shortly."
    }
  }'
```

---

## Step 4 — Configure the ticket reply (`replyWithTicketDetails1`)

```bash
uip maestro flow node configure CustomerEmailEscalation.flow replyWithTicketDetails1 \
  --detail '{
    "connectionId": "<OUTLOOK_CONN_ID>",
    "folderKey": "<OUTLOOK_FOLDER_KEY>",
    "method": "POST",
    "endpoint": "/reply-to-email",
    "bodyParameters": {
      "emailId": "=js:$vars.emailReceived1.output.id",
      "body": "=js:`Thank you for contacting us. Your request has been logged and assigned ticket ID ${$vars.createFreshdeskTicket1.output.id}. Our support team will follow up with you shortly.`"
    }
  }'
```

---

## Slack channel note

The Slack node (`slackAlertToChannel1`) is currently configured with a placeholder channel.
The workspace did not contain a `#vip-escalations` channel in the channel directory.
To use the correct channel:

1. Confirm `#vip-escalations` exists (or create it) in your Slack workspace
2. Retrieve its channel ID (the `C...` ID from Slack admin or the API)
3. Run:

```bash
uip maestro flow node configure CustomerEmailEscalation.flow slackAlertToChannel1 \
  --detail '{
    "connectionId": "849e85d8-1aa9-4d52-8bbd-20041c8f05d8",
    "folderKey": "5da18ec0-7de1-4e57-aaf1-ddc8a369c199",
    "method": "POST",
    "endpoint": "/send_message_to_channel_v2",
    "bodyParameters": {
      "channel": "<CORRECT_CHANNEL_ID>",
      "messageToSend": "=js:`🚨 VIP Escalation — ${$vars.emailReceived1.output.subject || \"(no subject)\"} — From: ${$vars.emailReceived1.output.from || \"unknown\"}`"
    }
  }'
```
