# Standard Resource — contract

A **Standard Resource (SR)** is the activity metadata the UiPath UI reads to
render an Integration Service activity, and that the platform uses to execute it.
This document is the **self-contained contract** — you do not need the source
`.proto` to author an SR. It is authored as **JSON** whose keys match the message
field names below (camelCase, exactly as written).

**Completeness — full INPUT surface, MINIMAL OUTPUT set.** The two sides follow
opposite rules:

- **Inputs — everything.** The SR must describe *every* request parameter/field
  the vendor's API accepts for the operation, required AND optional. If the
  vendor accepts four optional body inputs, all four appear in the SR.
- **Outputs — only what a consumer needs.** Do NOT enumerate the vendor's full
  response tree. Emit the record **identifier(s)** — mark each `primaryKey: true`
  and list them in `metadata.primaryKey` — plus any value that is the *point* of
  the operation (the download URL a get-file operation exists to return).
  Everything else the vendor happens to return is omitted. See §4.2.

  **Why minimal here.** The outputs you can observe come from ONE live response,
  which is a sample and not a contract: optional fields may be absent from it,
  nullable ones vary by entity, and a different input may return a different
  shape. Declaring all of it asserts more than the evidence supports.

The source-of-truth rule still holds: the input list comes from the **vendor's
API schema** (OpenAPI / Swagger spec, else the vendor's public docs — the same
vendor source step 4 uses to derive the call, never IS metadata),
NOT from the generated action's typed `Input`/`Output` (which usually carries
only the fields that operation minimally needed). See §4.2 for enumeration rules
(naming, request vs response, arrays/nested objects).

**Which KEYS to set per field** is a separate axis: emit the keys documented
below (identity, type, `method`, `reference`, enum) plus the design keys (§4.3).
**All design items are in scope except `generateSchema`.** §4.3 gives derivation
rules for `design.position` (all inputs), `design.displayPattern` +
`design.enableUserOverride` (lookup inputs), `design.isMultiSelect` +
`design.delimiter` (multi-value inputs), and `design.component` (`FolderPicker`
for hierarchical lookups). For the rest — other `component` values, `isHidden`,
`fieldActions`, `textBlocks`, widgets — there is no derivation rule, so carry
over whatever the activity being migrated already declares.
Also still deferred (do NOT emit): triggers/events (polling,
webhooks, bulk), curation flags, searchables,
and `compatibleProjectTypes` (a connector activity always targets a fixed
surface). These will be layered in later.

This SR is the metadata **companion to the generated action file** — the action
supplies the call wiring (`method`, `path`, and the `scriptRef` base names
from the script files themselves), while the **input set comes from the vendor API schema**
(and outputs stay minimal per the rule above). The mapping is given inline and in
the worked example at the end.

---

## Shape at a glance

```
StandardResource
├─ name, displayName            (identity — what the activity is called)
├─ path, type, elementKey       (routing — which connector + object)
├─ executionType                (sync | async | hybrid)
└─ metadata                     (REQUIRED)
   └─ method                    (REQUIRED — the verb slot for this operation)
      └─ POST | GET | GET_BY_ID | PUT | PATCH | DELETE
         ├─ operation           (REQUIRED — Create | List | Retrieve | …)
         ├─ method              (REQUIRED — HTTP verb string)
         ├─ path                (REQUIRED — the vendor path the action calls)
         ├─ parameters[]        (URL inputs: path + query params)
         └─ responseSchema      (output shape)
fields{}                        (BODY: all request inputs + only NECESSARY outputs)
└─ <fieldName>
   ├─ name, type, displayName   (REQUIRED)
   ├─ method                    (REQUIRED — per-verb request/response flags)
   └─ reference                 (lookup / DTL — see below)
```

**Where each vendor input goes (the split):**
- Anything in the **vendor URL** — a **path** param or a **query** param — is a
  **`parameter`** (§3).
- Anything sent in the **request body** is a **`field`** with
  `method.<VERB>.request = true` (§4).
