# Fresh inline resource correction

Correction-only procedure for a resource built by the current Rule 17 Create flow. Contract derivation, comparison, recovery selection, and persistence belong to [resource-interface-resolution.md](../../resource-interface-resolution.md); build orchestration and registration belong to [registry-discovery.md](../../registry-discovery.md).

This procedure has no task-type branches. The owning plugin supplies the builder skill, authoritative local contract paths, and a self-contained correction brief.

## Preconditions

All must hold:

- `origin` is `fresh` (built during the current Create flow);
- the sibling is not registered in the solution, published, deployed, or executed;
- the resolver found a semantic blocking/adaptable mismatch;
- the user explicitly chose `Correct fresh resource`;
- the plugin declares `correct-fresh`.

An existing local sibling, adopted residual from an earlier run, or tenant resource is never corrected in place. Use adapt, create a uniquely named replacement when supported, select another candidate, or defer.

## Correction brief

Delegate to the same owning skill that built the resource. Do not call `init`, rename the project, change the solution manifest, register, publish, deploy, or execute. Provide only:

```text
Correct the existing fresh UiPath resource in place by following <owning-skill>.
  Resource path: <absolute unregistered sibling path>
  Requested inputs:  <effective requested inputs [{name,type?,required}]>
  Requested outputs: <effective requested outputs [{name,type?}]>
  Blocking diff:     <exact missing/reversed/incompatible/extra-required findings>

Preserve compatible native types and unrelated implementation. Make only the resource-owned
contract edits needed for the requested interface. Do not initialize, rename, register,
publish, deploy, or execute. Keep every contract mirror required by the owning skill in sync.
Return JSON: { corrected: bool, path, error? }
```

The requested contract is authoritative. Exact case-sensitive field names and directions stay pinned. Do not ask the correcting skill to synthesize Case conversion expressions or coerce fields to `string`.

## Retry and outcome

After correction, reacquire through the plugin's declared `local-entry-points` provider and rerun the canonical comparison.

- Compatible/adapted → persist the new `actualContract`; return to registration.
- Still blocking → offer one final `Retry correction` / `Skip (defer)` choice.
- Second failed attempt, `corrected:false`, dead sub-agent, or unreadable contract after the provider retry → `deferred`; do not register; emit the task placeholder.

Maximum two correction attempts per fresh resource. Every attempt and diff is appended to `interface-resolved.json.decisions`. Never report a blocking correction failure as a warning-only resolved resource.
