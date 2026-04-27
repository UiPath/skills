# Activities

Activities are pre-built actions available for each connector (e.g., "Send Message", "Create Issue"). They represent specific operations the connector supports. Activities include both **actions** (non-trigger) and **triggers** (event listeners).

> Full command syntax and options: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific usage patterns are shown inline below.

---

## List Activities (Non-Trigger)

```bash
uip is activities list "<connector-key>" --output json
```

This lists **non-trigger activities only** (actions, not event listeners).

## List Trigger Activities

```bash
uip is activities list "<connector-key>" --triggers --output json
```

The `--triggers` flag filters to **trigger activities only** (`isTrigger=true`). These represent events the connector can fire (e.g., "Record Created", "Record Updated").

The **Operation** field on trigger activities indicates the trigger type:
- **CREATED** / **UPDATED** / **DELETED** — CRUD event triggers (require an intermediate "objects" step to discover which objects support the operation)
- Other values — custom event triggers (skip directly to metadata)

> When a trigger activity is selected, proceed to [triggers.md](triggers.md) for the trigger metadata workflow.

## Response Fields

| Field | Description |
|---|---|
| **`Name`** | Activity identifier |
| `DisplayName` | Human-readable name (e.g., "HTTP Request", "Send Message") |
| `Description` | What the activity does |
| **`ObjectName`** | The resource object this activity operates on (use as `<object-name>` in trigger describe for non-CRUD triggers) |
| `MethodName` | HTTP method used (GET, POST, etc.) |
| **`Operation`** | Operation type — for triggers, this is the event type (CREATED, UPDATED, DELETED, or custom) |
| `IsCurated` | Whether this is a curated/recommended activity |

---

## When to Use Activities vs Resources vs Triggers

- **Activities** = named actions (e.g., "Send Email"). Discovered via `is activities list`.
- **Triggers** = event listeners (e.g., "Record Created"). Discovered via `is activities list --triggers`. Metadata via `is triggers objects` / `is triggers describe`. See [triggers.md](triggers.md).
- **Resources** = data objects with CRUD (e.g., "Account"). Discovered via `is resources list`. Executed via `is resources execute <verb>`.

> After listing activities, present the available actions to the user. Activities provide context for what a connector can do — use this to guide which resource operations, triggers, or workflow actions to pursue.

---

## Filter Trees (CEQL)

Some IS activities — most notably **List All Records** and other list/query operations — accept a server-side filter expressed in **CEQL** (Connector Expression Query Language). As with trigger filters (which compile to JMESPath), CEQL filters are authored as a **structured filter tree** and the CLI compiles them to a CEQL string. Authoring as a tree keeps the CLI and Studio Web in lockstep so the activity round-trips cleanly when re-opened in SW.

The CLI persists both halves of the contract from a single `filter` input:

- **Runtime side** — the compiled CEQL string lands at `inputs.detail.queryParameters.where`. The IS connector reads `queryParameters.where` when executing List All Records and similar list/query operations.
- **Design-time side** — the structured tree is embedded under `inputs.detail.configuration`'s `essentialConfiguration.savedFilterTrees.where`. Studio Web reads this on open to re-render the filter widget; without it the filter UI shows up empty even though the runtime call still works.

Pass `filter` (the structured tree) and the CLI emits both halves in lockstep. Passing both `filter` and `queryParameters.where` is rejected at validation time — single source of truth.

### Tree shape

Identical to the trigger filter tree — the same `FilterTree` / `Filter` / `WorkflowValue` types are used; only the compiler output (CEQL vs JMESPath) differs.

```jsonc
{
  "groupOperator": 0,             // 0 = And, 1 = Or — combines sibling filters/groups
  "index": 0,                     // ordering index within parent (root is 0)
  "filters": [                    // leaf conditions at this level
    {
      "id": "<fieldName>",        // resource field name from `is resources describe`
      "operator": "<Operator>",   // PascalCase, see operator table below
      "value": {
        "value": <typed value>,   // string / number / boolean / ISO-8601 date-time / array
        "rawString": "\"...\"",   // verbatim user-entered text (with quotes for strings)
        "isLiteral": true         // literals only — expression values are not yet supported
      }
    }
  ],
  "groups": []                    // optional: nested subgroups (same shape as root)
}
```

A no-op filter — used when the user wants to list all records without restriction — is `null` or `{"groupOperator": null, "index": 0, "filters": []}`. Prefer **omitting** the `filter` field entirely.

### Compiled CEQL output

The CLI compiles each leaf to `<field> <op> <value>` (or `<field> <function>` for null checks) and joins siblings with the group operator. String values are wrapped in single quotes; booleans, numerics, and enums are passed bare.

