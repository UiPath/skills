# Alert Read Commands

Use this guide when the request concerns existing Insights alerts, alert activity, entitlement, or delivery metadata. All commands use the active CLI session. Do not accept or invent tenant, organization, process, alert, or delivery identifiers outside the command surface.

## Safe Output

The CLI already drops recipient IDs, delivery configuration, people-picker payloads, and raw alert `QueryJson` from these responses, so a field absent from a row is withheld by design, not missing data. Summarize delivery as type plus recipient count. Do not reconstruct a recipient list from any other command.

## Commands

### alerts list

List alert definitions visible to the current caller.

```bash
uip insights alerts list --output json
```

**Key Data fields:** `id`, `name`, `isActive`, `severity`, `engine`, `metric`, `operator`, `threshold`, `deliveryId`, `scopes`

**Use when:** User asks what alerts exist, which alerts are active, or needs an alert ID for a deeper lookup. Use `--agentic --process-key "<process-key>"` together only when the request is specifically scoped to one agentic process.

### alerts get

Get one alert definition by its positive integer ID.

```bash
uip insights alerts get <alert-id> --output json
```

**Key Data fields:** `id`, `name`, `isActive`, `severity`, `engine`, `metric`, `operator`, `threshold`, `windowSeconds`, `deliveryId`, `snoozedUntil`, `scopes`, plus `condition` on a query alert that carries a readable one

**Use when:** User asks how one alert is configured, scoped, delivered, or snoozed.

### alerts check-entitlement

Check whether the active tenant is entitled to real-time alerting.

```bash
uip insights alerts check-entitlement --output json
```

**Key Data fields:** `entitled`

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

**Key Data fields:** `alertId`, `alertName`, `triggeredAt`, `severity`, `metric`, `operator`, `threshold`, `deliveryId`

**Use when:** User asks which alerts fired, when they fired, or what condition triggered them. A row does not prove notification delivery.

### alert-history get-metrics

Get alert trigger counts by alert type and time interval.

```bash
uip insights alert-history get-metrics \
  --time-range 43200 \
  --time-grouping Day \
  --output json
```

**Key Data fields:** `groups`, `intervalEndTimes`, `counts`

**Use when:** User asks for alert trigger trends, counts, or comparisons over time. `--time-grouping` is mandatory and accepts `FifteenMinutes`, `Hour`, or `Day`. This command returns one aggregate rather than a row list, so it takes no `--limit` or `--offset`.

### alert-deliveries get

Get safe metadata for one alert delivery by its positive integer ID.

```bash
uip insights alert-deliveries get <delivery-id> --output json
```

**Key Data fields:** `id`, `type`, `recipientCount`, `tenantMatches`

**Use when:** User asks how a triggered alert is configured for delivery or whether the delivery has recipients. This command does not show recipient identities or prove a notification arrived.

## Interpretation Rules

`alerts list` and `alert-history list` support `--limit` and `--offset`; `get-metrics` and the two `get` commands do not. If `Pagination.HasMore` is true, retrieve later pages before concluding that an alert is absent. Use `--agentic` only with a non-empty `--process-key`; `--process-key` without `--agentic` is invalid.

Two alert engines produce definition rows, and `engine` says which. A `curated` alert carries the typed fields, so `metric`, `operator`, `threshold`, and `windowSeconds` describe it. A `query` alert is a stored query instead, so all four of those are null and the readable form appears as `condition` when the alert carries one. Never report a null `metric` on a query alert as missing or broken data, and do not offer to change a query alert's condition from here: that lives in the Insights UI.

`alerts get` and `alert-deliveries get` require a positive integer ID. Do not guess IDs. Use an ID returned from a list command or supplied by the user.

An empty `alerts list` response can reflect entitlement, visibility, or a tenant with no matching definitions. Run `alerts check-entitlement` when `alerts list` came back empty and the answer depends on which of those three caused it. Do not run it alongside a non-empty list, where it adds a backend entitlement call and changes nothing. Report a `false` result as one of several possible backend causes, not as proof that alerting is switched off.

Folder scopes are shown as names on `alerts list` (`N/A` for folders the caller cannot see) and as keys on `alerts get` and the agentic route. Both refer to the same folders. Map between them with `filter-folders list`, which returns `folderName` and `folderKey` for folders with Insights activity in the last 30 days.

Choose exactly one time selection for `alert-history list` or `get-metrics`: either `--time-range <minutes>`, or both `--since <epoch-seconds>` and `--until <epoch-seconds>`. Do not combine them.

History is ordered by the backend and must not be deduplicated or re-sorted. The backend may cap a result set at 1,000 rows. When `Pagination.Total` is 1,000, treat the data as potentially truncated even when `HasMore` is false.

## Investigation Workflow: Explain Why an Alert Did or Did Not Notify

1. Run `alerts get <alert-id> --output json` to inspect the alert's active state, threshold, window, scope, and snooze state.
2. Run `alert-history list` for the relevant period. State clearly whether triggers occurred.
3. If a delivery ID is available, run `alert-deliveries get <delivery-id> --output json` and report delivery type and recipient count only.
4. If the definition list is unexpectedly empty, run `alerts check-entitlement` and report the result with its ambiguity.