- A **response value** is a **`field`** with `method.<VERB>.response = true`.
  Every field the operation returns gets one; the identifier(s) additionally get
  `primaryKey: true` (§4.2).

`metadata.method` and `fields` are **maps/objects**, not arrays: `method` is
keyed by the verb (`POST`, `GET`, …); `fields` is keyed by the field name.
`parameters` is an array on the method.

---

## 1. `StandardResource` (top level)

| Key | Required | Type | What to set |
|---|---|---|---|
| `name` | ✅ | string | The **curated activity name** — the `Name` column from `uip is activities list` (e.g. `AddUsersToUsergroup`). NOT the v3 `objectName`, and NOT the vendor path. It is also the action file's base name and its `scriptRef`, so the three always match. |
| `displayName` | ✅ | string | Human label shown in the UI (e.g. `Add Users To User Group`). |
| `metadata` | ✅ | object | The operation definition — see §2. |
| `path` | — | string | The resource path — the vendor path in that vendor's own form, same as the `url` the action passes to `intsvc.http`. |
| `type` | — | string | Object type/category as the connector classifies it. |
| `elementKey` | — | string | The connector key (e.g. `uipath-salesforce-slack`). Identifies which connector this activity belongs to. |
| `executionType` | — | enum | `sync` (default for most activities), `async`, or `hybrid`. |
| `fields` | — | map<string, Field> | The object's fields — see §4. Keyed by field name. |
| `isHidden` | — | bool | Hide the activity from the palette; omit (defaults false) unless intentionally hiding. |
| `primaryKey` | — | (via metadata) | The identifier field(s); see §2. |

Do **not** emit: `order` (deprecated), `compatibleProjectTypes` (out of scope),
`agentIdentity` (only for `subType: "AgentExecution"`), `custom`, `experimental`.

---

## 2. `metadata` and `metadata.method`

```jsonc
"metadata": {
  "method": {
    "POST": { /* one verb slot — see the method object below */ }
  },
  "primaryKey": ["id"]        // optional: the resource's identifier field name(s)
}
```

`metadata.method` is **required** and holds **one verb slot** for the operation
this activity performs. Pick the slot from the action's HTTP method:

| Verb slot | HTTP `method` | `operation` enum | Use for |
|---|---|---|---|
| `GET` | `GET` | `List` (or `Retrieve`) | list / query |
| `GET_BY_ID` | `GET` | `Retrieve` | fetch a single record by id |
| `POST` | `POST` | `Create` | create / send |
| `PUT` | `PUT` | `Replace` | full replace |
| `PATCH` | `PATCH` | `Update` | partial update |
| `DELETE` | `DELETE` | `Delete` | delete |

Each verb slot object — **necessary fields only**:

| Key | Required | Type | What to set |
|---|---|---|---|
| `operation` | ✅ | enum | One of `Unknown, List, Retrieve, Replace, Update, Create, Delete, Upload, Download`. Match the table above. |
| `method` | ✅ | string | The HTTP verb (`GET`, `POST`, …) — same verb the action uses. |
| `path` | ✅ | string | The **verbatim vendor path** the action calls, in that vendor's own form (Slack `/usergroups.users.update`, Jira `/rest/api/3/search`). This is the routing key. |
| `description` | — | string | One-line description of the operation. |
| `operationId` | — | string | Stable id for the operation, if the connector uses one. |
| `parameters` | — | array | Request parameters — see §3. |
| `responseSchema` | — | object | Output shape — see §2.1. |
| `scriptRef` | — | string | The **base name of the action file that executes this method**, with the extension stripped (`addUsersToUserGroup.js` → `addUsersToUserGroup`). In this skill's flow the activity is executed by its generated action script, so this **is** set — to the main action file's base name. Not a path, not a filename with extension: the bare name only. You wrote that file in step 4, so use its base name (see §5.1). |

### 2.1 `responseSchema` (output shape)

