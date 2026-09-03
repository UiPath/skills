# Design: Minimal metadata file → Standard Resource generator

**Status:** ACCEPTED & IMPLEMENTED — the generator ships in the `uip` CLI as
`uip is activities metadata build`, and the workflow (activity-generation.md)
authors `activity/<name>.min.json` then runs it. This doc is the authoritative
min-file schema (§3) and derivation rulebook (§5).

## 1. Goal

Split SR generation into two halves with a hard boundary:

- **Judgment (LLM):** read the vendor API schema and the generated action, and
  distill the *irreducible facts* into a small, reviewable file —
  `activity.min.json`.
- **Mechanics (command):** a deterministic generator
  (`uip is activities metadata build`) expands
  that file into the full Standard Resource, applying every rule the contract
  fixes (position, `[*]` vs delimiter, lookup design, primaryKey collection,
  verb↔operation, …) identically every time, and validates the result.

Why: hand-authoring the whole SR JSON against the contract re-applies every
mechanical rule per generation — each a chance to drift. With the
split, a rule change is one script edit, not a prompt hope. The min-file also
becomes the **reviewable record** of every judgment the metadata encodes
(replacing the prose/README-based `scriptRef` passing flagged earlier).

```
vendor schema ──┐
                ├─(LLM judgment)─► activity.min.json ─(script)─► <activity>.json (SR)
action files ───┘                        ▲                            │
                                from steps 3 and 4              validated
                                scriptRef base names                 against contract
```

## 2. What is irreducible (goes in the file) vs derived (script)

| Author supplies | Why it lives in the file |
|---|---|
| activity `name`, `description`, `elementKey`, `vendorPath`, `httpMethod` | vendor/authoring knowledge |
| main `scriptRef` + each lookup's `scriptRef` | the script file base names, from steps 3–4 |
| per input: `name`, `type`, `in`, `required`, `description` | vendor schema |
| per input: `isArray` | vendor WIRE format (true array vs packed string) |
| per input: the **full `design` block, verbatim** | authored per the contract's §4.3 rules — passed through untouched so FUTURE design keys need no script change |
| per lookup: `value`, `display[]` | vendor + UX judgment (readable field) |
| per output: `name` (dotted), `type`, `primaryKey`, `isArray` | vendor response schema |
| `enum` values, `defaultValue`, `returned` | vendor schema |

Everything else — `method` blocks, `metadata.primaryKey`, `responseSchema`,
`[*]` suffixes, the parameters/fields split, displayName fallbacks — is
**rule-derived** by the script (§5). Design is deliberately NOT derived: the
author writes it and the script passes it through verbatim, VALIDATING the known
rules (position↔required, no delimiter on arrays, FolderPicker↔override) while
letting unknown/future design keys through untouched.

## 3. The minimal input file — `activity.min.json`

### 3.1 `activity` block

```jsonc
"activity": {
  "name": "add_users_to_usergroup",          // REQUIRED — activity/object name
  "displayName": "Add Users to User Group",  // optional → humanize(name)
  "description": "Add users to a Slack user group, keeping existing members.",  // REQUIRED
  "elementKey": "uipath-salesforce-slack",   // REQUIRED — connector key
  "vendorPath": "/usergroups.users.update",  // REQUIRED — the vendor's own path form
  "httpMethod": "POST",                      // REQUIRED — GET|GET_BY_ID|POST|PUT|PATCH|DELETE
  "operation": "Update",                     // optional → verb↔operation default (§5)
  "scriptRef": "add_users_to_usergroup"      // REQUIRED — MAIN action file base name
}
```

### 3.2 `inputs[]` — one entry per vendor input (ALL of them, required AND optional)

