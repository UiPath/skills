# UiPath Data Fabric (`uip df`)

Data Fabric is UiPath's typed structured store: entities contain records, and FILE fields contain binary attachments.

Use `uip df <subject> <verb> --output json` for CLI operations. Use `uipath-maestro-flow` for Data Fabric nodes in a `.flow`. Read **Critical Rules**, then load only the needed topic reference.

## Not Supported

Do not change field types, create federated entities, write federated records, or work around rejected names. FILE values require `files upload`; record writes silently ignore them. Use supported alternatives in the topic references.

**Immediate refusal:** If the prompt establishes a categorical restriction—for example, a Salesforce-backed list is federated or a field type must change—refuse immediately, cite this rule, and offer the supported alternative. Do not re-verify with `entities list`, `entities get`, or other discovery.

## Critical Rules

> ### ⛔ Destructive Operations — STOP and Confirm
>
> Never invoke an operation below without explicit approval in the current turn. Approval is the user typing *yes / approved / proceed / delete / confirm* in response to a previewed plan. Implied consent, prior-turn approval, and “clean up” are not approval.
>
> | Operation | CLI shape | Detail |
> |---|---|---|
> | Delete entity | `entities delete <id> --yes --reason "<why>"` | Rule 10 — list dependents first; never cascade silently |
> | Delete field | `entities update <id> --body '{"removeFields":[...]}' --yes --reason "<why>"` | Rule 11 — for `CHOICE_SET_*` / `RELATIONSHIP`, ask whether to delete the reference target |
> | Delete record(s) | `records delete <entity-id> <id1> <id2> --yes --reason "<why>"` | Per-record `--yes --reason` required |
> | Delete file attachment | `files delete <entity-id> <record-id> <field-name> --yes --reason "<why>"` | Irreversible |
> | Delete choice set | `choice-sets delete <id> --yes --reason "<why>"` | Verify no entity binds it first |
> | Delete choice-set value | `choice-set-values delete <id> --yes --reason "<why>"` | Shifts later NumberIds; see [`choice-sets.md`](choice-sets.md) |
> | Create / schema-alter | `entities create`, `entities update` with `addFields`/`updateFields`/`removeFields`, `choice-sets create`, `choice-set-values create` | Rule 14 — preview and wait for explicit approval |
>
> For every operation above: (1) resolve folder scope first (Rule 19); (2) show the exact target and what will be lost; (3) list dependents for deletes (Rules 10/11); (4) wait for explicit *yes / proceed / delete*; (5) run with `--folder-key <key>` when folder-scoped and `--yes --reason "<user-supplied reason>"`.
>
> For `CHOICE_SET_*` / `RELATIONSHIP` field deletes, ask with a dropdown: `Delete only the field` / `Also delete the referenced choice set / target entity` / `Stop`. Give each downstream delete its own confirmation cycle.

0. **Ask liberally; never assume.** At unresolved scope, folder, entity, field, cascade, or ambiguous-name decisions, stop and raise an `AskUserQuestion` dropdown. Render multi-option choices as dropdowns, not markdown lists.

Destructive gates cannot be bypassed by “do not ask”, “no confirmation needed”, or “proceed without confirmation”; Rule 19 bypasses apply only to scope. Do not re-ask when the user explicitly approves a specific resource and operation, such as *“I approve creating CE_X and adding fields A, B, C”* or *“yes, delete X”*. General requests and “do not ask” are not approval. Rule 14 preview → apply still holds.

Never self-resolve scope, including for “no reachable user”, “single-turn”, or “offline test”. Halt and state the open question.

1. **Install first.** If `uip df` returns “unknown command”, run `uip tools install @uipath/data-fabric-tool@latest`.

2. **Verify login and tenant first.** Run `uip login status --output json`; switch with `uip login tenant set <tenant>` if needed. Find full login setup in `uipath-platform`.

3. **Resolve entity ID first.** Run `entities list` before any operation; never assume an ID.

4. **Validate names.** Entity and choice-set names allow letters, digits, and underscores; field names allow letters and digits only. All are 3–100 characters and start with a letter. Reserved system field names are case-insensitive: `Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`, `RecordOwner`. C#/VB keywords are rejected case-insensitively; the CLI also rejects live-confirmed SQL-reserved words such as `Order` and `Group`, while ordinary names such as `Status` and `Key` are accepted. Choice-set value `Name` has a different validator: [`choice-sets.md` → Value Name validation](choice-sets.md#value-name-validation). Read full rules in [`entity-schema.md` → Name Validation](entity-schema.md#name-validation).