Minimal descriptor of what the activity returns, so the UI can type the output:

```jsonc
"responseSchema": {
  "type": "array",            // or "object"
  "items": { "type": "object" }  // element type when type is "array"
}
```

---

## 3. `parameters` (URL inputs — path + query)

A `parameter` is a request input that travels in the **vendor URL**: a **path**
param (part of the URL path) or a **query** param (in the query string).
**Include every URL param the vendor operation defines — required AND optional.**
Inputs sent in the request **body** are NOT parameters — they are `fields` (§4),
even when optional. The keys per parameter entry:

| Key | Required | Type | What to set |
|---|---|---|---|
| `name` | ✅ | string | Parameter name as the vendor/connector expects it. |
| `description` | ✅ | string | Short description (shown as help text). |
| `type` | ✅ | enum-string | Where in the URL it goes: `path` or `query`. |
| `dataType` | ✅ | enum-string | `string \| number \| long \| float \| double \| integer \| int \| boolean \| file \| byte \| binary \| date \| datetime \| password`. |
| `displayName` | ✅ | string | Human label in the UI. |
| `required` | — | bool | Whether the input is mandatory. |
| `defaultValue` | — | any | Default, if any. |
| `format` | — | string | e.g. `int32`, `int64`, `date-time`. |
| `reference` | — | object | Lookup / DTL for this parameter — see §5. |
| `design` | — | object | Rendering — the enabled keys, see §4.3. |
| `enhancedEnum` | — | array | Fixed choice list — see §6. (Use this, **not** the deprecated `enum`.) |
| `sortOrder` | — | int | Ordering hint. |

---

## 4. `fields` (the object's fields)

`fields` is an object keyed by field name; each value is a field. A field is a
**body** value — a **request-body** input or a **response-body** value (URL
inputs are `parameters`, §3). **Include every body input the vendor operation
accepts, but only the necessary response fields** — see §4.2 for how to
choose them. The table below is the set of **keys to set per field**:

| Key | Required | Type | What to set |
|---|---|---|---|
| `name` | ✅ | string | Field name (matches the vendor body/response key). |
| `type` | ✅ | string | Field data type (`string`, `boolean`, `integer`, `object`, `array`, …). |
| `displayName` | ✅ | string | Human label. |
| `method` | ✅ | object | Per-verb request/response flags — see §4.1. |
| `description` | — | string | Help text. |
| `primaryKey` | — | bool | True if this field is the resource identifier. |
| `defaultValue` | — | any | Default value. |
| `reference` | — | object | Lookup / DTL for this field — see §5. |
| `design` | — | object | Rendering, on input fields — the enabled keys, see §4.3. |
| `enum` | — | array | Fixed choice list for the field — see §6. |
| `sortOrder` | — | int | Ordering hint. |

Do **not** emit: `order` (deprecated), curation/search fields, `events`,
`experimental`, and design keys other than `position` / `displayPattern` /
`enableUserOverride` / `isMultiSelect` / `delimiter` / `component` (§4.3).

### 4.1 `field.method` (required)

Declares, per verb, whether the field participates in the request or response.
Keyed by the same verb as the operation. **Minimal form:**

```jsonc
"method": {
  "POST": {
    "name": "POST",       // the VERB name (matches the key), not the field name
    "request": true,      // it is a request (input) field
    "required": true      // mandatory input
  }
}
```

For an **output-only** field, set `"response": true` and omit `request`. Every
field must have a `method` entry for the operation's verb. Note `name` here is the
**verb** (e.g. `"POST"`), the same as the key — not the field's own name.

### 4.2 Enumerating the full field set (from the vendor schema)

Source the field list from the vendor API schema (spec/docs), not the action's
types. (URL params — path/query — are `parameters`, §3; everything below is
body.)

- **Request-body fields — ALL of them.** Every body input the vendor accepts:
  required AND optional. Mark them `method.<VERB>.request = true`; add
  `required = true` only for the mandatory ones.
