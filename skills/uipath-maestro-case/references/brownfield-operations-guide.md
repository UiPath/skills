# Composite Brownfield Operations

Load this guide only for an edit routed here by [brownfield.md](brownfield.md), which selects the exact plugin owners. Also load [case-editing-operations.md](case-editing-operations.md) for preservation, sweep, narrow-edit, and validation primitives. The operation-specific deltas follow.

## Insert a stage between two existing stages

1. Add the new stage through the stage owner, preserving existing node order and all task sets. Add tasks only when requested, through their selected task owners.
2. Give the new stage entry conditions for every intended upstream route.
3. Repoint every affected downstream stage-entry consumer and matching source-exit consumer from the old hand-off to the new stage. Preserve all unrelated routes and DNF branches.
4. Never add an edge. Reachability is condition-driven.

## Replace a placeholder task with an enriched task

Adopt the placeholder in place: keep its `id`, `elementId`, placement, envelope, and conditions. Resolve metadata through the current registry Rule-3/Rule-17 gate: reuse the session's successful normal pull and run `--force` only after the user selects Force; the placeholder guide's older unconditional-force upgrade step does not override this gate. Add only the selected owner's resource fields and schema delta; retain every compatible input and output. Reuse a deduplicated binding pair when available. Because adoption adds a resolved resource binding, synchronize [bindings_v2](bindings-v2-sync.md) and refresh resources before debug or publish.

## Re-sync a task after its source schema changed

1. Fetch current metadata. For non-connectors, follow the existing Rule-3/Rule-17 gate: reuse this session's successful normal pull; never force unless the user chose Force. For connectors, fetch the current complete spec through the connector owner.
2. Reconcile only owner-defined resource fields and changed `data.inputs[]` / `data.outputs[]`. Keep the task identity, placement, conditions, unaffected schema entries, and unknown fields.
3. Rebind added, renamed, or retyped inputs through the binding owner. Sweep every removed or renamed output and explicitly preserve, repoint, or remove each consumer.
4. Synchronize `bindings_v2.json` and refresh resources only when the top-level binding set changed. A schema-only resync leaves the sidecar untouched.

## Repoint a non-connector task at a different resource

1. Resolve the new resource under the existing registry gate and update `registry-resolved.json` when that build sidecar exists; do not synthesize an absent sidecar. Retain the selected task owner's zero-match fallback.
2. Treat the `name` / `folderPath` entries sharing one `resourceKey` as a pair. If no other consumer uses the old pair, update it in place. If shared, create or reuse the new deduplicated pair, repoint this task, and prune the old pair only when its remaining reference count is zero.
3. Resync the task schema against the newly selected resource using the preceding recipe. If task type also changes, use the new type's owner for its `type`, resource fields, and `data`, while retaining task identity and entry conditions.
4. Synchronize `bindings_v2.json` and refresh resources because the selected resource changed.

## Move a task to a different stage or lane

1. Keep the task `id`. Recompute the task's stage-scoped `elementId`, the owned input/output `elementId` values, and connector-rule input/output `elementId` values. Root companions with `elementId: "root"` do not move.
2. Remove the task from its source inner task set, drop that set only if empty, and insert into the destination without disturbing either stage's remaining task-set order. Only explicitly parallel siblings share an inner set; sequential work remains in consecutive single-task sets.
3. Sweep consumers: cross-task triples retain `sourceTask` but change `sourceStage`; stable output-ID expressions remain unchanged. Verify the moved task still precedes its consumers.
4. Reconcile both directions of task gating. Fix destination-invalid dependencies on the moved task and source-stage tasks that still select the moved task. Preserve valid `current-stage-entered` behavior.
5. If `id-map.json` exists, update the task's `stageId` and every moved task-entry condition mapping's `stageId`; keep their stable owned IDs, `ruleId`, and task `targetId`.
6. For a connector task and any connector-bound task-entry rule, copy the complete owner-managed raw cache to its new elementId-keyed path, update working audit references, and leave the old cache audit-only. Never reconstruct the payload or reuse it for another target.
7. Update this task's existing `registry-resolved.json` stage association when that audit sidecar exists; preserve its selection/contract metadata and do not synthesize an absent sidecar.

## Rename or delete a global variable or argument

First distinguish an internal Case variable from an In/Out argument:

