# MCP Server Guardrails

`uip agenthub mcp-guardrails` manages a server's built-in guardrails, the rules the Agent Gateway UI configures. Every command takes `--mcp <SLUG>` and the server's folder ([Folder Context](../SKILL.md#folder-context)). A rule screens every tool call of the server, including tools added later, before the tool runs and on its result.

## Which Validator

| The user wants to catch | `--validator` |
|---|---|
| Personal data: emails, card numbers, addresses, ID numbers | `pii-detection` |
| Input that tries to override instructions: jailbreaks, injected commands | `prompt-injection` |
| Hate, self-harm, sexual or violent content | `harmful-content` |
| Anything else the user can describe in words: a policy, a topic | `llm-as-judge` |

A server has at most one rule per validator. Two kinds of personal data go in one `pii-detection` rule with both entities.

## Log or Block

- `--action block` stops a violating call, and the caller gets `--reason`. `block` needs `--reason`, except on `prompt-injection`.
- `--action log` lets the call through and records the violation at `--severity info|warning|error` (default `info`). `--reason` goes only with `block`, `--severity` only with `log`.
- `block` fails closed: when the validator cannot answer, the call is blocked too.
- `llm-as-judge` needs the caller's user token. A caller with a PAT always gets `Unavailable` from it, so a blocking `llm-as-judge` rule blocks every call made with a PAT. Tell the user before creating one.

When the user did not say which action they want, ask ([Rule 12](../SKILL.md#critical-rules)).

## Settings

| Validator | Flags | Defaults on create | Values |
|---|---|---|---|
| `pii-detection` | `--entity <NAME>` (repeatable, or comma-separated), `--entity-threshold <NAME>=<VALUE>` (repeatable) | `Email` 0.7, `Address` 0.5; other entities 0.7 | 0 to 1 |
| `harmful-content` | `--entity <NAME>`, `--entity-threshold <NAME>=<VALUE>` | `Hate` 4, `Violence` 2; other entities 2 | 0, 2, 4 or 6 |
| `prompt-injection` | `--threshold <VALUE>` | 0.5 | 0 to 1 |
| `llm-as-judge` | `--instructions <TEXT>` and `--model <NAME>` (both required on create), `--positive-example <TEXT>` and `--negative-example <TEXT>` (up to 3 each), `--threshold <VALUE>` | 2 | 0, 2, 4 or 6 |

A create without `--entity` selects the default entities (`Email` and `Address`, or `Hate` and `Violence`): pass `--entity` for exactly what the user named. A flag another validator takes is refused, and so is an `--entity-threshold` for an entity that is not selected. Entity names, thresholds and example counts are checked before anything is sent.

### Entities

Names match ignoring case. Map the user's words to these names and never invent one: "credit cards" is `CreditCardNumber`, "SSN" is `USSocialSecurityNumber`. When nothing fits, show the list and ask.

- `pii-detection`: `Person`, `Address`, `Date`, `PhoneNumber`, `Email`, `CreditCardNumber`, `InternationalBankingAccountNumber`, `SwiftCode`, `ABARoutingNumber`, `USDriversLicenseNumber`, `UKDriversLicenseNumber`, `USIndividualTaxpayerIdentification`, `UKUniqueTaxpayerNumber`, `USBankAccountNumber`, `USSocialSecurityNumber`, `UsukPassportNumber`, `URL`, `IPAddress`.
- `harmful-content`: `Hate`, `SelfHarm`, `Sexual`, `Violence`.

### Judge Models

`--model` takes a `Name` from `uip agenthub guardrail-models list --output json`, which lists the tenant's models and needs no folder. Never guess one: a name the tenant does not offer is refused.

## Changing a Rule

- `update` applies only the flags you pass and keeps the rest: `--action log` alone keeps the threshold and the entities.
- `--entity` replaces the whole selection. Entities you keep keep their thresholds; new ones get the defaults.
- From `block` to `log` the reason is dropped and `--severity` applies (default `info`); from `log` to `block`, pass `--reason`.
- `update` writes the new rule, then deletes the old one, so the server is never unguarded, and the new rule keeps the old one's on/off state. A second run with the same flags writes nothing.
- When a delete fails, both rules apply until the old one is gone: run the same `update` again.
- `get` shows `OlderDuplicates` when the server has more than one rule of the validator (written outside the CLI); `update` and `delete` remove them.

## Removing a Rule

`uip agenthub mcp-guardrails delete --validator <VALIDATOR> --mcp <SLUG> --folder-path <FOLDER_PATH> --yes --output json` removes every rule of that validator. It never prompts: confirm with the user first ([Rule 8](../SKILL.md#critical-rules)). The CLI has no flag that turns a rule off, so off means `delete`.

When the user asks to turn a guardrail off, ask what they want: to let calls through and keep a record of violations, `update --validator <VALIDATOR> --action log` ([Changing a Rule](#changing-a-rule)); to stop screening, `delete`.

A rule that `list` shows with `Enabled: false` was switched off outside the CLI and screens nothing. The CLI cannot switch it on: `update` keeps its state, and `create` refuses while it exists. Tell the user to switch it on where it was switched off, or, if they agree, delete it and create it again.

## Rules the CLI Does Not Manage

`list` shows every rule. Rows with `Managed: false` are tool-level rules, other guardrail types or unknown validators, with their raw `Configuration`. `get`, `update` and `delete` act only on managed rules: leave the others as they are and tell the user.