```jsonc
{
  "name": "users",              // REQUIRED — vendor's own name, PLAIN (no [*])
  "type": "string",             // REQUIRED — wire scalar type (element type when isArray)
  "in": "body",                 // REQUIRED — path | query | body
  "required": true,             // optional, default false
  "description": "Comma-separated encoded user IDs to add.",  // REQUIRED
  "displayName": "Users to add",// optional → humanize(name)

  "isArray": true,              // ONLY when the vendor accepts a TRUE array → "[*]" name.
                                // A delimited-string list is NOT an array: plain name,
                                // type "string", and design.delimiter below.

  "returned": true,             // also present in the response (round-trip)
  "primaryKey": true,           // identifier — valid ONLY with returned:true (or on outputs)
  "enum": [ { "name": "Active", "value": "active" } ],   // optional closed set
  "defaultValue": "...",        // optional

  "lookup": {                   // present ⇔ the value is resolved at design time (DTL)
    "scriptRef": "list_users",  // REQUIRED — lookup action file base name
    "value": "id",              // REQUIRED — field stored (vendor-canonical ID)
    "display": ["id", "real_name"]   // REQUIRED — the reference.lookupNames
  },

  // REQUIRED on every input — the FULL design block, authored per the
  // contract's §4.3 rules and passed through to the SR VERBATIM. The script
  // never derives design; future design keys are added here, no script change.
  "design": {
    "position": "primary",      // required input → primary; optional → secondary
    "isMultiSelect": true,      // input accepts multiple entries
    "delimiter": ",",           // delimited-string list only — NEVER with isArray
    "enableUserOverride": true, // flat lookups only (NOT with FolderPicker)
    "displayPattern": "{real_name}",  // lookups: most readable lookup field
    "component": "FolderPicker" // hierarchical (folder-tree) lookups only
  }
}
```

### 3.3 `outputs[]` — only the necessary response fields

**Not the vendor's full response tree.** Emit the record identifier(s) — they get
`primaryKey: true` — plus any value that is the *point* of the operation (the
download URL a get-file operation exists to return). Omit everything else the
vendor happens to return.

The response you captured is one sample, not the vendor's contract: optional
fields may be absent from it, nullable ones vary by entity, and a different input
may return a different shape. Enumerating all of it claims more than you know.

```jsonc
{ "name": "usergroup.id",       // dotted path for nested values
  "type": "string",
  "primaryKey": true,           // → field.primaryKey + metadata.primaryKey
  "isArray": false,             // true → "[*]" name (a true response array)
  "description": "The ID of the updated user group." }
```

**LIST operations:** exactly ONE output entry — the records array the action
returns (`isArray: true`), e.g. `{ "name": "users", "type": "object",
"isArray": true, "description": "..." }` → SR field `users[*]`. Nothing else
(no `ok`, no envelope metadata): the action strips the envelope, so no other
output exists.

## 4. Redundancy rules (an input that is also an output)

The author writes every vendor input **exactly once**. `returned: true` declares
round-tripping; the script decides the expansion:

| Input kind + `returned: true` | Script emits |
|---|---|
| `in: body` | ONE merged field: `method.<VERB>` gets `request: true` AND `response: true` |
| `in: path` / `query` | TWO entries: the `parameters[]` entry, PLUS an auto-generated response `fields{}` entry (same name/type/description; no `design`, no `reference`, no `required` — but `primaryKey` survives) |

`outputs[]` lists only response-ONLY fields. Defensive merge: if a name appears
in both `inputs` and `outputs` anyway, the script merges (flags OR'd, the input's
`description`/`design`/`lookup` win) instead of erroring.

**`primaryKey` placement:** it is a response-side fact. Valid on an `outputs[]`
entry or on an input with `returned: true`; **invalid on a request-only input**
(validation error). `metadata.primaryKey` is always collected from the *expanded*
`fields{}` — whichever route the identifier arrived by.

## 5. Derivation rules (the script's rulebook)

```
in: path|query                → parameters[] entry (type = in, dataType = type)
in: body                      → fields{} request entry
outputs / returned            → fields{} response entry (see §4)

isArray                       → name gets "[*]" (true vendor arrays only; a
                                delimited-string list keeps its plain name and
                                declares design.delimiter in its design block)

required: true                → method.<VERB>.required / param.required = true

lookup                        → reference { scriptRef, lookupValue: value, lookupNames: display }
                                (never objectName / path / childPath / hydration)

design                        → PASSED THROUGH VERBATIM from the min-file entry —
                                the script derives NOTHING here. The author writes
                                it per contract §4.3; unknown/future design keys
                                flow through with no script change. Attached to
                                request-side entries only; response entries never
                                get design. Known rules are VALIDATED (§6): design
                                present on every input, position ∈ primary|secondary
                                and consistent with required, no delimiter with
                                isArray, no enableUserOverride with FolderPicker.

httpMethod → THE verb slot key  // an SR always has exactly ONE verb —
                                //   one activity = one operation = one slot
method.<VERB>.name = <VERB>
operation default             → GET→List, GET_BY_ID→Retrieve, POST→Create,
                                PUT→Replace, PATCH→Update, DELETE→Delete
                                (activity.operation overrides — e.g. Slack POST→Update)

enum                          → on a body field: emitted as field `enum` verbatim;
                                on a path|query input: auto-mapped to the parameter's
                                `enhancedEnum` (params never use the deprecated `enum` key)

responseSchema                → operation List → { "type": "array", "items": { "type": "object" } }
                                else → { "type": "object" }

metadata.primaryKey           → all expanded fields with primaryKey: true (names, incl. "[*]")

top level                     → name, displayName (fallback humanize), description,
                                type: "standard", elementKey, path: vendorPath,
                                executionType: "sync"

never emitted                 → objectName, reference.path/childPath/hydration,
                                order, dependsOn, curation, searchables, experimental,
                                design keys beyond those with derivation rules
```

