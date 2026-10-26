# UiPath Data Fabric (`uip df`)

Data Fabric is UiPath's typed data store: entities are schemas, records are rows, and file fields store binary attachments. Run operations as `uip df <subject> <verb> --output json`.

This file routes CLI operations and defines cross-cutting safety rules. Read Critical Rules, then load only the needed topic reference. For Data Fabric nodes inside a `.flow`, use `uipath-maestro-flow`; use this reference for CLI operations.

**One flag picks the target.** `uip df entities …` operates on live tenant entities. The same verbs with `--local` author an entity in a solution on disk; it becomes real only at deploy, requires no login or tenant, and `get` / `update` / `delete` take the entity **name** instead of an id. This file describes the tenant path unless stated otherwise; see [`local-entities.md`](local-entities.md) for the local path.

**Tenant is the default; `--local` only on an explicit ask.** Use `--local` only when the user explicitly asks for the entity to live in or ship with a solution. An open `.uipx` or a flow needing data is not sufficient; ask which path they want when ambiguous.

## Not Supported

Do not change field types, write federated records, or work around rejected names. FILE values require `files upload`; record writes silently ignore them. (**Creating** a federated entity from a connector or another entity **is** supported → [`federated-entity-creation.md`](federated-entity-creation.md); only record *writes* are not.) Use the rules and topic references for supported alternatives.

**Immediate refusal.** If a request is categorically unsupported (federated *write*, type-change, reserved-keyword name, cross-scope binding, etc.) and the prompt establishes that fact, refuse immediately, cite the rule, and offer the supported alternative. Do **not** re-verify with `entities list`, `entities get`, or other discovery. Creating an entity from a connector is not a refusal case → [`federated-entity-creation.md`](federated-entity-creation.md).

## Critical Rules

> ### ⛔ Destructive Operations — STOP and Confirm
>
> **Never invoke any of the following without explicit user approval in the current turn.** Approval = the user typed *yes / approved / proceed / delete / confirm* in response to a previewed plan. Implied consent, prior-turn approval, or "the user asked me to clean up" is NOT approval.
>
> | Operation | CLI shape | Detail |
> |---|---|---|
> | Delete entity | `entities delete <id> --yes --reason "<why>"` | Rule 10 — list dependents first, never cascade silently |
> | Delete field | `entities update <id> --body '{"removeFields":[...]}' --yes --reason "<why>"` | Rule 11 — for `CHOICE_SET_*` / `RELATIONSHIP`, ask whether to also delete the reference target |
> | Delete record(s) | `records delete <entity-id> <id1> <id2> --yes --reason "<why>"` | Per-record `--yes --reason` required |
> | Delete file attachment | `files delete <entity-id> <record-id> <field-name> --yes --reason "<why>"` | Irreversible |
> | Delete choice set | `choice-sets delete <id> --yes --reason "<why>"` | Shared resource — verify no entity binds it first |
> | Delete choice-set value | `choice-set-values delete <id> --yes --reason "<why>"` | Shifts NumberIds of later values — see [`choice-sets.md`](choice-sets.md) |
> | Create / schema-alter | `entities create`, `entities update` with `addFields`/`updateFields`/`removeFields`, `choice-sets create`, `choice-set-values create` | Rule 14 — preview schema, wait for explicit approval |
>
> **Mandatory sequence for every row above:**
> 1. **Resolve folder scope first** (Rule 19). Never guess or default to personal workspace.
> 2. Surface the exact target (entity name + ID, field name, record IDs) and what will be lost.
> 3. For deletes — list dependents (Rule 10/11).
> 4. Wait for explicit *yes / proceed / delete*. Silence and *"Do not ask"* / *"no confirmation needed"* do not approve (Rule 0).
> 5. Then run the CLI with `--folder-key <key>` if folder-scoped and `--yes --reason "<user-supplied reason>"`.
>
> **Cascade only on confirmation.** For `CHOICE_SET_*` / `RELATIONSHIP` field deletes, Rule 11 mandates a dropdown offering `Delete only the field` / `Also delete the referenced choice set / target entity` / `Stop`. Each downstream delete runs its own confirmation cycle.

