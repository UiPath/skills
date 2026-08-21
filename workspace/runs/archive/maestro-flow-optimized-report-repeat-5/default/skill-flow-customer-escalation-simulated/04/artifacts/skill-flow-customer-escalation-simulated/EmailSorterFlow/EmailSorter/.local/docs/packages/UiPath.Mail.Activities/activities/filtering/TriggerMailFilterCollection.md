# TriggerMailFilterCollection

`UiPath.Mail.Activities.IMAP.Filters.TriggerMailFilterCollection`

Represents a collection of mail filter conditions for IMAP email triggers. Extends `BaseFilterCollection<TriggerMailFilterElement, TriggerMailFilterLogicalOperator>`, providing a logical operator to combine multiple string-based filter conditions. Used by the NewIMAPEmailReceivedTrigger activity to filter incoming emails.

## Structure

| Property | Type | Description |
|----------|------|-------------|
| LogicalOperator | `TriggerMailFilterLogicalOperator` | How multiple filters are combined: AND (all must match) or OR (any must match). Inherited from BaseFilterCollection. |
| Filters | `List<TriggerMailFilterElement>` | Zero or more individual filter conditions to apply. Inherited from BaseFilterCollection. |

## Filter Element: TriggerMailFilterElement

`UiPath.Mail.Activities.IMAP.Filters.TriggerMailFilterElement`

Represents a single string-based filter condition within a TriggerMailFilterCollection. Unlike MailFilterArgument, trigger filters only support string fields and string operators (no date filtering).

| Property | Type | Description |
|----------|------|-------------|
| Criteria | `TriggerMailFilterField` | The email field to filter on (Subject, To, or From). |
| StringOperator | `TriggerMailStringFilterOperator` | The string comparison operator (e.g., Contains, Equals, StartsWith). |
| StringValue | `string` | The string value for the filter expression. |

## Enum Reference

**TriggerMailFilterLogicalOperator** (`UiPath.Mail.IMAP.Enums.TriggerMailFilterLogicalOperator`): `And`, `Or`

- `And` -- All filters must match (displayed as "All Filters").
- `Or` -- Any filter must match (displayed as "Any Filter").

**TriggerMailFilterField** (`UiPath.Mail.IMAP.Enums.TriggerMailFilterField`): `Subject`, `To`, `From`

- `Subject` -- Email subject line.
- `To` -- Recipient address.
- `From` -- Sender address.

**TriggerMailStringFilterOperator** (`UiPath.Mail.IMAP.Enums.TriggerMailStringFilterOperator`): `Contains`, `NotContains`, `Equals`, `StartsWith`, `EndsWith`, `NotStartsWith`, `NotEndsWith`, `NotEquals`

- `Contains` -- Field contains the value.
- `NotContains` -- Field does not contain the value.
- `Equals` -- Field exactly equals the value.
- `StartsWith` -- Field starts with the value.
- `EndsWith` -- Field ends with the value.
- `NotStartsWith` -- Field does not start with the value.
- `NotEndsWith` -- Field does not end with the value.
- `NotEquals` -- Field does not equal the value.

## Used By

- [NewIMAPEmailReceivedTrigger](../NewIMAPEmailReceivedTrigger.md)