`humanize(name)`: strip `[*]`, take the last `.` segment, space out underscores
and camelCase, capitalize — `usergroup.id` → "Id", `team_id` → "Team id" (so
supply `displayName` when the fallback is poor; it is a convenience, not a goal).

## 6. Validation (script-enforced, after expansion)

1. `isArray` entries must not carry `design.delimiter` (a true array is never
   joined).
2. Required keys: top level (`name`, `displayName`, `metadata`); verb slot
   (`operation`, `method`, `path`, `scriptRef`); every parameter
   (`name`, `description`, `type` ∈ path|query, `dataType`, `displayName`);
   every field (`name`, `type`, `displayName`, `method`).
3. Every `reference`: `scriptRef` present and a **bare base name** (no `/`, no
   `.`), `lookupValue` + non-empty `lookupNames`.
4. `primaryKey` only on fields with response participation.
5. No `[*]` field carries a `delimiter`.
6. `operation: List` ⇒ exactly one output, and it is an array.
7. Closed sets: operation enum, `executionType`, `position`.
8. `metadata.method` has exactly ONE verb slot — an SR is always single-verb
   (one activity = one operation).
9. Design (authored, pass-through): every INPUT carries a `design` block;
   `position` consistent with `required` (required → primary, optional →
   secondary); `component: "FolderPicker"` never combined with
   `enableUserOverride`; response-only fields carry NO design. Unknown design
   keys are allowed (future elements pass through unvalidated).

The script refuses to write the SR on any violation — the contract rules become
executable instead of advisory.

## 7. Worked example

### Input — `activity.min.json`

```jsonc
{
  "activity": {
    "name": "add_users_to_usergroup",
    "displayName": "Add Users to User Group",
    "description": "Add one or more users to a Slack user group, keeping the existing members.",
    "elementKey": "uipath-salesforce-slack",
    "vendorPath": "/usergroups.users.update",
    "httpMethod": "POST",
    "operation": "Update",
    "scriptRef": "add_users_to_usergroup"
  },
  "inputs": [
    { "name": "usergroup", "type": "string", "in": "body", "required": true,
      "description": "The user group to add users to.",
      "displayName": "User group",
      "lookup": { "scriptRef": "list_usergroups", "value": "id", "display": ["id", "name"] },
      "design": { "position": "primary", "isMultiSelect": false, "enableUserOverride": true, "displayPattern": "{name}" } },
    { "name": "users", "type": "string", "in": "body", "required": true,
      "description": "Comma-separated encoded user IDs to add. Existing members are kept.",
      "displayName": "Users to add",
      "lookup": { "scriptRef": "list_users", "value": "id", "display": ["id", "real_name"] },
      "design": { "position": "primary", "isMultiSelect": true, "delimiter": ",", "enableUserOverride": true, "displayPattern": "{real_name}" } },
    { "name": "include_count", "type": "boolean", "in": "body",
      "description": "Include the member count in the response.",
      "displayName": "Include member count",
      "design": { "position": "secondary" } },
    { "name": "team_id", "type": "string", "in": "body",
      "description": "Encoded team ID. Required only for org-wide apps.",
      "displayName": "Team ID",
      "design": { "position": "secondary" } }
  ],
  "outputs": [
    { "name": "usergroup.id", "type": "string", "primaryKey": true,
      "displayName": "User group ID",
      "description": "The ID of the updated user group." }
  ]
}
```