- **Response-body fields — only the NECESSARY ones.** Do not enumerate the
  vendor's full response tree. Emit only:
  - the record **identifier(s)** — mark each `primaryKey: true` and list them in
    `metadata.primaryKey` (e.g. `["usergroup.id"]`),
  - any value that is the **purpose of the operation** (e.g. the download URL a
    get-file operation exists to return).

  Mark them `method.<VERB>.response = true`. Everything else the vendor returns
  is omitted — including the envelope's own error signalling (`ok`, `error`),
  which the script detects and raises rather than surfacing as a bindable field.
- **LIST operations: the records array is the ONLY top-level output.** A list
  action returns the relevant records array with the envelope already stripped
  (the vendor's `{ ok, users: [] }` → the action returns `users`), so the SR
  declares that array — a `[*]` field (e.g. `users[*]`, `response: true`) — and
  never the envelope: no `ok`, no paging metadata, because the action omits them.
  The array's **ELEMENT fields get the same trim** — the identifier plus what the
  list exists to show, not every field the first record happened to carry.
- **Nested objects → dotted names.** Flatten a nested response value into a
  dot-path field name: `usergroup.id`. Each emitted leaf is its own entry in
  `fields`.
- **`[*]` suffix ONLY for true vendor arrays.** Use a `[*]`-suffixed name (e.g.
  `tags[*]`) only when the vendor's wire format for the field is an actual
  array/list. A `[*]` field never carries a `delimiter`.
- **Delimited-string lists keep the vendor's plain name.** When the vendor packs
  multiple values into ONE string (docs say "a comma separated string of IDs",
  example `A,B`), the field is a plain `string` field with NO `[*]` (e.g.
  `users`) — its multiplicity is expressed in design (`isMultiSelect: true` +
  `delimiter`, §4.3), not in the name or type. Read the WIRE format from the
  vendor schema; a plural noun with a separator convention is a delimited
  string, not an array.
- **The vendor decides the wire form — these two are just the common ones.**
  `delimiter` exists only to pack values into a string: a true array field
  needs NO `delimiter` (the values are sent as an actual array), a delimited
  string requires one. If the vendor defines some other form entirely (an array
  of objects, a key→value map, …), model the field to match the vendor's wire
  shape exactly — never force it into `[*]` or a delimited string.
- **`type`** is the leaf's scalar type (`string`, `boolean`, `integer`, …); for a
  true array use the element type on the `[*]` entry; for a delimited-string
  list it is `string` (the packed wire value).

A field may be **both** a request and a response field — set both flags on its
`method` entry.

### 4.3 `design` — rendering (being added incrementally)

`design` is the UX layer telling the UI how to render an **input** (a request
field or a parameter). It is added in stages; the design keys enabled now are
**`position`** (all inputs), **`displayPattern`** and **`enableUserOverride`**
(lookup inputs), **`isMultiSelect`** + **`delimiter`** (inputs that accept
multiple values), and **`component`** (`FolderPicker` for hierarchical lookups).

**`design.position` — where the input appears:**
- **required** input → `"primary"` — shown on the activity canvas.
- **optional** input → `"secondary"` — shown under "additional options".

An input is *required* when its `method.<VERB>.required` is `true` (for a field)
or its `required` is `true` (for a parameter); otherwise it is optional.

```jsonc
"design": { "position": "primary" }    // a required input
"design": { "position": "secondary" }  // an optional input
```

**`design.displayPattern` — how a resolved lookup value is shown** (lookup fields
only, i.e. fields/params that carry a `reference`). A lookup *stores* the vendor
ID (`reference.lookupValue`), but the UI should *show* a human-readable label.
Set `displayPattern` to a `{token}` pattern where the token is the **most
readable** field the lookup returns:

- Choose a name-like field from the lookup's returned fields
  (`reference.lookupNames`) — e.g. `name`, `real_name`, `display_name`, `title`,
  `label` — **never the raw id** (that is the stored `lookupValue`).
- If several readable fields exist, pick the single most descriptive one; you may
  combine tokens/literals for clarity (e.g. `"{real_name} ({id})"`), but favor the
  cleanest readable form.
- Only lookup inputs get `displayPattern`. A plain input with no `reference` gets
  `position` only.

```jsonc
"reference": { "lookupValue": "id", "lookupNames": ["id", "name"] },
"design": { "position": "primary", "displayPattern": "{name}" }
```

**`design.enableUserOverride` — allow a typed custom value** (lookup fields only).
Set `enableUserOverride: true` on lookup inputs, so the user can paste/type a raw
value (e.g. the vendor ID) instead of only picking from the resolved options.
Non-lookup inputs do not get it. **Exception: FolderPicker lookups do NOT get
`enableUserOverride`** — a folder is chosen by navigating the tree, not by typing
a raw override (see `component` below). So: flat lookups → `enableUserOverride:
true`; FolderPicker lookups → omit it.

**`design.isMultiSelect` — allow selecting more than one value.** Set
`isMultiSelect: true` when the input **semantically accepts multiple entries** —
regardless of how they travel on the wire. Both of these are multi-valued:
a **true vendor array** (the `[*]` fields), and a **delimited-string list** (the
vendor packs multiple values into one string — e.g. Slack `users`, "a comma
separated string of user IDs"). Set `isMultiSelect: false` for a genuinely
single-value input. Do NOT derive multiplicity from the declared wire type alone —
a `string`-typed field can still be a list.

**`design.delimiter` — how multi-selected values are packed into the wire
string.** Emitted ONLY for **delimited-string** inputs: set it explicitly to the
vendor's separator (Slack `users` → `delimiter: ","`). Never rely on the implicit
default (a space) — an unset delimiter silently space-joins the values and
malforms the request. A **true array** (`[*]`) field gets **NO `delimiter`** —
the values are sent as an actual array, nothing is joined, so passing a
delimiter there is meaningless. The pairing is: `[*]` + no delimiter ⇔ vendor
array; plain name + `delimiter` ⇔ vendor delimited string. These are the two
common multi-value wire forms — for anything else the vendor defines, mirror
the vendor's wire shape exactly (§4.2).

```jsonc
// single-value lookup (pick one group):
"design": { "position": "primary", "isMultiSelect": false, "enableUserOverride": true, "displayPattern": "{name}" }
// delimited-string list (vendor wants "U060...,U060..." in ONE string field `users`):
"design": { "position": "primary", "isMultiSelect": true, "delimiter": ",", "enableUserOverride": true, "displayPattern": "{real_name}" }
// true vendor array (`tags[*]`): isMultiSelect true, NO delimiter
"design": { "position": "primary", "isMultiSelect": true, "enableUserOverride": true, "displayPattern": "{name}" }
```

**`design.component` — render a hierarchical lookup as a folder browser.** When a
lookup's resolver resource is **hierarchical / folder-structured** — entries nest
as a tree of folders/containers (email folders, drive/file folders, …) rather
than a flat list — set `component: "FolderPicker"` so the UI shows a folder
browser instead of a flat dropdown. Determine "hierarchical" from the vendor API
(the resource has parent→child nesting, e.g. folders containing subfolders).

- **Flat-list lookups** (`usergroups`, `users`) → **no `component`** (default
  picker).
- **FolderPicker lookups** still resolve via `scriptRef` (the DTL script walks the
  hierarchy — see §5) and, per the rule above, **omit `enableUserOverride`**.

```jsonc
// hierarchical lookup (pick an email folder from a tree):
"design": { "position": "primary", "component": "FolderPicker", "displayPattern": "{displayName}" },
"reference": { "scriptRef": "list_mail_folders", "lookupValue": "id", "lookupNames": ["displayName"] }
```

Apply `design` only to **inputs** — request-body fields and URL parameters.
**Response-only fields get no `design`** (they are not placed on the input
canvas). Do not emit any design key other than `position`, `displayPattern`,
`enableUserOverride`, `isMultiSelect`, `delimiter`, and `component` yet.

---

## 5. `reference` — lookups and design-time lookups (DTL)

A `reference` on a field or parameter declares how a human-friendly value
resolves to a vendor-canonical ID — the metadata equivalent of the list/lookup
action on the code side. This is the **required** counterpart to the action's
step-3 lookups, and **DTL is in scope**.

```jsonc
"reference": {
  "lookupNames": ["handle", "name"],    // REQUIRED — field(s) shown to the user
  "lookupValue": "id",                  // REQUIRED — field stored as the value
  "scriptRef": "listUserGroups",        // REQUIRED — DTL resolver: the lookup action file's base name

  // optional refinements:
  "filterPattern": "displayName={filter}", // server-side filter template
  "orderBy": "ASC"                      // ASC | DESC | NONE (default ASC)
}
```

- **`scriptRef`** — a **DTL (design-time lookup)**: the **base name of the lookup
  action file** (extension stripped — `listUserGroups.js` → `listUserGroups`), not
  a path and not a filename with extension. The options are produced by running
  that action script at design time. **This activity structure uses `scriptRef`
  only** — step 4 emits a lookup action file for every lookup, and
  its base name goes here. The DTL script produces the options, including walking
  any **folder hierarchy** for a FolderPicker lookup — so no `childPath`/
  `hydration` is emitted here. (The schema also allows a direct `path` instead of
  `scriptRef` — Rule 1, §7 — but this skill does not use `path`.)
- `lookupNames` are the display column(s); `lookupValue` is the underlying value
  the activity stores (the vendor-canonical ID). Both are required.

Do **not** emit: `objectName` (obsolete), `path` (this structure uses `scriptRef`
only), `childPath`, `hydration`, `dependsOn` (deprecated), `experimental`.

### 5.1 `scriptRef` is a bare action-file base name — no SR for the lookup

A DTL lookup is served by an **action file only — it gets NO Standard resource of
its own.** The lookup action is referenced purely by its base name in the main
activity's `reference.scriptRef`. Likewise, the main activity itself is executed
by its own action file, referenced from `metadata.method.<VERB>.scriptRef` (§2)
by that file's base name.

In both places the value is the **file name with the extension stripped**
(`action.js` → `action`, `listUserGroups.js` → `listUserGroups`) — never a path,
never the extension. Which action file serves the main activity, and which serves
each DTL field, is decided by step 5,
which passes the correct base names down; it is recorded in the working dir's
the SR itself (each lookup field → its lookup
action file).

---

## 6. `enum` / `enhancedEnum` (fixed choice lists)

For a closed set of values. On a **field** use `enum`; on a **parameter** use
`enhancedEnum` (the plain `enum` on parameters is deprecated). Each entry:

```jsonc
{ "name": "Active", "value": "active", "description": "…" }  // value is REQUIRED
```

---

## 7. Contract rules

**Rule 1 — `path` XOR `scriptRef` on a `reference` (mutual exclusion).**
Exactly one of `reference.path` / `reference.scriptRef` must be set — never both,
never neither. (Enforced by the schema as
`(path != '') != (scriptRef != '')`.) **This activity structure always uses
`scriptRef`** (the DTL) and does not emit `path`; the XOR is why you must never
add both.

**Rule 2 — Required fields.** These must be present or the SR is invalid:

| Object | Required keys |
|---|---|
| `StandardResource` | `name`, `displayName`, `metadata` |
| `metadata` | `method` |
| each verb slot in `metadata.method` | `operation`, `method`, `path` |
| each `parameters[]` entry | `name`, `description`, `type`, `dataType`, `displayName` |
| each `fields{}` entry | `name`, `type`, `displayName`, `method` |
| `reference` | `lookupNames`, `lookupValue` (+ exactly one of `path`/`scriptRef`) |
| `enum` / `enhancedEnum` entry | `value` |

**Rule 3 — Closed value sets.**
- `parameter.type` ∈ `path | query` (URL locations only; body inputs are `fields`, not parameters)
- `parameter.dataType` ∈ `string | number | long | float | double | integer | int | boolean | file | byte | binary | date | datetime | password`
- `method.operation` ∈ `Unknown | List | Retrieve | Replace | Update | Create | Delete | Upload | Download`
- `executionType` ∈ `sync | async | hybrid`
- `design.position` ∈ `primary | secondary` (required inputs → `primary`, optional → `secondary`)
- `reference.orderBy` ∈ `ASC | DESC | NONE`
- The verb slot must agree with its `operation` (POST↔Create, PUT↔Replace, PATCH↔Update, GET↔List/Retrieve, GET_BY_ID↔Retrieve, DELETE↔Delete).

**Rule 4 — Do not emit deprecated keys:** `order` (on resource and field),
`reference.dependsOn`, `parameter.enum` (use `enhancedEnum`).

---

## 8. Worked example — Slack `addUsersToUserGroup` → SR

Projecting Slack `usergroups.users.update` into an SR, showing the split. For
this operation **all four inputs are body args, so they are all `fields`**
(`request: true`) — `usergroups.users.update` takes no path or query params, so
`parameters` is omitted entirely:

- **body inputs** (`usergroup`, `users`, `include_count`, `team_id`) →
  **`fields`** with `request: true`; the two ID inputs also carry DTL
  `reference`s,
- **`users` is a delimited-string list, NOT an array** — Slack's wire format is
  "a comma separated string of encoded user IDs" (`"U060R4BJ4,U060RNRCZ"`), so
  the field keeps the plain name `users` (no `[*]`), `type: "string"`, and its
  multiplicity lives in design: `isMultiSelect: true` + `delimiter: ","`. A
  `[*]` name would only be correct if Slack accepted a true array,
- **`design.position`** on each input: required inputs (`usergroup`, `users`)
  → `primary`, optional inputs (`include_count`, `team_id`) → `secondary`,
- **`design.displayPattern`** on the lookup inputs: the most readable lookup
  field — `{name}` for `usergroup`, `{real_name}` for `users`,
- **`design.enableUserOverride: true`** on both lookup inputs (a raw ID can be
  typed instead of picked),
- **no URL params** → **no `parameters`** for this operation,
- **one necessary output** → `usergroup.id` only (`response: true`,
  `primaryKey: true`, listed in `metadata.primaryKey`). The rest of Slack's
  response tree — `usergroup.name`, `usergroup.handle`, the counts, the prefs,
  and the envelope's own `ok`/`error` — is NOT enumerated: this operation exists
  to update a group, so its identifier is what a consumer needs. Response fields
  get no `design`.

Three `scriptRef`s: the activity's `metadata.method.POST.scriptRef` is the **main
action file's** base name (`add_users_to_usergroup`); each lookup field's
`reference.scriptRef` is its **lookup action file's** base name (`list_usergroups`,
`list_users`). The lookup actions get **no SR of their own**. `scriptRef` always
mirrors the real action file name — match the base name of the script you wrote.

```jsonc
{
  "name": "add_users_to_usergroup",
  "displayName": "Add Users to User Group",
  "description": "Add one or more users to a Slack user group, keeping the existing members.",
  "type": "standard",
  "elementKey": "uipath-salesforce-slack",
  "path": "/usergroups.users.update",
  "executionType": "sync",
  "metadata": {
    "primaryKey": ["usergroup.id"],
    "method": {
      "POST": {
        "operation": "Update",
        "method": "POST",
        "path": "/usergroups.users.update",
        "scriptRef": "add_users_to_usergroup",
        "description": "Add one or more users to a Slack user group, keeping the existing members.",
        // no "parameters": this operation has no path/query params — all inputs are body fields
        "responseSchema": { "type": "object" }
      }
    }
  },
  "fields": {
    // --- request body (all body inputs the vendor accepts, required AND optional) ---
    "usergroup": {
      "name": "usergroup",
      "type": "string",
      "displayName": "User group",
      "description": "The user group to add users to.",
      "method": { "POST": { "name": "POST", "request": true, "required": true } },
      "reference": {
        "scriptRef": "list_usergroups",
        "lookupValue": "id",
        "lookupNames": ["id", "name"]
      },
      "design": { "position": "primary", "isMultiSelect": false, "enableUserOverride": true, "displayPattern": "{name}" }
    },
    "users": {
      "name": "users",
      "type": "string",
      "displayName": "Users to add",
      "description": "Comma-separated encoded user IDs to add. Existing members are kept.",
      "method": { "POST": { "name": "POST", "request": true, "required": true } },
      "reference": {
        "scriptRef": "list_users",
        "lookupValue": "id",
        "lookupNames": ["id", "real_name"]
      },
      "design": { "position": "primary", "isMultiSelect": true, "delimiter": ",", "enableUserOverride": true, "displayPattern": "{real_name}" }
    },
    "include_count": {
      "name": "include_count",
      "type": "boolean",
      "displayName": "Include member count",
      "description": "Include the number of users in the response.",
      "method": { "POST": { "name": "POST", "request": true } },
      "design": { "position": "secondary" }
    },
    "team_id": {
      "name": "team_id",
      "type": "string",
      "displayName": "Team ID",
      "description": "Encoded team ID. Required only for org-wide apps.",
      "method": { "POST": { "name": "POST", "request": true } },
      "design": { "position": "secondary" }
    },

    // --- response body: ONLY the necessary output — the identifier ---
    "usergroup.id": {
      "name": "usergroup.id",
      "type": "string",
      "displayName": "User group ID",
      "description": "The ID of the updated user group.",
      "primaryKey": true,
      "method": { "POST": { "name": "POST", "response": true } }
    }
    // The rest of Slack's response tree — usergroup.name, handle, counts,
    // prefs, ok, error — is NOT enumerated. This operation exists to update a
    // group, so its identifier is the only output a consumer needs (§4.2).
  }
}
```

All lookups above use a **DTL** (`scriptRef`) — this activity structure uses
`scriptRef` only, never `path`. Both `usergroup` and `users` are **flat**
lookups, so no `component`. When a lookup's resource is instead **hierarchical**
(a folder tree), add `component: "FolderPicker"` and omit `enableUserOverride`
(the DTL script walks the tree; no `childPath`/`hydration`):

```jsonc
"parentFolderId": {
  "name": "parentFolderId",
  "type": "string",
  "displayName": "Email folder",
  "method": { "POST": { "name": "POST", "request": true, "required": true } },
  "reference": { "scriptRef": "list_mail_folders", "lookupValue": "id", "lookupNames": ["displayName"] },
  "design": { "position": "primary", "component": "FolderPicker", "displayPattern": "{displayName}" }
}
```

---

## 9. Deferred (out of scope — do not emit yet)

- **Design / UX layer — now IN scope, except `generateSchema`.** The items with
  written-down derivation rules are `design.position` (all inputs),
  `design.displayPattern` + `design.enableUserOverride` (lookup inputs),
  `design.isMultiSelect` + `design.delimiter` (multi-value inputs), and
  `design.component` (`FolderPicker` for hierarchical lookups) — see §4.3.
  Beyond those (other `component` values, `isHidden`, `fieldActions`,
  `textBlocks`, widgets, object-level design, solution-resource binding) there is
  no derivation rule to follow, so **carry over what the activity being migrated
  already declares** — `uip is resources describe <key> <objectName>` — instead of
  inventing values. `generateSchema` stays OUT: it is an api-type ObjectAction
  resolved at design time, not a static design item.
- **Triggers/events:** polling, webhooks, bulk, hydration, event types.
- **`compatibleProjectTypes`:** the activity always targets a fixed surface.
- Curation flags, searchables, `experimental`, `agentIdentity`.
