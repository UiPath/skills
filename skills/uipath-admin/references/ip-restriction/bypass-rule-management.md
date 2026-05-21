# Bypass Rule Management

Multi-step workflows for managing URL-pattern bypass rules via `uip admin ip-restriction bypass-rules`. For per-command flag tables, output codes, and single-command examples, see [ip-restriction-commands.md](ip-restriction-commands.md).

## Concept

Bypass rules carve out **URL-pattern exceptions** to IP allowlisting. Use them when the org has enforcement on but needs a specific App / folder / tenant URL pattern to remain reachable from outside the allowed IP ranges.

Each rule's regex pattern (`regexEntry`) is compiled server-side from the supplied string. Optional metadata (`appName`, tenant association) can travel with the rule.

Bypass rules only matter when [enforcement](enforcement-management.md) is `Enabled`. When enforcement is `Disabled`, they have no effect.

## Workflow: List & Inspect Rules

Use these read patterns before any create / update / delete to confirm what's already in place.

### List all rules

```bash
uip admin ip-restriction bypass-rules list --output json
```

### Search by pattern fragment or app name

`--filter` runs a case-insensitive substring match on each rule's `regexEntry` *and* `appName`. Useful when you remember a domain fragment but not the rule id.

```bash
uip admin ip-restriction bypass-rules list --filter "<FRAGMENT>" --output json
```

### Inspect one rule by id

```bash
uip admin ip-restriction bypass-rules get <RULE_ID> --output json
```

Returns `regexEntry`, `appName`, tenant association, and timestamps. Use this before update/delete to confirm you're targeting the right rule.

## Workflow: Create a Bypass Rule

Create is file-only (no inline shortcut for the create body).

1. Author the rule body (`bypass-rule.json`):
   ```json
   {
     "regexEntry": "^.*\\.contoso\\.com$",
     "appName": "<OPTIONAL_APP_NAME>"
   }
   ```
   Refer to UiPath docs for the full `AddRegexBypassRequest` schema (tenant fields, etc.).
2. Create:
   ```bash
   uip admin ip-restriction bypass-rules create --file ./bypass-rule.json --output json
   ```
3. Verify:
   ```bash
   uip admin ip-restriction bypass-rules get <NEW_RULE_ID> --output json
   ```

## Authoring Tips

- **Escape dots in regex.** A pattern like `.contoso.com` matches `Xcontoso.com` too. Use `\.contoso\.com`.
- **Anchor with `^` and `$`.** Otherwise the pattern matches any URL containing the fragment.
- **Test before deploying broadly.** Add the rule, verify it via UiPath app access, then promote.

## Workflow: Update a Rule

- **Regex-only change** — pass `--regex-entry "<NEW_PATTERN>"` inline.
- **Tenant / app metadata** — pass `--file ./bypass-rule-update.json` with the full `UpdateRegexBypassRequest` body.

## Workflow: Delete a Rule

1. Confirm the rule to delete:
   ```bash
   uip admin ip-restriction bypass-rules get <RULE_ID> --output json
   ```
2. Confirm with the user.
3. Run `bypass-rules delete <RULE_ID>`.

No `--confirm` flag required (unlike `ip-ranges delete`) — bypass-rule deletion only narrows access, never widens it.