- **Internal variable:** rename its readable resolver `id`/`name` and only owner-defined pointers, then rewrite every swept consumer. Delete only after consumers are repointed or removed.
- **In argument:** preserve its random `variables.inputs[].id`; rename the formal `name`, readable companion `id`/`name`, and owner-defined bridge `name`/`var`, while the bridge `source` keeps pointing to the unchanged formal ID. Delete the formal, companion, and bound-trigger bridge together after the consumer sweep.
- **Out argument:** preserve its random `variables.outputs[].id`; rename the formal `name`/`var` and companion `id`/`name`, then rewrite consumers. Delete both formal and companion after handling producers/consumers.

After an In/Out rename or delete, recompute affected `entryPoints[].input` / `.output` schemas through [entry-point sync](entry-points-sync.md); preserve entry identity and envelope. Synchronize `bindings_v2.json` only if top-level bindings changed.

## Change a variable's type or default

Keep resolver and formal-slot IDs. Apply the variable owner's type/default rules to every slot for that category: an internal companion plus every producing trigger bridge's `type` when trigger-sourced; both Out formal and companion slots; or the In formal, companion, and each bound-trigger bridge. Defaults remain only on owner-defined slots. Use the JSON-schema and file-type carve-outs and recheck swept expressions. For an In/Out argument, recompute affected entry-point schemas so name, type, default, body, and required stay externally accurate.

## Modify or remove an SLA or escalation

Address rules in `metadata.slaRules[]` or a stage's `data.slaRules[]` by stable `sla_` ID; address nested escalations by `esc_` ID.

- Modify only requested timing/expression or escalation fields. Preserve recipients and response fields not selected for change. Keep conditional rule priority and the `=js:true` default last; retain the owner's at-risk-only field rules.
- Before removing a rule, sweep its `slaId` and every nested `escalationId`, then remove only that `sla_` mapping and its nested `esc_` mappings from an existing `id-map.json`. Before removing one escalation, sweep its `escalationId` and remove only that `esc_` mapping. Explicitly repoint or remove each response consumer; never convert notify-only, start-task, enter-stage, exit-stage, or exit-case behavior implicitly. Remove an empty `slaRules` key as the SLA owner requires, but retain `escalationRule: []` when only the final escalation is removed.

## Add or repair an SLA response

Choose notify-only, start-task, enter-stage, exit-stage, or exit-case through the response owner before editing. Notify-only changes the escalation and adds no task, stage, or condition. A start-task response adds the follow-up task inside the breached stage and places `sla-status-change` on that task's own task-entry condition; it never re-enters the breached stage. For any graph response, apply the response owner's status and interrupting rules and recheck its four defects that structural validation cannot detect.

## Replace a trigger with a different type

Keep the trigger ID and owner-retained envelope. Replace only target-owned configuration fields, then use the variable owner to recompose that trigger's outputs and root companions while retaining every compatible In-argument bridge. Sweep formal slots, companions, bridges, and consumers before pruning a spec-derived output.

When either source or target is event, reconcile its target-local raw cache, `trigger-spec-cache.json` T-entry, connector bindings, and IS cache through the event/common owners. Converting away from event removes the derived T-entry and recomposes outputs from remaining triggers; a retained full-response cache is audit-only and cannot repopulate it. Converting to event runs the current target-local cache/splice pipeline. If unresolved after the existing selection gate, use the event owner's placeholder fallback; never fabricate connector IDs.

Update the matching `entry-points.json` item in place through the entry-point owner, retaining its `uniqueId`, trigger fragment, order, and unknown fields. Synchronize `bindings_v2.json` when top-level bindings change and refresh resources.

## Re-target an event trigger (same type, different event)

Run the integrated target-local raw-cache pipeline and splice the new complete spec's `Data.CaseShape` subtrees using only owner-permitted substitutions. Never summarize or reconstruct connector payloads. Keep the trigger ID and envelope; replace only event-owned configuration. Reconcile bindings, outputs, formal slots, companions, bridges, and consumers before pruning zero-reference remnants. Update the matching entry point in place. Synchronize bindings/connection cache and refresh resources for the new event. Use the event placeholder when unresolved.

## Convert a Stage to/from an Exception Stage

Keep the Stage node type and ID. Convert to secondary using the stage owner's `stageType` representation; convert to primary by restoring the owner-defined primary representation. Ensure the result remains reachable. Reconcile every forward/reverse condition consumer: secondary stages stay outside the normal required-stage chain and return to origin when applicable; primary stages participate in normal predecessor/successor routing. Preserve DNF. `isInterrupting` belongs to the containing stage-entry condition object and changes only when requested behavior changes.

## Re-wire a stage transition — no edges

Repoint every matching target-entry and source-exit consumer, not just the first. Preserve rule IDs, DNF branches, and unrelated routes. Never create an edge.

<!-- END: brownfield-operations-guide.md -->
