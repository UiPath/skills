# Audit Exclusion Rules — Workflow Guide

Exclusion rules decide which events the audit trail stops recording. They are organization-scoped CRUD under `uip admin audit org exclusions`.

This file is the workflow and the safety contract. The command surface — every flag, `Data` shape, and output `Code` — is in [audit-commands.md → exclusions](./audit-commands.md#uip-admin-audit-org-exclusions).

Every write here suppresses evidence. Read [Before any write](#before-any-write--the-confirmation-contract) before the first `create`.

## What a rule is

A rule carries at most one **selector** per dimension:

| Dimension | Flag | Values |
|---|---|---|
| Tenant | `--exclude-tenant <guid...>` | tenant GUIDs. Repeatable. |
| EventSource | `--source <guid...>` | source GUIDs from `audit org sources`. Repeatable. |
| EventTarget | `--target <guid...>` | target GUIDs from `audit org sources`. Repeatable. |
| EventType | `--type <guid...>` | type GUIDs from `audit org sources`. Repeatable. |
| Status | `--status <status>` | `Success` or `Failure`, case-insensitive; `0` and `1` work too. **Single-valued.** |

> **The tenant selector is `--exclude-tenant`, not `--tenant-id`.** On `audit tenant sources|events|export` — and across `authz` — `--tenant-id` means "run this call against that tenant". Here the tenants are what the rule *matches*, which is a different concept, so it gets a different name. Passing `--tenant-id` to `exclusions create` is an unknown option.

Values inside one selector are OR-ed; selectors are AND-ed across dimensions. `--type <A> --type <B> --status Success` excludes successful events of type A **or** type B. A rule with no selector is refused — it would exclude every event in the organization.

`--status` takes one value, unlike the other four. A selector holding both statuses matches every event, which is exactly what omitting the flag already does.

Six facts that change what you do:

1. **Exclusion is never retroactive.** Events already in the trail stay there. A rule suppresses only events that arrive after it becomes active.
2. **Suppressed events are unrecoverable.** Deleting the rule resumes recording from that moment; it does not restore what was dropped while the rule was active.
3. **Widening a rule re-stamps its start time.** Renaming leaves `activatedOn` alone; changing which events it matches resets it, so the widened rule never covers events it did not previously match.
4. **`--inactive` excludes nothing.** That is how you stage a replacement next to the rule it takes over from, and how an inactive rule may reuse an active rule's name or match set. It is also not sticky — see [Replacing a rule](#replacing-a-rule--update-is-a-full-replacement-not-a-patch).
5. **Two things can never be excluded:** UiPath's own monitoring events, and audit-configuration changes — including changes to the exclusion rules themselves. The service refuses those selector values with `SelectorValueNotPermitted`.
6. **A rule name may not be a bare GUID.** `get`, `update` and `delete` settle name-vs-id by shape, so a GUID-shaped name could never be addressed by name — and if it matched another rule's id, those verbs would hit that other rule instead. The CLI refuses such a name locally.

`enforcement` is always `Exclude` and is not a flag. The CLI fills it in.

## Addressing a rule: by name or by policy id

`get`, `update` and `delete` take a single `<rule>` positional that accepts **either** the rule's name or its `policyId`. A GUID is used as it stands and costs no lookup; a name is matched against the organization's rules (exactly first, then case-insensitively).

```bash
uip admin audit org exclusions get "<RULE_NAME>" --output json
uip admin audit org exclusions get <POLICY_ID> --output json
```

Prefer the name the admin used — it is what the user says and what your report should echo. Reading by name costs one call, not two: the lookup's listing already carries the rule, so `get` answers from it.

A name is unique only among **active** rules, so an inactive rule may share one. When a name matches more than one rule the CLI refuses to guess:

| Outcome | `Result` | Exit | What to do |
|---|---|---|---|
| Name matches one rule | `Success` | 0 | — |
| Name matches an active **and** an inactive rule | `ValidationError` | 3 | The message lists both policy ids with their active state. Ask the user which one, or pass the id. Never pick the active one yourself — an admin staging a replacement meant the other. |
| Name matches nothing | `Failure` | 1 | Re-read `exclusions list`; the name may be stale or belong to another organization. |
| Rule listed without a `policyId` | `Failure` | 1 | Its stored document is unparseable and nothing can address it. Report it as needing a server-side fix. |

## Scope: organization only

There is no `audit tenant exclusions`. The service takes the owning organization from the validated request scope and ignores the tenant header. To limit a rule to some tenants, name them in a Tenant selector:

```bash
uip admin audit org exclusions create \
  --name "<RULE_NAME>" \
  --exclude-tenant <TENANT_ID> \
  --type <EVENT_TYPE_ID> \
  --output json
```

Reaching for `uip admin audit tenant exclusions` yields `unknown command`. It is not a missing feature to work around — re-issue against `org` with an `--exclude-tenant` selector.

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

The rule name must be unique among the organization's **active** rules (max 256 characters) and may not be a bare GUID. An inactive rule may hold a name an active rule wants.

## Step 5 — Verify, then report

Read the rule back and report from the response, not from the command you typed:

```bash
uip admin audit org exclusions get "<RULE_NAME>" --output json
```

Confirm `IsActive`, `Enforcement`, and that `Selectors` carries every dimension you intended. Report `PolicyId` and `ActivatedOn` — the instant exclusion starts. `ActivatedOn` is `null` on an inactive rule.

## Replacing a rule — `update` is a full replacement, not a patch

`update` is a PUT. Every field is resent, and anything omitted is **dropped**. Renaming a rule with `update "<RULE>" --name "<NEW_NAME>"` alone deletes all of its selectors, and a rule cannot exist with no selector — so either the call is refused or you have silently widened the rule.

**Activation is part of the replacement.** Without `--inactive` the rule comes back **active**, so editing a rule someone deliberately staged inactive starts it excluding events. Pass `--inactive` again to keep it staged — `get` first and check `IsActive` before you decide.

Procedure:

1. `exclusions get "<RULE>" --output json`.
2. Re-derive the full flag set from the response's `Selectors`, including the ones you are not changing, and add `--inactive` when `IsActive` was `false`.
3. Send `update` with `<RULE>` first, then every flag.

```bash
uip admin audit org exclusions update "<RULE>" \
  --name "<NEW_NAME>" \
  --type <EVENT_TYPE_ID> \
  --status Success \
  --output json
```

> Put `<RULE>` **before** the selector flags. Those flags are variadic, so a value written after one is read as another of its values.
>
> When renaming, `<RULE>` is the rule's **current** name (or its id) and `--name` is the new one. Passing only `--name` changes nothing about which rule is addressed.

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
- `isActive` may be omitted and defaults to **true** — the same default `create` applies without `--inactive`. To stage a rule from a file, set `"isActive": false` explicitly; on `update`, omitting it re-activates a staged rule.
- `name` is required, non-empty, trimmed before sending, and may not be a bare GUID.
- A selector carries only `type` and `values`.
- `type` is one of `Tenant`, `EventSource`, `EventTarget`, `EventType`, `Status`. Note the dimension is `Tenant` even though its flag is `--exclude-tenant`.
- `values` must be a non-empty array of strings, and only one selector per dimension is allowed. Ids are checked as GUIDs and a `Status` value is canonicalized (`success`, `0`, `Success` all store as `Success`) — the file gets exactly the checks the flags get, so the two input styles cannot disagree about what a valid rule is.
- Anything else — `policyId`, `activatedOn`, `createdOn`, `lastModifiedOn`, a typo — is rejected by name before the request is sent. Server-owned fields are refused, not ignored.
- The file must be one rule, not an export of many, and is capped at 64 KB (measured in bytes, before the read).

> **The round-trip trap.** `exclusions get` returns PascalCased keys (`PolicyId`, `IsActive`, `Selectors`) plus server-owned fields, because the CLI host PascalCases every key under `Data`. Piping that response straight into `--file` fails on both counts. Rebuild the body in camelCase with only the four write keys, or — simpler — use the inline flags for updates and keep `--file` for bodies you author yourself.

## Error codes → what to do

The service returns `application/problem+json`; the CLI folds its `detail` into `Message` and lifts the machine-readable `code` into `Context.errorCode`, which is what the `Instructions` hint keys on. The envelope also carries `ErrorCode` and `Retry`. **Read `Instructions` and act on it — do not re-send the same body and do not improvise a different verb.**

Exit codes follow the CLI contract: `0` success, `1` a service `Failure`, `2` a `403`, `3` a `ValidationError` (anything the CLI refused locally, plus a `400`).

| `code` | Meaning | Recovery |
|---|---|---|
| `RuleNotFound` | No rule with that id — or it belongs to another organization, which answers identically. | Re-read the name or id from `exclusions list`. |
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

The CLI also rejects input locally with `Result: ValidationError` and exit `3`, before any HTTP call: a missing or GUID-shaped `--name`, no selector at all, a non-GUID selector value, a `--status` outside `Success`/`Failure`/`0`/`1`, `--file` combined with inline flags, an unsupported `--file` key, a `--file` selector with an unknown dimension / empty `values` / a duplicated dimension, and an ambiguous `<rule>` name. These never reach the network. Fix the command; do not retry it unchanged.

An unreadable `--file` path is different again: a missing file is a `ValidationError`, but a permission or directory error is reported as a local I/O failure with the path in `Context`, not as a bad argument. Fix the file, not the flags.

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

1. **Operation and result** — `Listed 4 exclusion rules (3 active)`, `Created rule '<RULE_NAME>' (<POLICY_ID>)`, `Deleted rule '<RULE_NAME>'`. Lead with the name; carry the id alongside it so the user can disambiguate later.
2. **Selectors in names, not GUIDs.** Translate every id through `audit org sources`; a GUID tells the user nothing about what stopped being recorded.
3. **Active state and start instant** — `IsActive` plus `ActivatedOn`, or "staged, excluding nothing" for an inactive rule.
4. **What this means for the trail** — which events stop being recorded, and from when. On a delete: recording resumes now; the gap stays.
5. **Next step** — offer one and wait. Do not chain another write.

## Anti-patterns

1. **Do NOT reach for `audit tenant exclusions`.** The surface is org-only; scope a rule to tenants with `--exclude-tenant`.
2. **Do NOT pass `--tenant-id` to an exclusions command.** It is the read verbs' "run against this tenant" flag and is not an option here; the selector is `--exclude-tenant`.
3. **Do NOT `update` with only the field you are changing.** It is a full replacement — `get` first and resend every selector.
4. **Do NOT drop `--inactive` when replacing a staged rule.** `update` re-activates by default, which turns a rule someone parked into one that suppresses events.
5. **Do NOT feed a `get` response back into `--file`.** PascalCased keys and server-owned fields are both rejected.
6. **Do NOT mix `--file` with inline flags.**
7. **Do NOT pass `--status` twice** to exclude both outcomes. It is single-valued, and a rule matching both statuses is the same as one with no Status selector.
8. **Do NOT invent selector GUIDs**, and do not assume a tenant GUID from another organization will error — it is accepted and matches nothing.
9. **Do NOT create a rule without a selector** to mean "everything", and do not interpret a vague "mute the audit noise" as authorization to do so.
10. **Do NOT pick a rule yourself when a name is ambiguous.** An active and an inactive rule may share a name; ask which one, or use the id.
11. **Do NOT name a rule with a bare GUID.** It is refused, because `get`/`update`/`delete` would read it as a policy id.
12. **Do NOT retry a `SelectorValueNotPermitted` refusal** with a different spelling of the same target. Audit-configuration and UiPath monitoring events are permanently non-excludable.
13. **Do NOT treat a 404 on `list` as a bad command.** It means the service has no exclusion surface in this organization; report and stop.
14. **Do NOT present a created rule as retroactive.** It never removes an event already recorded.