| Operator | CEQL token | Notes |
|---|---|---|
| `Equals` | `=` | |
| `NotEquals` | `!=` | |
| `LessThan` / `LessThanOrEqual` / `GreaterThan` / `GreaterThanOrEqual` | `<` / `<=` / `>` / `>=` | Numeric / date-time |
| `Contains` / `NotContains` | `Contains` / `Not Contains` | Substring (string) |
| `StartsWith` / `NotStartsWith` / `EndsWith` / `NotEndsWith` | `Starts With` / `Not Starts With` / `Ends With` / `Not Ends With` | String |
| `Like` / `NotLike` | `Like` / `Not Like` | Pattern match (connector-specific) |
| `In` / `NotIn` | `In` / `Not In` | Membership — `value.value` is a list; rendered as `(v1, v2, …)` |
| `IsNull` / `IsNotNull` | `Is Null` / `Is Not Null` | No `value` needed |
| `Is` / `IsNot` | `=` against literal `true` / `false` | Boolean shortcut |

Logical operators between siblings:

| `groupOperator` | CEQL token |
|---|---|
| `0` (And) | ` AND ` |
| `1` (Or) | ` OR ` |

### Examples

**Active accounts only:**

```json
{
  "groupOperator": 0, "index": 0,
  "filters": [
    { "id": "Status", "operator": "Equals",
      "value": { "value": "Active", "rawString": "\"Active\"", "isLiteral": true } }
  ]
}
```
→ CEQL: `Status = 'Active'`

**Score ≥ 80 AND Region in (EMEA, APAC):**

```json
{
  "groupOperator": 0, "index": 0,
  "filters": [
    { "id": "Score", "operator": "GreaterThanOrEqual",
      "value": { "value": 80, "rawString": "80", "isLiteral": true } },
    { "id": "Region", "operator": "In",
      "value": { "value": ["EMEA", "APAC"], "rawString": "[\"EMEA\",\"APAC\"]", "isLiteral": true } }
  ]
}
```
→ CEQL: `Score >= 80 AND Region In ('EMEA', 'APAC')`

**Subject contains "urgent" AND (owner = me OR owner is null):**

```json
{
  "groupOperator": 0, "index": 0,
  "filters": [
    { "id": "Subject", "operator": "Contains",
      "value": { "value": "urgent", "rawString": "\"urgent\"", "isLiteral": true } }
  ],
  "groups": [
    {
      "groupOperator": 1, "index": 1,
      "filters": [
        { "id": "OwnerId", "operator": "Equals",
          "value": { "value": "${me.id}", "rawString": "\"${me.id}\"", "isLiteral": false } },
        { "id": "OwnerId", "operator": "IsNull" }
      ]
    }
  ]
}
```
→ CEQL: `Subject Contains 'urgent' AND (OwnerId = ${me.id} OR OwnerId Is Null)`. Non-literal values (`isLiteral: false`) are emitted as `${expression}` placeholders for runtime resolution.

### How to build a CEQL filter tree

1. Run `uip is resources describe "<connector-key>" "<objectName>" --connection-id "<id>" --operation List` to read the resource's filterable fields (`requestFields` / `parameters` flagged as filterable).
2. For each user-intent condition, pick a matching field `name` from that response — using an unknown field name will be rejected by the CLI at configure time.
3. Choose an operator based on the field type (see operator table). Date-time fields take ISO-8601 strings; enums take the literal enum value.
4. Build one leaf per condition; place multiple conditions under the same `groupOperator` (0 for AND, 1 for OR).
5. If you need mixed AND/OR logic, use nested `groups`.
6. Wrap values in a `WorkflowValue` object with `value`, `rawString`, `isLiteral`. Strings, numbers, booleans, dates, and arrays are all valid `value` types; only `isLiteral: true` is currently supported by activity-side compilation.
7. If the resource doesn't expose filterable fields, the activity does not support server-side filtering — omit `filter` and filter downstream in the flow (e.g. with a Script node).

### What NOT to generate

| Invalid input | Why it fails | Valid replacement |
|---|---|---|
| `"filter": "Status = 'Active'"` | Bare CEQL string — `filter` must be an object. | Structured tree with `filters: [...]`. |
| `"filterExpression": "..."` | That field is reserved for the trigger (JMESPath) path. | Use `filter` (CEQL tree) for activities. |
| `{ "operator": "equals", ... }` | Operator is case-sensitive. | `"operator": "Equals"` |
| `{ "value": "Active" }` on a leaf | Bare string — must be wrapped in the `WorkflowValue` object. | `{ "value": { "value": "Active", "rawString": "\"Active\"", "isLiteral": true } }` |
| `{ "id": "fields.Status", ... }` | `fields.` prefix — use the bare field name from `is resources describe`. | `{ "id": "Status", ... }` |
| `In` operator with a single value not in a list | `In` expects an array `value`. | Use `Equals`, or pass `value: ["one"]`. |
