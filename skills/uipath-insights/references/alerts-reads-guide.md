# Alert Read Commands

Use this guide when the request concerns existing Insights alerts, alert activity, entitlement, or delivery metadata. All commands use the active CLI session. Do not accept or invent tenant, organization, process, alert, or delivery identifiers outside the command surface.

Keys inside `Data` are PascalCase on the wire. Read `AlertName`, not `alertName`.

## Safe Output

The CLI drops recipient IDs, delivery configuration, people-picker payloads, and the raw alert `QueryJson` from these responses, so a field absent from a row is withheld by design rather than missing data. Summarize a delivery as its type plus recipient count. Do not reconstruct a recipient list from any other command.

## Not Free Reads

`alerts list` (without `--agentic`), `alerts get`, and `alerts check-entitlement` run a backend entitlement and permission preflight that can bootstrap Insights permissions and queue a warehouse warmup. Call each one because the answer needs it, not to confirm something another command already reported. `alerts list --agentic`, `alert-history`, and `alert-deliveries get` skip the preflight.

## Commands

### alerts list

List alert definitions visible to the current caller.

```bash
uip insights alerts list --output json
```

**Key Data fields:** `Id`, `Name`, `IsActive`, `Severity`, `Engine`, `Metric`, `MetricState`, `Operator`, `Threshold`, `WindowSeconds`, `DeliveryId`, `SnoozedUntil`, `LastTriggeredAt`, `Scopes`, plus `ConditionVisible` and `Condition` on a query alert

**Use when:** User asks what alerts exist or needs an alert ID for a deeper lookup. Use `--agentic --process-key "<process-key>"` together only when the request is specifically scoped to one agentic process.

### alerts get

Get one alert definition by its positive integer ID.

```bash
uip insights alerts get <alert-id> --output json
```

**Key Data fields:** the same row `alerts list` returns.

**Use when:** The alert ID came from the user rather than a list, or the row needs re-reading after a change. A row already on hand from `alerts list` is the same row, so do not re-fetch it just to see more fields.

### alerts check-entitlement

Check whether the active tenant is entitled to real-time alerting.

```bash
uip insights alerts check-entitlement --output json
```

**Key Data fields:** `Entitled`

**Use when:** User asks whether alerting is available, or an empty alert list may be caused by entitlement filtering. A `false` response can have multiple backend causes.

### alert-history list

List alert trigger history rows in a required time window, newest first.

```bash
uip insights alert-history list --time-range 1440 --output json
```

For exact bounds, use Unix epoch seconds, unlike Jobs commands, which use milliseconds:

```bash
uip insights alert-history list \
  --since <epoch-seconds> \
  --until <epoch-seconds> \
  --output json
```

Narrow the window further with `--alert-name <name>`, `--folder-name <names...>` (folder names, never keys; repeatable), and `--severity <severities...>` (repeatable, one of `INFO`, `WARN`, `ERROR`, `NORMAL`). All three are optional and apply to `get-metrics` as well.

**Key Data fields:** `AlertId`, `AlertName`, `TriggeredAt`, `Severity`, `Metric`, `MetricState`, `Operator`, `Threshold`, `DeliveryId`

**Use when:** User asks which alerts fired, when they fired, or what condition triggered them. A row does not prove notification delivery. `TriggeredAt` is epoch seconds, not milliseconds and not an ISO timestamp, so do not reuse the Jobs convention when converting it.

### alert-history get-metrics

Get alert trigger counts by alert type and time interval.

```bash
uip insights alert-history get-metrics \
  --time-range 43200 \
  --time-grouping Day \
  --output json
```

**Key Data fields:** `Groups`, `IntervalEndTimes`, `Counts`

**Use when:** User asks for alert trigger trends, counts, or comparisons over time. `--time-grouping` is mandatory and accepts `FifteenMinutes`, `Hour`, or `Day`. Results are grouped by alert type: `Counts` holds one row of counts per entry in `Groups`, and each count pairs with the interval end time at the same index in `IntervalEndTimes`. This command returns one aggregate rather than a row list, so it takes no `--limit` or `--offset`.

### alert-deliveries get

Get safe metadata for one alert delivery by its positive integer ID.

