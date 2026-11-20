# Expense approval: details for the case

- Request reference: `{{RUN_TOKEN}}`
- Approver: is-sandboxes-test@uipathsandboxes.onmicrosoft.com

## Approver email (Microsoft Outlook 365)

- Connection: is-sandboxes-test@uipathsandboxes.onmicrosoft.com, ID
  `dd657127-91f5-4568-a3a3-c024bc03fb0f`
- Subject: Expense approval required — {{RUN_TOKEN}}
- Body: An expense request is awaiting approval. Reference: {{RUN_TOKEN}}

## Audit record (Jira)

- Connection: is-sandboxes-test@uipath.com-uipath-sandbox-380, ID
  `f5273a4d-d492-4bcd-a106-5a20bf89a3ef`
- Project: SJP, issue type ID 10506
- Summary: Expense audit — {{RUN_TOKEN}}
- Description: Audit record for approved expense request. Reference: {{RUN_TOKEN}}

The tenant also has personal Outlook and Jira connections with the same names,
so use these two connection IDs.
