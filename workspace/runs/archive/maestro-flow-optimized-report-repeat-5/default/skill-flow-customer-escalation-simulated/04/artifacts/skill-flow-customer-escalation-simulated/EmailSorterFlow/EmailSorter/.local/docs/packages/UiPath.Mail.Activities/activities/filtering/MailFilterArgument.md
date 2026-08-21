# MailFilterArgument

`UiPath.Mail.Activities.Business.ForEachMail.MailFilterArgument`

Represents a collection of server-side mail filter conditions. Each condition targets a mail field (From, Subject, Date, etc.) with an operator and value. Multiple conditions are combined using a logical operator (AND/OR). Used by the ForEachEmailX activity to filter emails before iteration.

## Structure

| Property | Type | Description |
|----------|------|-------------|
| LogicalOperator | `MailFilterLogicalOperator` | How multiple filters are combined: AND (all must match) or OR (any must match). |
| Filters | `List<SingleMailFilterArgument>` | Zero or more individual filter conditions to apply. |

## Filter Element: SingleMailFilterArgument

`UiPath.Mail.Activities.Business.ForEachMail.SingleMailFilterArgument`

Represents a single filter condition within a MailFilterArgument collection. For string-based fields, use Criteria + Operator + Value. For the Date field, use Criteria + Operator + DateFilter (or DateEqualsFilter when Operator is Equals).

| Property | Type | Description |
|----------|------|-------------|
| Criteria | `MailFilterField` | The email field to filter on (e.g., From, Subject, Date). |
| Operator | `MailFilterOperator` | The comparison operator (e.g., Contains, Equals, NewerThan). |
| Value | `InArgument<string>` | The string value for the filter expression. Ignored when Criteria is Date. |
| DateFilter | `DateFilterOption` | A relative date range used when Criteria is Date and Operator is not Equals. Ignored for non-date fields. |
| DateEqualsFilter | `InArgument<DateTime>` | An exact DateTime for equality comparison when Criteria is Date and Operator is Equals. |

## Enum Reference

**MailFilterLogicalOperator** (`UiPath.Mail.Implementation.MailFilterLogicalOperator`): `And`, `Or`

- `And` -- All filters must match (displayed as "All Filters").
- `Or` -- Any filter must match (displayed as "Any Filter").

**MailFilterField** (`UiPath.Mail.Implementation.MailFilterField`): `From`, `To`, `Date`, `CC`, `BCC`, `Subject`, `Body`, `Categories`

- `From` -- Sender address.
- `To` -- Recipient address.
- `Date` -- Message date (switches the filter to date mode).
- `CC` -- CC recipients.
- `BCC` -- BCC recipients.
- `Subject` -- Email subject line.
- `Body` -- Email body content.
- `Categories` -- Email categories.

**MailFilterOperator** (`UiPath.Mail.Implementation.MailFilterOperator`): `Contains`, `NotContains`, `Equals`, `StartsWith`, `EndsWith`, `NewerThan`, `OlderThan`, `IsEmpty`, `IsNotEmpty`

- `Contains` -- Field contains the value.
- `NotContains` -- Field does not contain the value.
- `Equals` -- Field exactly equals the value (for Date fields, uses DateEqualsFilter).
- `StartsWith` -- Field starts with the value.
- `EndsWith` -- Field ends with the value.
- `NewerThan` -- Date is newer than the DateFilter range (date fields only).
- `OlderThan` -- Date is older than the DateFilter range (date fields only).
- `IsEmpty` -- Field is empty (no value operand needed).
- `IsNotEmpty` -- Field is not empty (no value operand needed).

**DateFilterOption** (`UiPath.Mail.Implementation.DateFilterOption`): `Today`, `TwoDays`, `ThreeDays`, `SevenDays`, `FourteenDays`, `ThirtyDays`, `NinetyDays`

Relative date ranges used with NewerThan/OlderThan operators on the Date field.

## Used By

- [ForEachEmailX](../ForEachEmailX.md)