### Output — generated SR (must equal the contract §8 worked example)

Key expansions to check while reviewing:

- `users`: plain name (delimited string, not an array) → `fields.users`,
  `type: "string"`, its authored `design` block copied VERBATIM, reference
  `{ scriptRef: "list_users", lookupValue: "id", lookupNames: ["id","real_name"] }`.
- `include_count` / `team_id`: `design: { position: "secondary" }` only.
- `usergroup.id`: `response: true`, `primaryKey: true`, no design;
  `metadata.primaryKey = ["usergroup.id"]`.
- `metadata.method.POST`: `operation: "Update"` (override), `scriptRef:
  "add_users_to_usergroup"`, no `parameters` (no URL inputs), `responseSchema:
  { "type": "object" }`.

A LIST variant (`list_users` as its own activity) would have
`operation: "List"`, `outputs: [ { "name": "users", "type": "object",
"isArray": true, ... } ]` → single SR output `users[*]`, and `responseSchema:
{ "type": "array", "items": { "type": "object" } }`.

## 8. The generator — shape

Implemented as **`uip is activities metadata build`**:

```bash
uip is activities metadata build activity/<name>.min.json [--out <file>]
```

The default output path replaces `.min.json` with `.json`. It **validates before
it writes**, so a rejected build leaves no artifact behind. Internally:

```
VERB_OP map, humanize(), fname()            // tiny pure helpers
referenceFor(lookup)                        // → { scriptRef, lookupValue, lookupNames }
                                            // design: NO derivation — authored block
                                            //   passed through verbatim (validated in §6.9)
fieldEntry(verb, entry, dir)                // → one fields{} entry (request|response)
generate(min)                               // split inputs, expand, collect primaryKey,
                                            //   assemble top level + metadata.method
validate(min, sr)                           // §6 — throws with ALL violations listed
```

Verified: generating from the §7 min-file reproduces the contract's §8 worked
example; the List variant produces the single `users[*]` output +
array `responseSchema`; the §6 violations (isArray+delimiter, request-only
primaryKey, non-bare scriptRef, List with extra outputs) are all rejected with
per-violation messages.

## 9. Where this fits in the workflow

`activity-generation.md` reaches this file at **step 5**:

1. Read the contract (`standard-resource-contract.md`) — authoritative for review
   and debugging.
2. Fill `activity/<name>.min.json` from the vendor schema, the response captured
   in step 4, and the lookup script base names from step 3. **All judgment lives
   here.**
3. Step 6 runs `uip is activities metadata build` → the activity metadata file,
   then `uip is activities metadata types` → the script's type header.
4. The command's validation replaces any manual rule-check: it refuses to write
   on a violation, so a rejected build leaves no artifact behind.

**Unchanged by this design:** the contract document, one metadata file per main
activity, and lookup scripts getting none of their own.

## 10. Resolved decisions

1. **File locations (DECIDED):** the SR lands at `activity/<name>.json` next to
   the action files (matching the `uipath-salesforce-slack/activity/` scaffold
   layout), with the min-file beside it as `activity/<name>.min.json` — kept as
   the reviewable source of truth; the SR is regenerated, never hand-edited.
2. **`display` ordering (ADOPTED):** last element = most readable, drives
   `displayPattern`. The convention the generator implements.
3. **Single verb (DECIDED):** an SR always has exactly one verb slot (§5, §6.8).
4. **`enum` routing (DECIDED):** one `enum` key in the min-file; body field →
   `enum`, path/query param → `enhancedEnum` (§5).
5. **Design is AUTHORED, not derived (DECIDED):** the min-file carries the full
   `design` block per input and the script passes it through verbatim —
   future design elements are added in the min-file with no script change. The
   script validates the known rules (§6.9) and lets unknown keys through. This
   replaced the earlier derive-design-from-facts approach (which also removed
   the top-level `delimiter` and `lookup.hierarchical` min-file keys — both now
   expressed directly inside `design`).

## 11. Out of scope

Everything the contract defers: design keys beyond the six enabled, triggers/
events, curation, searchables, `compatibleProjectTypes`, `nativeType`/`mask`/
`sampleValue`. Multi-verb SRs do not exist — an SR is always single-verb (one
activity = one operation), by definition, not by deferral.
