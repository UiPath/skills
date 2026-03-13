# Examples Repository Reference

Use the examples repository as a **last resort** when activity docs, `find-activities`, and `get-default-activity-xaml` don't give you what you need — or when you need **full workflow composition patterns** showing how multiple activities work together end-to-end. Activity docs describe individual activities well, but the examples repository shows multi-step orchestration.

## Searching Examples

```bash
# Search by service tags (AND logic — all tags must match)
uipcli rpa list-workflow-examples --tags '["web"]' --limit 10 --format json

# Multiple tags narrow down results
uipcli rpa list-workflow-examples --tags '["jira", "confluence"]' --limit 10 --format json

# Use prefix to filter by category
uipcli rpa list-workflow-examples --tags '["gmail"]' --prefix "email-communication/" --limit 15 --format json

# Once you identify relevant examples, retrieve XAML content:
uipcli rpa get-workflow-example --key "email-communication/add-new-gmail-emails-to-keap-as-contacts.xaml"
```

## Tag Selection Guidelines

- Identify the services/integrations the user wants (e.g., "salesforce", "gmail", "jira", "web")
- Convert to lowercase tags: `["salesforce"]`, `["gmail"]`, `["jira", "confluence"]`
- Multiple tags use AND logic — all tags must match

**Complete tag list:** `adobe-sign`, `asana`, `box`, `concur`, `confluence`, `database`, `document-understanding`, `docusign`, `dropbox`, `email-generic`, `excel`, `excel-online`, `freshbooks`, `freshdesk`, `github`, `gmail`, `google-calendar`, `google-docs`, `google-drive`, `google-sheets`, `gsuite`, `hubspot`, `intacct`, `jira`, `mailchimp`, `marketo`, `microsoft-365`, `onedrive`, `outlook`, `outlook-calendar`, `pdf`, `powerpoint`, `productivity`, `quickbooks`, `salesforce`, `servicenow`, `sharepoint`, `shopify`, `slack`, `smartsheet`, `stripe`, `teams`, `testing`, `trello`, `web`, `webex`, `word`, `workday`, `zendesk`, `zoom`

## When to Use

- Activity docs, `find-activities`, and `get-default-activity-xaml` didn't provide enough context
- You need end-to-end workflow patterns showing multiple activities composed together
- You need to understand service-specific integration patterns (e.g., OAuth flows, trigger setups)
- You're building a complex multi-activity workflow and want to see how others structured similar automations

## Studying Retrieved Examples

When studying repository examples from `uipcli rpa get-workflow-example`:
- The command returns the full XAML content directly
- Parse the namespace declarations at the top to identify required packages
- Look for `<Variable>` elements to understand data structures
- Study `<Argument>` elements for input/output patterns
- Study `<Configuration>` and `<Connection>` sections for determining dynamic activity properties usage
- Examine activity configurations for proper property settings
