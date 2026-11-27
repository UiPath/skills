# Registry resolution (Phase 1)

Turn the resource names an approved `sdd.md` declares into tenant identities,
recorded in `tasks/registry-resolved.json`. Run it before authoring any
resource-bound task, and on its own when the request asks for Phase 1,
registry refresh, or a fresh `tasks/registry-resolved.json`.

`uip maestro case sdd resolve` needs a CLI that ships it (cli#4238; released
builds up to 1.203.0 do not). If the CLI reports it as an unknown command
(`ErrorCode: "invalid_argument"`), say so in one line, then write the same
entry shape by hand from the pulled index files: `stage`, `task`, `taskType`,
`cacheFile`, `searchQuery`, `matches` (every exact-name entry), `selected`,
`rationale`. Steps 4 to 6 apply unchanged.

### Index files by task type

| Task type | Index file | Identity field | Creatable |
|---|---|---|---|
| `agent` | `agent-index.json` | `entityKey` | yes |
| `api-workflow` | `api-index.json` | `entityKey` | yes |
| `business-rule` | `businessRule-index.json` ¹ | `entityKey` | yes ¹ |
| `process` | `processOrchestration-index.json` | `entityKey` | no |
| `rpa` | `process-index.json` | `entityKey` | no |
| `action` | `action-apps-index.json` | `id` | no |
| `case-management` | `caseManagement-index.json` | `entityKey` | no |
| `function` | `function-index.json` ¹ | `entityKey` | no |
| `flow-process` | `flow-index.json` | `entityKey` | no |
| `wait-for-connector` | `typecache-triggers-index.json` | `uiPathActivityTypeId` | no |
| `execute-connector-activity` | `typecache-activities-index.json` | `uiPathActivityTypeId` | no |
| `external-agent` | `typecache-external-agent-activities-index.json` | `uiPathActivityTypeId` | no |
| `external-workflow` | `typecache-external-automation-activities-index.json` | `uiPathActivityTypeId` | no |
| `wait-for-timer` | *(no index — built-in)* | — | — |

All indexes live under `~/.uip/case-resources/`. Read with the Read tool,
never `node -e ... fs.*`.

¹ CLIs without `sdd resolve` never pull these indexes, so a task of
either type stays unresolved as a placeholder — never record it as
`absent` and never offer to create it.

## Steps

<!--skill-flavor:registry-login:start-->
1. `uip login status --output json`, then `uip maestro case registry pull --output json`.
<!--skill-flavor:registry-login:end-->
   Always pull first. Before a pull, a missing `~/.uip/case-resources/<type>-index.json`
   means "not fetched yet", never "the tenant has none".
2. `uip maestro case sdd resolve sdd.md --out tasks/registry-resolved.json --output json`.
   It reads each task's `Resolved Resource` name, searches the right index, narrows
   by the SDD's folder, and writes one entry per task. It replaces a stale ledger
   whole. Never hand-author or re-wrap this file; keep its
   `{resolved, unresolved, scope}` shape, which is the shape
   `uip maestro case validate --strict --sdd` reads.
3. If `Data.Scope.cache.stale` is `true`, run `uip maestro case registry pull --force --output json`
   once and run step 2 again.
4. If the pull reported failures (`PartialSuccess, N failed`) or `Data.Scope.missingIndexes`
   is non-empty, stop and report which indexes are missing. A failed pull is not an
   empty lookup: resolve leaves tasks on a missing index out of `Data.Unresolved[]`,
   so nothing below would ask about them.
5. Otherwise `Data.Unresolved[]` is the only work left. Ask about it with
   `AskUserQuestion`, one question per `(name, taskType)` group, at most four
   questions per call; past four groups, ask the rest in a next call.
   A question takes 2 to 4 options:

   | `reason` | Options |
   |---|---|
   | `ambiguous`, up to 3 `candidates[]` | one option per candidate, labelled by its `folder`, plus `Use a placeholder` |
   | `ambiguous`, 4 or more `candidates[]` | `Use a placeholder`, `Force pull and re-resolve`; list every candidate `folder` in the question text so the user can answer with a folder through Other |
   | `absent` (no match) | `Force pull and re-resolve`, `Use placeholders for all` |

   After `Force pull and re-resolve`, run step 2 again and ask only about what is
   still unresolved.

   Never settle `ambiguous` by position: the cache lists resources in the order
   they were registered, which says nothing about which one the SDD means.
