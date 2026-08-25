# Bypass Rule Management

Manage URL-pattern bypass rules with `uip admin ip-restriction bypass-rules`. See [ip-restriction-commands.md](ip-restriction-commands.md) for per-command flag tables, output codes, and single-command examples.

## Concept

Bypass rules create **URL-pattern exceptions** to IP allowlisting for specific App, folder, or tenant URL patterns. The server compiles each `regexEntry`; optional metadata may include `appName` and tenant association. Rules have no effect when [enforcement](enforcement-management.md) is `Disabled`.

## Inspect

Before creating, updating, or deleting a rule, run:

- `uip admin ip-restriction bypass-rules list --output json` to list all rules.
- `uip admin ip-restriction bypass-rules list --filter "<FRAGMENT>" --output json` for a case-insensitive substring search across `regexEntry` and `appName`.
- `uip admin ip-restriction bypass-rules get <RULE_ID> --output json` to inspect one rule, including `regexEntry`, `appName`, tenant association, and timestamps.

Use inspection to confirm the target before update or delete.

## Create

Create is file-only; there is no inline shortcut for the create body.

1. Write `bypass-rule.json`, for example:
   ```json
   {
     "regexEntry": "^.*\\.contoso\\.com$",
     "appName": "<OPTIONAL_APP_NAME>"
   }
   ```
   Refer to UiPath docs for the full `AddRegexBypassRequest` schema, including tenant fields.
2. Run `uip admin ip-restriction bypass-rules create --file ./bypass-rule.json --output json`.
3. Run `uip admin ip-restriction bypass-rules get <NEW_RULE_ID> --output json` to verify the result.

## Authoring Rules

- Escape dots: `.contoso.com` also matches `Xcontoso.com`; use `\\.contoso\\.com`.
- Anchor patterns with `^` and `$` to avoid matching URLs containing the fragment.
- Test the rule through UiPath app access before deploying it broadly.

## Update

- For a regex-only change, pass `--regex-entry "<NEW_PATTERN>"` inline.
- For tenant or app metadata, pass `--file ./bypass-rule-update.json` containing the full `UpdateRegexBypassRequest` body.

## Delete

1. Run `uip admin ip-restriction bypass-rules get <RULE_ID> --output json` and confirm the target.
2. Confirm the deletion with the user.
3. Run `bypass-rules delete <RULE_ID>`.

Do not use a `--confirm` flag: unlike `ip-ranges delete`, bypass-rule deletion only narrows access and never widens it.