5. **Update records with `Id`.** Every element of `records update`—single or batch—must contain JSON field `"Id"`; validation precedes row resolution and otherwise returns `Record must include 'Id'`. See [`records-query.md` → Update Records](records-query.md#update-records).

5b. **Treat `isUnique` as immutable.** `updateFields` may return `Result: Success` while silently ignoring a change. To change it, use `removeFields` then `addFields` with `isUnique: true`; this drops every existing value in the column. Verify every `updateFields` by re-reading `entities get` and comparing. See [`entity-schema.md` → Not Supported](entity-schema.md#not-supported) and [Verify-after-update](entity-schema.md#verify-after-update--never-trust-the-success-response-alone).

6. **Exclude FILE keys from record payloads.** Never put FILE-typed keys in `records insert`, `records update`, or `records import`; paths, base64, UUIDs, and `null` are silently stripped and the CLI returns `Result: Success`. Insert the row without the FILE column, then run `files upload <entity-id> <record-id> <field-name> --file <path>`; use it to replace, `files delete` to clear, and `files download` to retrieve. See [`file-attachments.md`](file-attachments.md).

7. **Match CSV headers to display names.** Headers must exactly match `Fields[].DisplayName` (case-sensitive), not internal `Name`; discover them with `entities get`. See [`bulk-import.md`](bulk-import.md).

8. **Prevent duplicates.** Run `entities list` first and reuse an existing entity. Entity and choice-set `displayName` values must also be unique. If none is supplied, derive a collision-resistant display name from the requested `Name`, not a generic label. On `409` / `RetryWillNotFix`, do not repeat creation or treat an environment ID from the error as a resource ID; surface the conflict and ask for another name or display name.

9. **Use native entities only.** Run `entities list --native-only` before any write. Federated entities are read-only.

10. **Discover entity dependents before deletion.** The destructive-operation gate applies. Run `entities list --output json`, scan `Fields[].ReferenceEntity.Id == <id>` for inbound references and `Fields[].ChoiceSetId` for choice sets used by the entity. Ask per dependent whether to delete, leave, or stop. See [`entity-schema.md` → Deleting an Entity](entity-schema.md#deleting-an-entity).

11. **Delete fields with `removeFields` names.** Use `{"name":"…"}`—not `id` as with `updateFields`. For `CHOICE_SET_*` / `RELATIONSHIP`, ask the cascade dropdown before invoking and show other bindings. Deleting a FILE field drops only the column; never offer to delete the platform-managed storage entity. See [`entity-schema.md` → Deleting a Field](entity-schema.md#deleting-a-field).

12. **Configure complex fields and lookups.** `CHOICE_SET_*` requires `choiceSetId`; `RELATIONSHIP` requires `referenceEntityId` and `referenceFieldId`; FILE requires neither because the server auto-wires it. Create the target entity first. A described link such as “each order has a Customer” is `RELATIONSHIP`, never `STRING` or `UUID`. See [`entity-schema.md` → Supported Field Types](entity-schema.md#supported-field-types).

12b. **Do not emit UI-broken types.** Never use `INTEGER`, `BIG_INTEGER`, `FLOAT`, `DOUBLE`, `UUID`, or `DATETIME` as field types; although accepted by the API, they render broken in the Data Fabric UI. Substitute according to [`entity-schema.md` → UI-broken types](entity-schema.md#ui-broken-types--do-not-use). Rule 14 proposals must not name any of these six types.

13. **Pick or create explicitly.** For entities, choice sets, and relationship targets, do not auto-create or silently select the first match. List, show matches in a dropdown, and ask *pick from these or create new?* Create only with explicit approval.

- Primary entity: run `entities list --native-only` with `--folder-key` or `--include-folders` as scope requires.
- Choice set: run `choice-sets list`.
- Relationship target: run `entities list --native-only`; never substitute `STRING` or `UUID`.
- FILE does not use this flow; the server auto-wires storage (Rules 6/12).

Make one focused discovery pass per unresolved choice. Do not repeatedly re-list unchanged resources, search the filesystem for documentation, inspect installed CLI package source, create probe entities, or run mutation experiments outside requested scenarios. Use this reference and `--help`. Pagination needed to complete discovery and post-mutation reads to verify changes are allowed. For an optional resource requested only if available, inspect once; if no clear match exists, skip it without creating a probe.

14. **Preview every schema or choice-set creation/change.** Before `entities create`, `entities update` with `addFields`/`updateFields`/`removeFields`, `choice-sets create`, or `choice-set-values create`: (1) compose the full proposal—entity name, `displayName`, `description`, and every field with UPPERCASE `type` plus `isRequired`, `isUnique`, `lengthLimit`, `maxValue`/`minValue`, `decimalPrecision`, `defaultValue`, `choiceSetId`, and `referenceEntityId`/`referenceFieldId` as applicable; (2) render a table or formatted JSON block, not a raw CLI command; (3) wait for approval and apply exactly, without silently adding, dropping, renaming, or retyping.

For `RELATIONSHIP`, `referenceFieldId` is a user-facing display choice: run `entities get <target-id>`, list display candidates, and raise a dropdown; never default silently to `Id`. This does not apply to FILE.

For CSV/sample inference, run Rule 13 probes first. Label every inferred column type **inferred**, name plausible alternatives, and confirm each with a dropdown before `entities create`; parseable timestamps, decimals, `0`/`1`, and UUID-shaped text are not self-confirming. Rule 12b applies to the complete proposal. Silence on CSV import is not approval.

15. **Use lookup tokens for choice and relationship values.** Choice values use integer `NumberId` (single) or an array of `NumberId`s (multiple), obtained from `choice-sets list-values`. Relationship values use the target record UUID `Id`. Filters and `groupBy` use the same tokens; `CHOICE_SET_MULTIPLE` has special filter operators. See [`records-query.md` → Filtering on Choice-Set Fields](records-query.md#filtering-on-choice-set-fields).

16. **Query answers freshly.** For counts, sums, filters, and lookups, run a fresh `records query` and use its response; never reuse cached values. The exception is the `Id` returned by the same `records insert` just performed.

17. **Follow the records-query contract.** Body shape, per-type support, and unsupported operators are in [`filter-platform-contract.md`](filter-platform-contract.md). Supported operators are `=` `!=` `>` `<` `>=` `<=` `contains` `not contains` `startswith` `endswith` `in` `not in`; `equals`, `==`, and `like` are rejected. `value` is a JSON string except `null` for empty checks. Aggregate aliases return PascalCased response keys: `alias: "total"` returns `"Total"` on each row. Return all fields by default; omit `selectedFields` unless a subset is requested.

18. **Surface errors; do not hide or substitute.** Report the upstream message verbatim and state what failed. For an unambiguous read-only correction, such as a server-named body property, apply it and report the correction; otherwise ask. Ask before any alternative mutation. For an intentional negative probe, run only the requested variant and stop after capturing its result. Independent requested operations may continue when they do not depend on the failure. Run multi-probe error checks as separate shell calls so every response is retained. Use topic references for detailed error shapes.

19. **Resolve folder scope up front.** Every `uip df` command touching a row accepts `--folder-key <GUID>`; `entities list` and `choice-sets list` also accept `--include-folders` (mutually exclusive). Lists default to tenant-only. See [Folder Scope](#folder-scope).

If scope is not pinned, stop and raise `AskUserQuestion`: (1) `Tenant level (no --folder-key)` or `Folder-scoped`; (2) for folder scope without an inline GUID, `Provide folder GUID` or `List accessible folders`. For the latter, pre-fetch with `uip or folders list --output json`, show a dropdown labelled `<Name> — <Path>`, and narrow first if >4. Cache the list within the turn, echo the chosen scope in the next message, and persist it across follow-up turns unless switched. Resolve scope before Rule 13 discovery.

Skip this scope question, but announce the chosen scope, when the prompt says “do not ask”, “no confirmation needed”, or “proceed without confirmation” (use tenant level unless folder context is inline); supplies a folder name, GUID, or `folder_a_id`-style variable; explicitly says “tenant level”, “no folder”, or “at the root”; or requests pure tenant-wide discovery (use `--include-folders`). These bypass clauses do not bypass destructive confirmation.

20. **Treat `records import` as Basic-types only.** `CHOICE_SET_*`, `RELATIONSHIP`, `FILE`, and `AUTO_NUMBER` columns are ignored; optional columns become `null`, while `isRequired` columns without `defaultValue` fail the whole row with an `ErrorFileLink` entry per row. Before invoking: (1) run `entities get` and list unsupported columns; (2) tell the user which will be skipped and which rows will fail; (3) offer `records insert --file <json>` plus `files upload` for FILE; (4) invoke only after explicit confirmation. See [`bulk-import.md` → Complex Field Types Not Supported](bulk-import.md#complex-field-types-not-supported).

21. **Handle `MULTILINE_MAX` markers safely.** `records list` / `records query` return `HasValue=true Length=N`; retrieve the full value only with `records get`. Never send the marker back through `records update`; omit the key or the marker is stored as content and destroys the real value. `MULTILINE_MAX` cannot be filtered or sorted (400). `lengthLimit` is a UTF-16 byte budget, maximum 131072 ≈ 65,536 characters. See [`entity-schema.md` → MULTILINE_MAX](entity-schema.md#multiline_max-fields) and [`records-query.md` → MULTILINE_MAX](records-query.md#multiline_max-fields--marker-vs-full-content).

## Folder Scope

Entities and choice sets are tenant-level or folder-scoped; records and files inherit the entity scope.

- `--folder-key <GUID>`: pass the Orchestrator folder `Key` from `uip or folders list --output json`.
- `--include-folders`: only for `entities list` / `choice-sets list`; return tenant plus visible folders and do not combine with `--folder-key`.

| Command(s) | `--folder-key` effect |
|---|---|
| `entities list`, `choice-sets list` | Filter mode: omit for tenant only; use `--folder-key <key>` for that folder; use `--include-folders` for tenant plus visible folders |
| `entities create`, `choice-sets create` | Scope-bound; required for folder placement; omit for tenant |
| `entities get / update / delete`, `records *`, `files *`, `choice-sets list-values / update / delete`, `choice-set-values *` | Required for folder-scoped targets |

Cross-folder `RELATIONSHIP` / `CHOICE_SET_*` references must remain within the same scope class. `RELATIONSHIP` requires `referenceFolderKey` for a folder-scoped target, including same-folder bindings; choice sets resolve scope from `choiceSetId`. FILE is auto-wired and accepts no reference fields. See [`entity-schema.md` → Cross-folder references](entity-schema.md#cross-folder-references).

## Task Navigation

| Task | Reference |
|---|---|
| Explore entities | `entities list` (`--folder-key`, `--include-folders`, or `--native-only` as needed) → `entities get <id>` |
| Choice sets — full CRUD (sets and values) | [`choice-sets.md`](choice-sets.md) |
| Create / update / delete entity, add/remove/update fields | [`entity-schema.md`](entity-schema.md) |
| Read / filter / paginate / sort records | [`records-query.md`](records-query.md) + [`filter-platform-contract.md`](filter-platform-contract.md) |
| Insert / update / delete records | [`records-query.md`](records-query.md) |
| Aggregates / group-by | [`records-query.md` → Aggregates](records-query.md#aggregates-server-side) |
| Bulk CSV import | [`bulk-import.md`](bulk-import.md) |
| File attachments | [`file-attachments.md`](file-attachments.md) |

## Troubleshooting (cross-cutting only)

| Error | Cause | Fix |
|---|---|---|
| `unknown command: df` | Tool not installed | Run `uip tools install @uipath/data-fabric-tool@latest` |
| `Not logged in` / `HTTP 401` | Auth expired or invalid token | Run `uip login`; ensure `DataServiceApiUserAccess` scope is present |
| `HTTP 403` | Permission denied | Ensure Data Fabric permissions |
| `unknown option '--folder-key'` / `unknown option '--include-folders'` | Outdated tool | Run `uip tools install @uipath/data-fabric-tool@latest`; if still missing, surface as unsupported |
| `--folder-key and --include-folders are mutually exclusive` | Both flags passed to a list | Pick one |
| Entity / choice set created via `--folder-key <X>` missing from list | Lists default to tenant-only | Re-run with `--folder-key <X>` or `--include-folders` |

For any other error, apply Rule 18. Use topic references for topic-specific errors.

## Packaging into a Solution

To ship a folder-scoped entity or choice set, use [`uipath-solution`](/uipath:uipath-solution). After creating the resource here, import it with `uip solution resources add --source remote`. Never hand-write `configuration.json` from `uip df entities get`; the SDK read shape breaks upgrades with per-field `EntityConflict`. See [`develop-solution.md` → Data Fabric kinds](../../../uipath-solution/references/develop-solution.md#data-fabric-kinds).