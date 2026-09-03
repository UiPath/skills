# solution-skeleton: what it is and what gets renamed

`solution-skeleton/` is a verbatim copy of a known-good Studio Web export's manifests. No job
source is included: the job is staged in as the project's root `main.ts` at pack time, which is the
whole point of the staging step.

It is the fallback for phase 1. The primary path is `uip solution init` plus `uip functions new
--empty` plus `uip solution projects add`, verified live to produce job-capable
(`ProcessType=Function`) releases. `scaffold_solution.py --template` instantiates the skeleton.

`TagOverdueTicketProcess` is the exemplar: the one project directory, and the boilerplate every
instantiated project is copied from. The skeleton is trimmed to exactly this one process. The
original export also carried descriptors and manifest rows for four other processes (`Test HTTP`,
`HoldInvoicesProcess`, `FlagBigOrderProcess`, `ApplyTaxProcess`) that shipped no project directory;
instantiation never read them, so they were removed rather than kept as residue. The manifests'
`Projects[]` arrays list only the exemplar and are replaced wholesale at instantiation anyway.

## Renamed or regenerated at instantiation

| File | Occurrence | What happens |
|---|---|---|
| `Solution.uipx` | `SolutionId` | kept as-is. The `.uipx` carries the id; template mode does not mint a fresh one, because only `uip solution init` does that. See the warning below. |
| `Solution.uipx` | `Projects[]` | replaced by one entry per requested project, each with a fresh `Id` GUID and `Type: "Function"` |
| `SolutionStorage.json` | `SolutionId` | kept, matching `Solution.uipx` |
| `SolutionStorage.json` | `Projects[]` | replaced by one entry per requested project, each with a fresh `ProjectId` |
| `TagOverdueTicketProcess/` | directory name | copied to `<ProjectName>/` once per requested project |
| `<ProjectName>/project.uiproj` | `Name` | the project name |
| `<ProjectName>/uipath.json` | `name`, `projectId`, `id` | the project name, and a fresh GUID matching `SolutionStorage.json`'s `ProjectId` |
| `<ProjectName>/uipath.json` | `functions` | rewritten to `{<jobName>: "functions/<jobName>.ts:default"}` from the mapped job's filename; `uip functions pack` rebuilds this map by scanning `functions/`, so it only has to agree with what staging places there |
| `<ProjectName>/package.json` | `name` | the project name, lowercased (npm requires it) |
| `<ProjectName>/package.json` | `devDependencies` | the SDK added when absent, and any `dependencies` block dropped. The SDK is a devDependency for local typechecking only: `type<T>()` is erased at compile time and `defineFunction` comes from the runtime, so nothing in this pipeline installs anything. |
| `<ProjectName>/.npmrc` | whole file | written when absent: `@uipath` scope -> GitHub Packages, token as `${GH_NPM_REGISTRY_TOKEN}`, never a literal |
| `<ProjectName>/entry-points.json` | `entryPoints[0].uniqueId`, `filePath` | fresh GUID; `filePath` set to `content/main.ts`. The staging step rewrites this file with the schemas derived from this project's own job, carrying this uniqueId over because the bindings reference it. |
| `<ProjectName>/entry-points.json` | `input` / `output` schemas | **absent from the skeleton on purpose.** They are the contract the platform validates against, and they are per-job. When the skeleton carried the exemplar's schemas, a job whose contract could not be lowered inherited them and deployed under a contract that had nothing to do with it -- passing every check and faulting at invoke time. There is now nothing to inherit, and staging refuses rather than falling back. |
| `<ProjectName>/bindings_v2.json` | `key`, `id`, `EntryPointUniqueId` | fresh GUIDs, the last matching `entry-points.json` |
| `<ProjectName>/bindings_v2.json` | `metadata.Name`, `metadata.Slug` | the action name |
| `<ProjectName>/tsconfig.json` | nothing | copied unchanged. `moduleResolution: bundler` is load-bearing for the ESM-only SDK. |
| `resources/solution_folder/package/<ProjectName>.json` | `name`, `spec.name`, `projectKey`, `key` | the project name, the `.uipx` project `Id`, and a fresh key |
| `resources/solution_folder/process/function/<ProjectName>.json` | `name`, `spec.name`, `spec.packageName`, `projectKey`, `dependencies[0].name`, `spec.package.key` | the project name, `<SolutionName>.function.<ProjectName>`, the `.uipx` project `Id`, and the package descriptor's key |
| `jobs.map.json` | `projects` | rewritten to map each project to its job source path |

`resources/solution_folder/**` is the part that makes a release a job rather than an HTTP endpoint.
`kind: process`, `type: function`, `spec.type: "Function"` and `targetFrameworkValue: "Portable"` are
what produce a `ProcessType=Function` release, so do not prune that tree when trimming the template.

## Warning: the SolutionId is the export's

Template mode reuses the exported `SolutionId`. Two solutions carrying the same id collide on
`uip solution upload`, which probes Studio Web for it. This pipeline never uploads to Studio Web, so
the collision does not arise on the pack, publish, deploy route. If the solution ever needs to reach
Studio Web, scaffold it with `uip solution init` instead and take the id that command mints.