0. **Ask liberally — never assume at decision points.** When scope, folder, entity, field, cascade choice, or a name-match choice is unresolved, stop and raise an `AskUserQuestion` dropdown. Bias: *ask, then act*, not *act, then explain*. Render every multi-option pick as a dropdown, not a markdown list.

    **Destructive ops are non-bypassable.** For any row in the Destructive Operations block you MUST raise the AskUserQuestion confirmation **even if the user said "do not ask" / "no confirmation needed" / "proceed without confirmation"**. Rule 19 bypass clauses apply only to *scope resolution*. Silence or "do not ask" alone does not clear the gate.

    **Pre-approval that satisfies the gate.** Do not re-ask when the user explicitly confirms a specific operation and resource, for example *"I approve creating CE_X and adding fields A, B, C"*, *"yes, delete X"*, or equivalent `--yes` authorization. A general request or *"do not ask"* is not confirmation. Preview → apply per Rule 14 still holds.

    **Never self-resolve a scope question.** Phrases like *"Assumption I will proceed with:"*, *"defaulting to tenant"*, or *"I'll assume …"* violate this rule. Halt the mutation, list the open question, and STOP. *"No reachable user"* / *"single-turn"* / *"offline test"* is NOT permission to default.

1. **Install the tool first.** If `uip df` returns "unknown command": `uip tools install @uipath/data-fabric-tool@latest`.

2. **Verify login and tenant first.** Run `uip login status --output json`. Switch with `uip login tenant set <tenant>` if needed. Full login setup is in the parent `uipath-platform` skill.

3. **Always resolve entity ID first.** Use `entities list` before any operation. Never assume an entity ID.

4. **Schema name rules.** Entity and choice-set names allow letters, digits, and underscores; field names allow letters and digits only. All are 3–100 characters and start with a letter. Reserved system field names are case-insensitive: `Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`, `RecordOwner`. C#/VB keywords are rejected case-insensitively; the CLI also rejects live-confirmed SQL-reserved words such as `Order` and `Group`, while ordinary names such as `Status` and `Key` are accepted. **Choice-set value `Name` uses a different validator** — see [`choice-sets.md` → Value Name validation](choice-sets.md#value-name-validation). Full rules: [`entity-schema.md` → Name Validation](entity-schema.md#name-validation).

