# Audit Exclusion Rules — Workflow Guide

Exclusion rules decide which events the audit trail stops recording. They are organization-scoped CRUD under `uip admin audit org exclusions`.

This file is the workflow and the safety contract. The command surface — every flag, `Data` shape, and output `Code` — is in [audit-commands.md → exclusions](./audit-commands.md#uip-admin-audit-org-exclusions).

Every write here suppresses evidence. Read [Before any write](#before-any-write--the-confirmation-contract) before the first `create`.

## What a rule is

A rule carries at most one **selector** per dimension:

| Dimension | Flag | Values |
|---|---|---|
| Tenant | `--tenant-id <guid...>` | tenant GUIDs |
| EventSource | `--source <guid...>` | source GUIDs from `audit org sources` |
| EventTarget | `--target <guid...>` | target GUIDs from `audit org sources` |
| EventType | `--type <guid...>` | type GUIDs from `audit org sources` |
| Status | `--status <status...>` | `Success` or `Failure` |

Values inside one selector are OR-ed; selectors are AND-ed across dimensions. `--type <A> --type <B> --status Success` excludes successful events of type A **or** type B. A rule with no selector is refused — it would exclude every event in the organization.

Five facts that change what you do:

1. **Exclusion is never retroactive.** Events already in the trail stay there. A rule suppresses only events that arrive after it becomes active.
2. **Suppressed events are unrecoverable.** Deleting the rule resumes recording from that moment; it does not restore what was dropped while the rule was active.
3. **Widening a rule re-stamps its start time.** Renaming leaves `activatedOn` alone; changing which events it matches resets it, so the widened rule never covers events it did not previously match.
4. **`--inactive` excludes nothing.** That is how you stage a replacement next to the rule it takes over from, and how an inactive rule may reuse an active rule's name or match set.
5. **Two things can never be excluded:** UiPath's own monitoring events, and audit-configuration changes — including changes to the exclusion rules themselves. The service refuses those selector values with `SelectorValueNotPermitted`.

`enforcement` is always `Exclude` and is not a flag. The CLI fills it in.

## Scope: organization only

There is no `audit tenant exclusions`. The service takes the owning organization from the validated request scope and ignores the tenant header. To limit a rule to some tenants, name them in a Tenant selector:

```bash
uip admin audit org exclusions create \
  --name "<RULE_NAME>" \
  --tenant-id <TENANT_ID> \
  --type <EVENT_TYPE_ID> \
  --output json
```

Reaching for `uip admin audit tenant exclusions` yields `unknown command`. It is not a missing feature to work around — re-issue against `org` with a `--tenant-id` selector.

## Permissions

| Operation | Needs |
|---|---|
| `list`, `get` | audit-read permission (`Audit.Read` scope on the token) |
| `create`, `update`, `delete` | a **user** token whose identity is in the organization's Administrators group |

A service-to-service (client-credentials / external-app) token reads rules but is refused on every write. On a 403 from a write, check the token type before checking group membership.

## Step 1 — Probe availability before promising anything

This surface is newer than the rest of `uip admin audit`. Establish it exists before planning a change around it:

```bash
uip admin audit org exclusions list --output json
```

| Response | Meaning | Do this |
|---|---|---|
| `Result: Success` | Available. | Continue. |
| `unknown command 'exclusions'` | The installed CLI predates the feature. | Report the CLI is too old and tell the user to upgrade `@uipath/cli`. Do **not** guess another verb, and do **not** fall back to `uip or audit-logs` — it has no exclusion surface. |
| `HTTP 404` on `list` | The CLI has the command; the audit service in this organization does not yet expose `/api/EventConfig/rules`. | Report that exclusion rules are unavailable in this organization and stop. Retrying and re-wording the command will not change it. |
| `HTTP 401` | Token lacks `Audit.Read`. | Tell the user to run `uip logout && uip login`. Never retry a 401 (Critical Rule 29). |

## Step 2 — Discover the selector ids

Never invent a source, target, or type GUID (Critical Rule 26). Read the live catalog:

```bash
uip admin audit org sources --output json
```

A tenant GUID that is not in this organization is **accepted** by the service and matches nothing, so a typo becomes a rule that silently never fires. Resolve tenant ids with `uip admin tenants list --output json` and echo the tenant name you resolved.

## Step 3 — Propose, then confirm

Before the write, show the user:

- the rule name;
- every selector, with the **names** from the sources catalog — not bare GUIDs;
- what stops being recorded in plain words ("successful `<EVENT_TYPE_NAME>` events from `<TENANT_NAME>` will no longer be recorded");
- that events already recorded are unaffected, and events suppressed from now on cannot be recovered.

Wait for explicit confirmation. See [Before any write](#before-any-write--the-confirmation-contract).

## Step 4 — Create

```bash
uip admin audit org exclusions create \
  --name "<RULE_NAME>" \
  --type <EVENT_TYPE_ID> \
  --status Success \
  --output json
```

Add `--inactive` to save the rule without activating it.

The rule name must be unique among the organization's **active** rules (max 256 characters). An inactive rule may hold a name an active rule wants.

## Step 5 — Verify, then report

Read the rule back and report from the response, not from the command you typed:

```bash
uip admin audit org exclusions get <POLICY_ID> --output json
```

Confirm `IsActive`, `Enforcement`, and that `Selectors` carries every dimension you intended. Report `PolicyId` and `ActivatedOn` — the instant exclusion starts. `ActivatedOn` is `null` on an inactive rule.

## Replacing a rule — `update` is a full replacement, not a patch

`update` is a PUT. Every field is resent, and anything omitted is **dropped**. Renaming a rule with `update <POLICY_ID> --name "<NEW_NAME>"` alone deletes all of its selectors, and a rule cannot exist with no selector — so either the call is refused or you have silently widened the rule.

Procedure:

1. `exclusions get <POLICY_ID> --output json`.
2. Re-derive the full flag set from the response's `Selectors`, including the ones you are not changing.
3. Send `update` with `<POLICY_ID>` first, then every flag.

```bash
uip admin audit org exclusions update <POLICY_ID> \
  --name "<NEW_NAME>" \
  --type <EVENT_TYPE_ID> \
  --status Success \
  --output json
```

> Put `<POLICY_ID>` **before** the selector flags. The selector flags are variadic, so an id written after one is read as another of its values.

Changing the match set re-stamps `ActivatedOn`; renaming alone does not.

## Staging a replacement

To swap a rule without a recording gap and without a name collision:

1. `create` the replacement with `--inactive` — it excludes nothing and may reuse the live rule's name or match set.
2. Have the user review it with `exclusions get`.
3. `delete` the old rule.
4. `update` the replacement without `--inactive`, resending every flag (see above).

`--inactive` is also the answer to an `OverlappingRuleExists` rejection: the new rule is staged alongside the rule that already covers it.

## The `--file` body contract

`--file <path>` supplies the whole body instead of the inline flags. The two input styles **cannot be mixed** — `--file` plus any inline flag is rejected before the file is read, because merging them would leave it ambiguous which input owns a field both set.

A body carries exactly four keys, in **camelCase**:

```json
{
  "name": "<RULE_NAME>",
  "enforcement": "Exclude",
  "isActive": true,
  "selectors": [
    { "type": "EventType", "values": ["<EVENT_TYPE_ID>"] },
    { "type": "Status", "values": ["Success"] }
  ]
}
```

- `enforcement` may be omitted; the CLI fills in the only legal value.
- A selector carries only `type` and `values`.
- `type` is one of `Tenant`, `EventSource`, `EventTarget`, `EventType`, `Status`.
- Anything else — `policyId`, `activatedOn`, `createdOn`, `lastModifiedOn`, a typo — is rejected by name before the request is sent. Server-owned fields are refused, not ignored.
- The file must be one rule, not an export of many, and is capped at 64 KB.

> **The round-trip trap.** `exclusions get` returns PascalCased keys (`PolicyId`, `IsActive`, `Selectors`) plus server-owned fields, because the CLI host PascalCases every key under `Data`. Piping that response straight into `--file` fails on both counts. Rebuild the body in camelCase with only the four write keys, or — simpler — use the inline flags for updates and keep `--file` for bodies you author yourself.

## Error codes → what to do

The service returns `application/problem+json`; the CLI surfaces its `detail` as `Message` and keys the `Instructions` hint on the machine-readable `code`. **Read `Instructions` and act on it — do not re-send the same body and do not improvise a different verb.**

| `code` | Meaning | Recovery |
|---|---|---|
| `RuleNotFound` | No rule with that id — or it belongs to another organization, which answers identically. | Re-read the id from `exclusions list`. |
| `DuplicateRuleName` | Another **active** rule holds that name. | Pick a different `--name`, or update the existing rule. An inactive rule may keep a name in use. |
| `OverlappingRuleExists` | An active rule already excludes everything this one would; its id is in the message. | Delete or narrow that rule, or save this one with `--inactive`. |
| `RuleLimitExceeded` | The organization is at its rule cap. | Delete a rule before adding another. Report the cap to the user rather than pruning rules you did not create. |
| `EmptySelectorsNotAllowed` | The body constrains nothing. | Pass at least one selector flag. |
| `InvalidSelectorValue` | A value is not the right shape. | Selector values are GUIDs; `--status` takes `Success` or `Failure`. |
| `UnknownSelectorValue` | No audit metadata defines that id. | Re-discover ids with `audit org sources`. |
| `SelectorValueNotPermitted` | The target is protected — UiPath monitoring events or audit-configuration changes. | Narrow the rule to events the organization owns. Report the refusal; it is by design and has no workaround. |
| `SelectorLimitExceeded` | Too many selectors, or too many values in one. | Split into several narrower rules. |
| `RuleModifiedConcurrently` | Another admin changed the rule mid-call. | `exclusions get` again and retry once with the fresh state. |
| `InvalidRequest` | Rejected before the rule logic; the message names the field. | Fix the named field. Server-owned fields may not be sent. |

The CLI also rejects bodies locally with `Result: ValidationError` — a missing `--name`, a non-GUID selector value, a `--status` outside `Success`/`Failure`, `--file` combined with inline flags, an unsupported `--file` key. These never reach the network. Fix the command; do not retry it unchanged.

## When an investigation comes up empty, check the exclusions

An active rule makes matching events absent from `audit <scope> events` **and** from `audit <scope> export`. Nothing in either response says an event was suppressed.

So when a targeted query returns nothing and the user expected a hit, list the rules before concluding the action never happened:

```bash
uip admin audit org exclusions list --output json
```

If a rule covers the source, target, type, or status you searched, say so explicitly: the trail has a deliberate gap for those events from `ActivatedOn` onward. This does **not** license naming an actor the query did not return (Critical Rule 27b) — it explains the silence, it does not fill it.

## Before any write — the confirmation contract

`create`, `update`, and `delete` change what the organization's audit trail records. Treat them like `ip-restriction enforcement enable` (Critical Rule 31), not like a read.

Before the first write of a session, state the impact and get explicit confirmation:

> "This stops the audit trail recording `<WHAT>` from the moment the rule activates. Events already recorded are unaffected, but events suppressed from then on cannot be recovered — deleting the rule later resumes recording, it does not restore the gap. Exclusion rules are organization-wide. Proceed?"

Rules that follow from that:

- **Never create or widen a rule the user did not ask for**, and never widen one "to be safe". If the user's description is broader than what the noise justifies, propose the narrow rule and say what you left out.
- **Never delete a rule you did not create** as a way past `RuleLimitExceeded` or `OverlappingRuleExists`. Report the conflict and let the user choose.
- **Never chain writes.** One rule, verified and reported, then wait.
- **Compliance framing:** if the user's stated reason is volume or cost, note that an exclusion is the wrong tool for a retention question — it destroys the record rather than shortening its life. Say it once; if the user reaffirms, proceed with the narrow rule.

## Output etiquette — after an exclusions call

1. **Operation and result** — `Listed 4 exclusion rules (3 active)`, `Created rule '<RULE_NAME>' (<POLICY_ID>)`, `Deleted rule '<RULE_NAME>'`.
2. **Selectors in names, not GUIDs.** Translate every id through `audit org sources`; a GUID tells the user nothing about what stopped being recorded.
3. **Active state and start instant** — `IsActive` plus `ActivatedOn`, or "staged, excluding nothing" for an inactive rule.
4. **What this means for the trail** — which events stop being recorded, and from when. On a delete: recording resumes now; the gap stays.
5. **Next step** — offer one and wait. Do not chain another write.

## Anti-patterns

1. **Do NOT reach for `audit tenant exclusions`.** The surface is org-only; scope a rule to tenants with `--tenant-id`.
2. **Do NOT `update` with only the field you are changing.** It is a full replacement — `get` first and resend every selector.
3. **Do NOT feed a `get` response back into `--file`.** PascalCased keys and server-owned fields are both rejected.
4. **Do NOT mix `--file` with inline flags.**
5. **Do NOT invent selector GUIDs**, and do not assume a tenant GUID from another organization will error — it is accepted and matches nothing.
6. **Do NOT create a rule without a selector** to mean "everything", and do not interpret a vague "mute the audit noise" as authorization to do so.
7. **Do NOT retry a `SelectorValueNotPermitted` refusal** with a different spelling of the same target. Audit-configuration and UiPath monitoring events are permanently non-excludable.
8. **Do NOT treat a 404 on `list` as a bad command.** It means the service has no exclusion surface in this organization; report and stop.
9. **Do NOT present a created rule as retroactive.** It never removes an event already recorded.
