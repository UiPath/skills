# Solution Scenarios

Real multi-project recipes that the step-by-step files don't cover head-on. Each scenario has the setup, the behavior to expect, the gotcha that bites, and a fix. Read these before starting on a complex solution — most of them surface during `solution resource refresh` or `solution deploy run`.

> All scenarios assume you've already read [develop-solution.md](develop-solution.md) and [pack-and-deploy.md](pack-and-deploy.md). Each file links back to the relevant step.

---

## Symptom triage

Land here from a grep on an error message? Pick the matching row.

| You see... | Open |
|---|---|
| Suffix `_1` (or `_N`) on a resource file you didn't ask for | [same-name-across-folders](scenarios/same-name-across-folders.md) |
| Tool dialog in Studio Web won't open for one of two same-name tools | [same-name-across-folders](scenarios/same-name-across-folders.md) |
| `referenceKey` for an in-solution tool — do I use the cloud key or something else? | [intra-solution-references](scenarios/intra-solution-references.md) |
| Two projects bind the same cloud resource (queue/asset/bucket) — what does refresh do? | [shared-cloud-resource](scenarios/shared-cloud-resource.md) |
| `[1009] <kind> <name>: Invalid argument 'Value'` at deploy | [virtual-resource](scenarios/virtual-resource.md) |
| New asset/queue not on cloud — how do I ship it as part of the solution? | [virtual-resource](scenarios/virtual-resource.md) |
| `Synced 0 resources (1 already in solution)` on re-refresh | [virtual-resource](scenarios/virtual-resource.md) (idempotency section) |
| I want to add one virtual queue / asset / bucket without going through bindings | `uip solution resource add --source local --kind <kind> --name <name>` — see [develop-solution.md Step 9](develop-solution.md#step-9-add-a-resource-atomically) |
| I want to import one existing remote resource into the solution | `uip solution resource add --source remote --kind <kind> --name <name> --folder-path <folder>` — see [develop-solution.md Step 9](develop-solution.md#step-9-add-a-resource-atomically) |
| I want to delete a single resource by key | `uip solution resource remove <resource-key>` — see [develop-solution.md Step 10](develop-solution.md#step-10-remove-a-resource) |
| I want to change a field on an existing resource's spec | `uip solution resource edit <resource-key> --patch '{...}'` — see [develop-solution.md Step 11](develop-solution.md#step-11-edit-a-resource) |
| I edited a spec field but `refresh` didn't pick it up | Expected — `refresh` never overwrites a resource already in the solution. Use `resource edit` to mutate spec. |
| `resource edit` silently ignored a property I passed | The SDK skips unknown / reference / read-only props by design — see [manual-edits](scenarios/manual-edits.md) for what's editable vs not |
| My hand-edit got reverted on the next refresh | [manual-edits](scenarios/manual-edits.md) (the SDK re-derives bindings) |
| Other deploy / refresh failures (folder collision, suffix amplification, missing bindings, version collision) | [failure-modes](scenarios/failure-modes.md) |

---

## Scenarios

| File | When you need it |
|---|---|
| [same-name-across-folders](scenarios/same-name-across-folders.md) | Two bindings target a resource with the same name in different cloud folders. The SDK suffixes the second one `_1`. |
| [intra-solution-references](scenarios/intra-solution-references.md) | A coordinator project needs to invoke a sibling project that ships in the same solution and isn't on cloud yet. |
| [shared-cloud-resource](scenarios/shared-cloud-resource.md) | Two projects bind the same cloud resource (typically a shared queue/asset/bucket). Refresh dedups silently. |
| [virtual-resource](scenarios/virtual-resource.md) | Brand-new asset/queue/bucket shipped with the solution — no cloud counterpart yet. Refresh creates a virtual stub; deploy needs a value or link. |
| [manual-edits](scenarios/manual-edits.md) | The CLI doesn't cover the field you need to edit. What's safe to hand-edit on solution-level files and deploy configs, what isn't. |
| [failure-modes](scenarios/failure-modes.md) | Cross-cutting symptom→cause→fix table for deploy and refresh failures that don't fit a single scenario. |

---

## Related

- [solution-overview.md](solution-overview.md) — Overview, lifecycle diagram, command tree
- [develop-solution.md](develop-solution.md) — Step-by-step: new, project add, refresh, list
- [pack-and-deploy.md](pack-and-deploy.md) — Step-by-step: pack, publish, deploy, configuration
- [activate-and-manage.md](activate-and-manage.md) — Activate, uninstall, manage packages