6. Write each answer into that task's entry under `resolved` with Edit:
   - Pick: set `selected` to the chosen candidate exactly as resolve normalized it
     (`{name, identifierField, identifier, folder}`), add `"gateDecision": "pick:<name>"`,
     update `rationale`, and drop the row from `unresolved`.
   - Placeholder, or no answer: keep `matches` and `selected: null`, and add the
     task type's identity slot holding `"<UNRESOLVED: <reason>>"`: `taskTypeId`
     for non-connector tasks, `typeId` for connector tasks (`wait-for-connector`,
     `execute-connector-activity`). The marker is what tells `validate --strict --sdd`
     and the build that the miss is deliberate. Add `"gateDecision": "resolve-at-build"`
     only when the user chose it.
   - A placeholder on an `ambiguous` row keeps its `matches`, so
     `validate --strict --sdd` reports it as an error by design (only zero-match
     entries are softened). Report that error as expected; do not loop trying to
     clear it.
7. Stop here when the request is Phase 1 only. Otherwise bind each `selected`
   name and folder in the task's builder call; a miss stays an explicit
   placeholder (`.unresolved('<kind>')` where the kind supports it).

Example: the SDD names `InvoiceCheck` and three tenant folders hold one. Resolve
reports `reason: "ambiguous"` with three candidates, so the question offers the
three folders plus `Use a placeholder`. The user picks `Finance/Prod`, so that
entry becomes
`"selected": {"name": "InvoiceCheck", "identifierField": "entityKey", "identifier": "<entityKey>", "folder": "Finance/Prod"}`
with `"gateDecision": "pick:InvoiceCheck"`.

## Connector operations

`sdd resolve` leaves every task whose SDD block states an `Activity Type ID`
unresolved ("names no resource"): that id, not a name, identifies the
connector operation. Resolve each such task before authoring it:

1. `uip maestro registry search --activity-type-id <ACTIVITY_TYPE_ID> --output json`.
   None of these answers is a miss; fix the cause and search again:

   | Answer | Do |
   |---|---|
   | "needs a pulled connector library" | `uip maestro registry pull --output json` |
   | `ConfigError` naming `search-activity-type-id` | Builder SDK predates the flag: upgrade it as the message says. Never retry without the flag. |
   | Command fails naming a definition it could not read, or `Data.UnreadDefinitions` above `0` ("The search is incomplete") | `uip maestro registry pull --force --output json`. Still failing or incomplete: stop and report it. Never author a placeholder from an incomplete search. |

2. `Data.Total` is `1`: bind that operation's `NodeType`.
3. `Data.Total` above `1`: the rows share the id. Pick by what differs.
   - `NodeType` differs (`…connector.event.…`, `…connector.trigger.…`): forms
     of one operation. Take the form the task type needs.
   - `NodeType` is the same and `ObjectName` differs: a generic operation, one
     row per object. Take the row whose `ObjectName` is the `objectName` the
     SDD's `Operation` line states; adding it as a query word returns that row
     alone: `uip maestro registry search <OBJECT_NAME> --activity-type-id <ACTIVITY_TYPE_ID> --output json`.
     Pass that name as the connector call's `object` option, and as `--object`
     to `registry describe` and `registry prepare`. `NodeType` alone fails
     `check` with `CONNECTOR_OBJECT_REQUIRED`.
   - Fewer rows returned than `Data.Total`: repeat with `--limit <TOTAL>`
     before picking.
4. `Data.Total` is `0` with no `Data.UnreadDefinitions`: run
   `uip maestro registry pull --force --output json` once, then search again.
   Still `0`: author the task as `.unresolved('connector')` or
   `.unresolved('wait-for-connector')` and record the miss as in step 6 of
   [Steps](#steps). Never bind another operation in its place, even one on the
   same connector with the same object name.
5. Never list a connector to pick an operation by name
   (`registry search --connector <CONNECTOR_KEY>` with no id): a long list is
   cut off, and two operations can share an object name.