5. **`records update` requires `"Id"` in every element** (single or batch). Body shape is validated before the row is resolved, so a body missing `"Id"` fails with `Record must include 'Id'` even offline. See [`records-query.md` → Update Records](records-query.md#update-records).

5b. **`isUnique` is immutable after field creation.** `updateFields` returns `Result: Success` but silently no-ops the value. To change it: `removeFields` → `addFields` with `isUnique: true` (**drops every existing value in the column**). Verify every `updateFields` call by re-reading `entities get` and comparing. Full surface: [`entity-schema.md` → Not Supported](entity-schema.md#not-supported) + [Verify-after-update](entity-schema.md#verify-after-update--never-trust-the-success-response-alone).

6. **Never put a FILE-typed key in `records insert` / `records update` / `records import` payloads.** Paths, base64, UUIDs, and `null` are silently stripped; the CLI returns `Result: Success`. Insert the row without the FILE column, then run `files upload <entity-id> <record-id> <field-name> --file <path>` (also for replace); run `files delete` to clear and `files download` to retrieve. Full surface: [`file-attachments.md`](file-attachments.md).

7. **CSV headers must match `Fields[].DisplayName`** (case-sensitive), not internal `Name`. Discover via `entities get`. See [`bulk-import.md`](bulk-import.md).

8. **Never create duplicate entities.** Always run `entities list` first and reuse an existing entity. Entity and choice-set `displayName` values must also be unique. If absent, derive a collision-resistant display name from the requested `Name`, not a generic label. On `409` / `RetryWillNotFix`, do not repeat the same create or treat an environment ID from the error as a resource ID; surface the conflict and ask for a different name or display name.

9. **Record writes are native-only.** Use `entities list --native-only` before any record write. Federated entities are read-only for records because data lives in the source, but **creating** and reading them (`records list` / `records query`) is supported → [`federated-entity-creation.md`](federated-entity-creation.md).

10. **Entity delete — dependent discovery.** Gating is in the Destructive Operations block. Scan inbound references (`entities list --output json` → `Fields[].ReferenceEntity.Id == <id>`) and choice sets used by fields (`Fields[].ChoiceSetId`). Ask per dependent: delete, leave, or stop. Full sequence: [`entity-schema.md` → Deleting an Entity](entity-schema.md#deleting-an-entity).

11. **Field delete — `removeFields` uses `{"name":"…"}`** (NOT `id` like `updateFields`). For `CHOICE_SET_*` / `RELATIONSHIP` fields, raise a cascade-ask dropdown before invoking (`Delete only the field` / `Also delete the referenced choice set / target entity` / `Stop`) and echo other bindings so the user sees blast radius. `FILE` field delete drops only the column—never offer to delete the platform-managed storage entity. Full sequence: [`entity-schema.md` → Deleting a Field](entity-schema.md#deleting-a-field).

12. **Complex fields need extra config and lookups.** `CHOICE_SET_*` needs `choiceSetId`; `RELATIONSHIP` needs `referenceEntityId` + `referenceFieldId`; `FILE` needs neither because the server auto-wires it. The type for a link such as "each order has a Customer" is `RELATIONSHIP`, never `STRING` or `UUID`. The target entity must exist first. Full shape: [`entity-schema.md` → Supported Field Types](entity-schema.md#supported-field-types).

12b. **UI-broken types — never emit as a field type.** `INTEGER`, `BIG_INTEGER`, `FLOAT`, `DOUBLE`, `UUID`, `DATETIME` are accepted by the API but render broken in the Data Fabric UI. Substitute per [`entity-schema.md` → UI-broken types](entity-schema.md#ui-broken-types--do-not-use). Rule 14 preview must not name any of the six anywhere in the proposal.

13. **Pick-or-create flow — applies to entities, choice sets, and relationship targets.** When the user names a target without disambiguating, or names none, do NOT auto-create or silently take the first match. Run the appropriate list command, present matches via dropdown, and ask *pick from these or create new?*. Create only with explicit approval.
    - **Primary entity:** run `entities list --native-only` (+ `--folder-key` or `--include-folders` per scope) → dropdown → user picks or confirms create-new.
    - **Choice set** (CHOICE_SET_* field, choice-set-value writes): run `choice-sets list` → dropdown.
    - **Relationship target:** run `entities list --native-only` → dropdown. Never fall back to `STRING`/`UUID`. `FILE` does not use this flow; the server auto-wires its storage entity (Rules 6/12).

    **Bounded discovery.** For each unresolved choice, make one focused discovery pass before asking or skipping; do not repeatedly re-list unchanged resources or search the filesystem for documentation. Never inspect installed CLI package source or create temporary probe entities to infer schema or syntax; use this reference and `--help`. Pagination needed to complete that pass and post-mutation reads used to verify changed state are allowed. For an **optional** resource where the request says to use one if available and otherwise skip, inspect once; if no clear match exists, skip it without creating probes. Do not run extra mutation experiments beyond requested scenarios.

14. **Schema preview — compose, render, wait.** Before every `entities create` / `entities update` with `addFields`/`updateFields`/`removeFields` / `choice-sets create` / `choice-set-values create`: (1) compose the full proposal — entity name, `displayName`, `description`, every field with UPPERCASE `type` and all extras (`isRequired`, `isUnique`, `lengthLimit`, `maxValue`/`minValue`, `decimalPrecision`, `defaultValue`, `choiceSetId`, `referenceEntityId`/`referenceFieldId`); (2) render it as a table or formatted JSON block, NOT a raw CLI command; (3) apply revisions exactly—never silently add, drop, rename, or retype what the user did not approve.

    **`referenceFieldId` on `RELATIONSHIP` is a user-facing display choice.** List target display candidates via `entities get <target-id>` and raise a dropdown; never silently default to `Id`. This applies only to `RELATIONSHIP` (`FILE` has no such choice).

    **CSV / sample-data inference — confirm every inferred type.** Run Rule 13 probes first so complex-field alternatives are grounded. For every column, label the chosen type **inferred** and name plausible alternatives; parseable timestamps, decimals, `0`/`1`, and UUID-shaped text are not self-confirming. Dropdown-confirm before `entities create`. Rule 12b applies to the whole proposal. Silence on a CSV import ≠ approval.

15. **Choice / relationship record values use lookup tokens, not labels.** Choice value → integer `NumberId` (single) or array of `NumberId`s (multi), from `choice-sets list-values`. Relationship value → target record's UUID `Id`. Filter / `groupBy` use the same tokens; `CHOICE_SET_MULTIPLE` filtering has special operator semantics—see [`records-query.md` → Filtering on Choice-Set Fields](records-query.md#filtering-on-choice-set-fields).

16. **Answer with `records query`, not from memory.** For counts, sums, filters, and lookups, issue a fresh `records query` and use the server response. Do not reuse cached values from previous turns or tool results. Exception: the `Id` returned by the same `records insert` just made.

17. **`records query` filters.** Body shape, per-type support, and unsupported-operator handling: [`filter-platform-contract.md`](filter-platform-contract.md). Operator whitelist: `=` `!=` `>` `<` `>=` `<=` `contains` `not contains` `startswith` `endswith` `in` `not in`; `equals` / `==` / `like` are rejected. `value` is a JSON string except `null` for empty checks. **Aggregate aliases return PascalCased in the response**—`alias: "total"` returns key `"Total"` on each row. **Return all fields by default**—omit `selectedFields` unless a subset is requested.

18. **Never hide or silently substitute after an error.** Surface the upstream message verbatim and state what failed. If a read-only request has one unambiguous correction (for example, the server names the required body property), apply it and report the correction; otherwise ask. Always ask before an alternative mutation; for an intentional negative probe, run only the requested variant and stop after capturing its result. Independent requested operations may continue when they do not depend on the failure; run multi-probe error checks as separate shell calls so every response is retained. Detailed error shapes are in the relevant topic reference.

19. **Resolve folder scope up front; pass `--folder-key` on folder-scoped targets.** Every `uip df` command touching a row accepts `--folder-key <GUID>`; `entities list` and `choice-sets list` also accept `--include-folders` (mutually exclusive). See [Folder Scope](#folder-scope) for the matrix. It is required on folder-scoped writes and recommended on reads. Lists default to **tenant-only**.

    **Mandatory scope-prompt flow.** If scope is not pinned, stop and ask via `AskUserQuestion`: (1) `Tenant level (no --folder-key)` vs `Folder-scoped`; (2) for folder scope without an inline GUID, offer `Provide folder GUID` (user-typed) or `List accessible folders` (pre-fetch `uip or folders list --output json`, dropdown labelled `<Name> — <Path>`, narrow first if >4). Resolve this before Rule 13 scope-specific discovery. Cache the folder list within the turn; echo chosen scope in the next message. Scope persists across follow-up turns unless switched.

    **Bypass clauses—skip the AskUserQuestion when ANY hold** (still announce the chosen scope in one line):
    - Prompt says *"do not ask"* / *"no confirmation needed"* / *"proceed without confirmation"*—proceed at **tenant level** unless folder context is inline. Scope only; destructive-op gates still fire (Rule 0).
    - Prompt names a folder inline or supplies a folder GUID / `folder_a_id`-style variable—proceed with that folder.
    - Prompt explicitly states tenant scope (*"tenant level"*, *"no folder"*, *"at the root"*).
    - Pure tenant-wide discovery read—default to `--include-folders` and announce.

20. **`records import` supports Basic types only.** `CHOICE_SET_*`, `RELATIONSHIP`, `FILE`, `AUTO_NUMBER` columns are ignored on import; optional columns land as `null`; **`isRequired` columns without a `defaultValue` fail the whole row** (`ErrorFileLink` entry per row). Sequence: (1) `entities get` → list unsupported columns; (2) tell the user which columns will be skipped and which rows will fail because a required unsupported column has no default; (3) offer `records insert --file <json>` (+ `files upload` for FILE) as the alternative; (4) invoke only after explicit confirmation. See [`bulk-import.md` → Complex Field Types Not Supported](bulk-import.md#complex-field-types-not-supported).

21. **`MULTILINE_MAX`—preview reads, no filter/sort.** `records list` / `records query` return a preview: content truncated to 10,000 characters with a `...[Truncated]` suffix or a size marker (`HasValue=true Length=N`), depending on the tenant. Full value is only via `records get`. Never echo a preview through `records update`; the server accepts it as a normal value and destroys the real content; omit the key instead. No filter/sort support (400). `lengthLimit` is a UTF-16 byte budget (max 131072 ≈ 65,536 chars). Full contract: [`entity-schema.md` → MULTILINE_MAX](entity-schema.md#multiline_max-fields) + [`records-query.md` → MULTILINE_MAX](records-query.md#multiline_max-fields--preview-vs-full-content).

## Folder Scope

Entities and choice sets are tenant-level or folder-scoped; records and files inherit the parent entity's scope.

- `--folder-key <GUID>` scopes the call to that folder. Pass the Orchestrator folder `Key` from `uip or folders list --output json`.
- `--include-folders` is valid only on `entities list` / `choice-sets list`, returns tenant plus every visible folder, and is mutually exclusive with `--folder-key`.

| Command(s) | `--folder-key` effect |
|---|---|
| `entities list`, `choice-sets list` | Filter mode. Omit both → tenant only; `--folder-key <key>` → that folder only; `--include-folders` → tenant + all visible folders. |
| `entities create`, `choice-sets create` | **Scope-bound**—required for folder placement; omit → tenant. |
| `entities get / update / delete`, `records *`, `files *`, `choice-sets list-values / update / delete`, `choice-set-values *` | Required on folder-scoped targets. |

**Cross-folder references** on `RELATIONSHIP` / `CHOICE_SET_*` fields are restricted to the same scope class. `RELATIONSHIP` requires `referenceFolderKey` when its target is folder-scoped, including same-folder bindings; choice sets resolve scope from `choiceSetId`. `FILE` is auto-wired and takes no reference fields. Full matrix: [`entity-schema.md` → Cross-folder references](entity-schema.md#cross-folder-references).

## Task Navigation

- Explore entities: `entities list` (`--folder-key`, `--include-folders`, or `--native-only` as needed) → `entities get <id>`.
- Choice-set CRUD: [`choice-sets.md`](choice-sets.md).
- Entity and field create/update/delete: [`entity-schema.md`](entity-schema.md).
- Federated entity create/update: [`federated-entity-creation.md`](federated-entity-creation.md).
- Solution-local entities: [`local-entities.md`](local-entities.md).
- Record read/filter/paginate/sort and insert/update/delete: [`records-query.md`](records-query.md) + [`filter-platform-contract.md`](filter-platform-contract.md).
- Aggregates/group-by: [`records-query.md` → Aggregates](records-query.md#aggregates-server-side).
- Bulk CSV import: [`bulk-import.md`](bulk-import.md).
- File attachments: [`file-attachments.md`](file-attachments.md).

## Troubleshooting (cross-cutting only)

For topic-specific errors, use the relevant reference. Otherwise apply Rule 18.

| Error | Cause | Fix |
|---|---|---|
| `unknown command: df` | Tool not installed | `uip tools install @uipath/data-fabric-tool@latest` |
| `Not logged in` / `HTTP 401` | Auth expired or invalid token | `uip login`; ensure `DataServiceApiUserAccess` scope is present |
| `HTTP 403` | Permission denied | Ensure account has Data Fabric permissions |
| `unknown option '--folder-key'` / `unknown option '--include-folders'` | Outdated tool | `uip tools install @uipath/data-fabric-tool@latest`; if still missing, surface as unsupported |
| `--folder-key and --include-folders are mutually exclusive` | Both flags passed on `entities list` / `choice-sets list` | Pick one |
| Entity / choice set created via `--folder-key <X>` doesn't appear in list | Lists default to tenant-only | Re-run with `--folder-key <X>` or `--include-folders` |
| Record write to a federated entity fails | Federated entities are read-only; data lives in the source | Write at the source; `--native-only` filters writable entities. Creating a federated entity **is** supported → [`federated-entity-creation.md`](federated-entity-creation.md) |

## Packaging into a Solution

To ship a folder-scoped entity or choice set in a deployable solution, use [`uipath-solution`](/uipath:uipath-solution). After creating the resource here, import it with `uip solution resources add --source remote`—**never hand-write `configuration.json` from `uip df entities get`**; the SDK read shape breaks upgrade with per-field `EntityConflict`. Full flow, `--source local` caveats, and drift recovery: [`develop-solution.md` → Data Fabric kinds](../../../uipath-solution/references/develop-solution.md#data-fabric-kinds).

If the entity is a **local entity**—the user explicitly asked for it to be authored inside the solution—skip import and author it with `uip df entities <verb> --local` per [`local-entities.md`](local-entities.md). It does not touch the tenant until solution deployment.