```bash
uip insights alert-deliveries get <delivery-id> --output json
```

**Key Data fields:** `Id`, `Type`, `RecipientCount`, `TenantMatches`

**Use when:** User asks how a triggered alert is configured for delivery or whether the delivery has recipients. This command does not show recipient identities or prove a notification arrived. A `RecipientCount` of 0 is a broken delivery, not an empty read.

## Interpretation Rules

Every alert definition read returns active definitions only, and deletion is a soft delete. `IsActive` is therefore true on every row returned, and a deactivated or deleted alert is invisible to `alerts list`, `alerts get`, and the agentic route alike. Report "which alerts are inactive" as a question this surface cannot answer, never as "none".

`alerts list` and `alert-history list` support `--limit` (default 50) and `--offset`; `get-metrics` and the two `get` commands do not. Because the default is 50, a 50-row result is a full page rather than a complete list. Read `Pagination.Total` and `Pagination.HasMore`, and retrieve later pages before concluding that an alert is absent. Use `--agentic` only with a non-empty `--process-key`; `--process-key` without `--agentic` is invalid.

Two alert engines produce definition rows, and `Engine` says which. A `curated` alert carries the typed fields, so `Metric`, `MetricState`, `Operator`, `Threshold`, and `WindowSeconds` describe it. A `query` alert is a stored query instead, so all five of those are null and `Scopes` is empty. `ConditionVisible` says whether a readable form exists, and `Condition` is present only when it does. Never report a null `Metric` on a query alert as missing or broken data, and do not offer to change a query alert's condition from here: that lives in the Insights UI. An `Engine` shown as a raw number is one this CLI does not recognize, so the typed fields may not apply to it either.

`alerts get` and `alert-deliveries get` require a positive integer ID. Do not guess IDs. Use an ID returned from a list command or supplied by the user.

An empty `alerts list` response can reflect entitlement, visibility, or a tenant with no matching definitions. Run `alerts check-entitlement` when `alerts list` came back empty and the answer depends on which of those three caused it. Do not run it alongside a non-empty list, where it adds a backend entitlement call and changes nothing. Report a `false` result as one of several possible backend causes, not as proof that alerting is switched off. While entitlement is false, `alerts list` and `alerts get` return only alerts tied to a process key; the agentic route is unaffected.

A 403 on the definition routes usually means the caller's Orchestrator folder access could not be resolved rather than an entitlement problem. Check the active tenant and folder permissions before reaching for `check-entitlement`.

Folder scopes are shown as names on `alerts list` (`N/A` for folders the caller cannot see) and as keys on `alerts get` and the agentic route. Both refer to the same folders. Map between them with `filter-folders list`, which returns `FolderName` and `FolderKey` for folders with Insights activity in the last 30 days. On `alerts list` a scope covering several folders arrives as one bracketed string, so do not count scope values to count folders.

Choose one time selection for `alert-history list` or `get-metrics`: `--time-range <minutes>` for a window ending now, or `--since <epoch-seconds>` optionally paired with `--until <epoch-seconds>`. Passing `--time-range` alongside either absolute bound is rejected, and `--since` must be strictly earlier than `--until`.

`--folder-name` matches by flattening each trigger's folder list, so a trigger sitting in two of the requested folders is returned twice by `list` and counted twice by `get-metrics`, and a trigger recording no folder is dropped. Do not deduplicate the rows: `get-metrics` counts the same flattened rows server-side, so a client-side dedupe makes the two commands contradict each other.

History is ordered by the backend and must not be re-sorted. The backend caps a result set at 1,000 rows. When `Pagination.Total` is 1,000, treat the data as potentially truncated even when `HasMore` is false, and narrow the time window to see older triggers.

## Investigation Workflow: Explain Why an Alert Did or Did Not Notify

1. Run `alerts get <alert-id> --output json` to inspect the alert's threshold, window, scope, and snooze state.
2. Run `alert-history list` for the relevant period. State clearly whether triggers occurred.
3. If a delivery ID is available, run `alert-deliveries get <delivery-id> --output json` and report delivery type and recipient count only.
4. If the definition list is unexpectedly empty, run `alerts check-entitlement` and report the result with its ambiguity.

None of these four steps proves a notification reached anyone. Say so in the answer.
