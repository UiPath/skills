# DataServiceEval seed project

Sandbox template injected into every `tests/tasks/uipath-rpa/dataservice/smoke/*` task via `sandbox.template_sources`.

## Layout

| File | Purpose |
|------|---------|
| `project.json` | RPA Windows process. Pins `UiPath.DataService.Activities` to `[23.1.4-dev]` (local nupkg). `entitiesStores` points at `.entities/EntitiesStore.json`. |
| `NuGet.Config` | Adds `./packages` as a NuGet source so the local `.nupkg` resolves before public feeds. |
| `packages/UiPath.DataService.Activities.23.1.4-dev.nupkg` | Local activity-pack binary. Source of truth: `Entities-Desktop/Output/Packages/Activities/`. |
| `.entities/EntitiesStore.json` | Two pre-installed entities (`CodingAgentsEvalEntity`, `CodingAgentsEvalFileEntity`) with stable GUIDs. `Installed: true` so the agent skips `data-fabric-entities install`. |
| `Main.xaml` | Empty `Sequence` root with all `uda` / `udam` / `udd` / `upr` / `local` xmlns declarations + `TextExpression.NamespacesForImplementation` + `TextExpression.ReferencesForImplementation` pre-wired. Agent fills in activities. |

## What the agent does NOT need to do

- Run `uip rpa init` — project is scaffolded.
- Run `uip rpa packages install` — DS dependency is pinned.
- Run `uip rpa data-fabric-entities install` — `EntitiesStore.json` already has `Installed: true` for both entities.
- Hand-declare XAML namespaces — pre-declared on the root `<Activity>`.

## What the agent IS expected to do

- Read `.entities/EntitiesStore.json` for entity GUIDs + field GUIDs + types.
- Add the prompt-specified `uda:*` activity elements inside the `<Sequence>` block in `Main.xaml`.
- Run `uip rpa validate --file-path Main.xaml --project-dir . --output json` after edits.
- Run `uip rpa build "." --log-level Warn --output json` at the end. Both must exit clean.

## Known limitations

- **`DataService.DataServiceEval.dll` is not pre-baked.** It is generated client-side by Studio/`uip rpa` from `EntitiesStore.json` on first build. If `build` fails with `Cannot create unknown type '{clr-namespace:DataServiceEval}…'`, the agent (or task pre_run) must run `uip rpa data-fabric-entities install --add <ENTITY_NAME> --project-dir .` to materialize the DLL. This requires tenant auth — the smoke-rpa-skills.yml runner authenticates against alpha.uipath.com, so the install will only succeed if the two entities also exist on the runner's tenant.
- **Entity GUIDs are synthetic** (`a1b2c3d4-…` / `b2c3d4e5-…`). They match no live tenant. If the runtime resolver insists on tenant verification at build time, swap with real GUIDs from `CodingAgentsEvals` via `df entities get`.
- **23.1.4-dev vs 25.9 skill docs.** The skill teaches DS 25.9 patterns. API parity confirmed by the package author — but a smoke failure that names a 25.9-only property may indicate package drift.
