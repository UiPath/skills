# Public Safety

This skill is intended for a public skills repository. Keep all content, examples, fixtures, logs, and commits safe to publish.

## Never include

- Raw exported BPMN from customers, tenants, demos, or operator-supplied examples.
- Tenant URLs, organization names, folder keys, connection IDs, release keys, queue IDs, process IDs, user IDs, or email addresses.
- Private process names, business payloads, screenshots, exported package contents, or traces.
- Local absolute paths from developer machines.
- Temporary mission notes, task transcripts, or Rookery-only context.
- Internal-only repository paths as runtime instructions for the skill user.

## Use instead

- Synthetic process names such as `InvoiceApproval`.
- Synthetic element IDs such as `Task_ValidateRequest`.
- Placeholder resource labels such as `<PROCESS_NAME>`, `<FOLDER_KEY>`, or `<CONNECTION_NAME>` when the user must provide a real value.
- Short structural examples that demonstrate XML shape without private data.
- Summaries of behavior rather than copied private XML.

## Review checklist

Before committing:

- Search changed files for local path fragments, URLs, IDs, and private names.
- Confirm every example can be understood without access to internal repositories.
- Confirm Integration Service examples do not contain real connector resource identifiers.
- Confirm generated package metadata examples are synthetic or omitted.
