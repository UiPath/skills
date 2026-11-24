# Entities from a Schema — create an approved entity set in one run

Creates choice sets, native entities and federated entities over natives from one approved `entities.json`, in dependency order, through `scripts/entities-compile.mjs`. The script is deterministic: agent decides what the entities are; script only turns the approved file into `uip df` creates and checks what the platform stored.

Use when:

- an entity set (several entities, choice sets, relationships, federated views) must be created from one approved definition — e.g. the build of a genome whose Data Fabric entities come from a data model;
- the same set must be recreated in another folder or solution.

Single entity, single field change → [`entity-schema.md`](entity-schema.md). Federated entity over a connector → [`federated-entity-creation.md`](federated-entity-creation.md).

## Critical Rules

1. **The file is approved before `apply`.** Show the user `plan.json`'s `order` and `trace`; run `apply` only after approval.
2. **Folder level is the default target.** Resolve the folder per [`data-fabric.md`](data-fabric.md) folder-scope rules, pass its key as `--folder-key`. Use `--local` only when the user asks for the entities to ship with a solution ([`local-entities.md`](local-entities.md)).
3. **Never edit `plan.json` or `state.json` by hand.** Change `entities.json`, run `plan` again.
4. **On exit 2 fix `entities.json`; never work around a refusal** (rename silently, drop a field, default a length).
5. **On exit 1 report `result.json` `failed` as it is.** Do not retry a step whose `platform.Retry` is `RetryWillNotFix`. Rerun `apply` with the same `--state` only after the cause is fixed: it skips what exists.
6. **A `kind: "review"` entity is a proposal.** Settle it to `native` or `federated` with the user; `plan` refuses it.

## Workflow

```bash
node "<SKILL_DIR>/scripts/entities-compile.mjs" plan --schema "<ENTITIES_JSON>" --out "<PLAN_JSON>"
node "<SKILL_DIR>/scripts/entities-compile.mjs" apply --plan "<PLAN_JSON>" --state "<STATE_JSON>" --out "<RESULT_JSON>" --folder-key "<FOLDER_KEY>"
```

Solution instead of folder (run `plan` with `--local` too):

```bash
node "<SKILL_DIR>/scripts/entities-compile.mjs" plan --schema "<ENTITIES_JSON>" --out "<PLAN_JSON>" --local
node "<SKILL_DIR>/scripts/entities-compile.mjs" apply --plan "<PLAN_JSON>" --state "<STATE_JSON>" --out "<RESULT_JSON>" --local --solution "<SOLUTION_DIR>"
```

`apply` accepts `--profile <PROFILE>` for a non-default `uip` login. Keep `<STATE_JSON>` per target: a state file of another folder or solution is refused.

| Exit | Meaning | Next |
|---|---|---|
| 0 | Done; every read-back matches | Report `result.json` |
| 1 | Platform failed (`failed.platform`), or stored something other than sent (`readBack.*.differences`), or local `validate` failed | Report; fix cause; rerun with same `--state` |
| 2 | Refused (`refused` in `plan.json`, or `failed.refused` in `result.json`) | Fix `entities.json`; `plan` again |

## `entities.json`

Format: [`entities.schema.json`](entities.schema.json). Unknown keys are refused.

```json
{
  "version": 1,
  "choiceSets": {
    "EventType": { "displayName": "Event type", "values": [{ "name": "Meeting", "displayName": "Meeting" }] }
  },
  "entities": {
    "clubEvent": {
      "kind": "native",
      "realizes": [{ "class": "Event", "role": "owner" }],
      "fields": {
        "eventName": { "type": "STRING", "length": 80, "required": true, "property": "Event.name" },
        "type": { "type": "CHOICE_SET_SINGLE", "choiceSet": "EventType", "required": true, "property": "Event.type" },
        "budget": { "type": "DECIMAL", "precision": 2, "property": "Event.budget" }
      }
    },
    "clubEventDetail": { "kind": "native", "realizes": [{ "class": "Event", "role": "part", "key": "eventName" }],
      "fields": { "eventName": { "type": "STRING", "length": 80, "required": true, "unique": true }, "room": { "type": "STRING", "length": 20 } } },
    "clubEventView": {
      "kind": "federated",
      "realizes": [{ "class": "Event", "role": "view" }],
      "primary": { "entity": "clubEvent", "fields": { "eventName": "eventName" } },
      "sources": [{ "entity": "clubEventDetail", "join": "eventName", "fields": { "eventName": "detailEventName", "room": "room" } }]
    }
  }
}
```

