# Registry resolution (Phase 1)

Turn the resource names an approved `sdd.md` declares into tenant identities,
recorded in `tasks/registry-resolved.json`. Run it before authoring any
resource-bound task, and on its own when the request asks for Phase 1,
registry refresh, or a fresh `tasks/registry-resolved.json`.

That file is a contract, not notes. `uip maestro case validate --strict --sdd`
reads it to tell a justified placeholder from a skipped lookup, and a later
build (on this machine or another) reads it instead of re-resolving.

## Steps

1. `uip login status --output json`, then `uip maestro case registry pull --output json`.
   Always pull first. Before a pull, a missing `~/.uip/case-resources/<type>-index.json`
   means "not fetched yet", never "the tenant has none".
2. `uip maestro case sdd resolve sdd.md --out tasks/registry-resolved.json --output json`.
   It reads each task's `Resolved Resource` name, searches the right index, narrows
   by the SDD's folder, and writes one entry per task. It replaces a stale ledger
   whole. Never hand-author or re-wrap this file; keep its
   `{resolved, unresolved, scope}` shape.
3. If `Data.Scope.cache.stale` is `true`, run `uip maestro case registry pull --force --output json`
   once and resolve again.
4. `Data.Unresolved[]` is the only work left. Ask about all of it in ONE
   `AskUserQuestion`, one group per `(name, taskType)`:

   | `reason` | Options |
   |---|---|
   | `ambiguous` (several exact-name matches) | one option per entry of `candidates[]`, labelled by its `folder`, plus `Use a placeholder` |
   | `absent` (no match) | `Force pull and re-resolve`, `Use placeholders for all` |

   After `Force pull and re-resolve`, run step 2 again and ask only about what is
   still unresolved.

   Never settle `ambiguous` by position: the cache lists resources in the order
   they were registered, which says nothing about which one the SDD means.
5. Write each answer into that task's entry under `resolved` with Edit:
   - Pick: set `selected` to the chosen candidate exactly as resolve normalized it
     (`{name, identifierField, identifier, folder}`), add `"gateDecision": "pick:<name>"`,
     update `rationale`, and drop the row from `unresolved`.
   - Placeholder, or no answer: keep `matches` and `selected: null`, and add
     `"taskTypeId": "<UNRESOLVED: <reason>>"` so the miss is explicit for whichever
     build reads the ledger. Add `"gateDecision": "resolve-at-build"` only when the
     user chose it.
6. Stop here when the request is Phase 1 only. Otherwise bind each `selected`
   name and folder in the task's builder call; a miss stays an explicit
   placeholder (`.unresolved('<kind>')` where the kind supports it).

Example: the SDD names `API Workflow` and six tenant folders hold one. Resolve
reports `reason: "ambiguous"` with six candidates. The user picks
`Shared/uipath-maestro-case/NameToAgeFixed`, so that entry becomes
`"selected": {"name": "API Workflow", "identifierField": "entityKey", "identifier": "df4b78d9-6cb7-4511-95ec-37ff80c98319", "folder": "Shared/uipath-maestro-case/NameToAgeFixed"}`
with `"gateDecision": "pick:API Workflow"`.

If the CLI reports `sdd resolve` as an unknown command (`ErrorCode: "invalid_argument"`),
say so in one line, then write the same entry shape by hand from the pulled
index files: `stage`, `task`, `taskType`, `cacheFile`, `searchQuery`,
`matches` (every exact-name entry), `selected`, `rationale`.