| Key | Holds |
|---|---|
| `kind` | `native`, `federated`, or `review` (proposal, refused by `plan`) |
| `realizes` | Classes of the data model the entity carries; `role`: `owner`, `part` (more fields of a class on the same key), `copy`, `junction` (many-to-many link), `view` |
| field `type` | `STRING` (needs `length`), `DECIMAL` (needs `precision`; 0 for integers), `BOOLEAN`, `DATE`, `DATETIME_WITH_TZ`, `CHOICE_SET_SINGLE` (needs `choiceSet`), `RELATIONSHIP` (needs `target`, a native of the file, and `display`) |
| field `display` | `RELATIONSHIP` only: the target's field shown for a related record (`Id` or a field of the target). Sent as `referenceFieldId`. A user-visible choice: ask, never default |
| field `required`, `unique` | `true` / `false`; absent = `false` |
| field `property` | Data-model property the field carries; feeds `trace` |
| federated `primary`, `sources[]` | Natives of the file; `fields` maps source field → name in the view; each source `join`s on a field it shares with the primary, selected on both |

## Gates (`plan` exit 2)

| Refused | Why |
|---|---|
| Entity name with anything but letters and digits, or under 3 characters (`customer_order`) | Platform rejects: "Entity name must start with a letter, use only letters and numbers, and be 3-100 characters" |
| Entity or field name a reserved SQL word, any case (`order`, `key`, `user`, `percent`) | Platform rejects: "a reserved SQL word and cannot be used as an entity or field name"; checked against the Transact-SQL reserved keywords |
| Field name a C# or VB keyword, any case (`event`, `virtual`, `date`) | Platform rejects: `RESERVED_LANGUAGE_KEYWORDS` |
| Field name of a system field (`Id`, `CreateTime`, …) | Every entity has it |
| Choice-set name with anything but letters and digits | Platform rejects |
| Choice value name not starting with a letter, or with symbols | Platform rejects; keep the code as `displayName` |
| `STRING` without `length`, `DECIMAL` without `precision` | No default is invented |
| `RELATIONSHIP` to a federated entity or to an entity not in the file | Relationship needs a native target created first |
| `RELATIONSHIP` without `display`, or a `display` the target does not have | The display field is the user's choice, never defaulted |
| Relationships forming a cycle | Each target must exist before the field pointing at it |
| `junction` role with fewer than two relationships | A junction links two sides |
| Federated source not a native of the file | Only federation over natives is compiled |
| Same name selected from two federated sources | Tenant refuses the create (`Failed to open all connection(s)`); rename one |
| Join field not selected on primary and source | Server joins only on selected fields |

## Responses

`plan.json`: `schemaHash`, `target` (`folder` / `local`), `order` (choice sets, natives with each relationship target first, federated last), `steps[]` (one `uip df` create each; body ids as `{{entity X.id}}`, `{{entity X.field <DISPLAY>}}` (the target's display field id), `{{choiceSet X.id}}`, `{{folderKey}}`), `trace[]` (property → entity field, role), `refused[]`.

`result.json`: `created` (ids per step; also kept in `--state`), `readBack` (per entity: field count, `differences[]`), `failed` (`step` + `platform` response as returned, or `refused`), `validate` (local only).

Read-back compares type (folder only — local read-back gives SQL types), length, precision, required, unique, relationship target and display field, choice set. `--local` bodies name the relationship target only and carry no display field. Federated read-back checks every selected name exists.

## Known Platform Failure

A federated create can fail with `Failed to open all connection(s)` even with a valid body: the platform validates native sources in parallel inside one transaction. `result.json` records it; do not retry in a loop. Report it with the step and the `platform` response.

## Anti-patterns

- Calling `uip df entities create` by hand for some entities of the set and the script for others — `state.json` then misses ids and later relationships cannot resolve.
- Reusing one `--state` file across folders.
- Fixing a refusal by editing `plan.json`.
