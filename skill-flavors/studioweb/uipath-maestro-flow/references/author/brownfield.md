<!--skill-flavor:brownfield-convert-resolve-executors:start-->
4. Publish executors or keep them in-solution, then find the in-solution ones with `uip solution resources list --kind Process --output json` (`solutionResources`).
<!--skill-flavor:brownfield-convert-resolve-executors:end-->

<!--skill-flavor:brownfield-common-edits-table:start-->
| **Add a resource node** | Discover in-solution projects with `uip solution resources list --kind Process --output json` (`solutionResources`), or the tenant registry for published resources; add with `Edit`; wire edges. Use the relevant plugin's `impl.md` and [editing-operations-json.md](editing-operations-json.md). |
<!--skill-flavor:brownfield-common-edits-table:end-->

<!--skill-flavor:brownfield-after-edits:start-->
1. Run `uip maestro flow validate new.flow --output json`. Fix errors and re-validate.
2. Run `uip maestro flow format new.flow --output json`. Run it before publish or debug (see "Always run `flow format` after edits" in [the Author capability index](CAPABILITY.md)); without it, stale or hand-edited `layout` data renders as misshapen rectangles in Studio Web.
<!--skill-flavor:brownfield-after-edits:end-->

<!--skill-flavor:brownfield-migrate-section:start-->
If `flow format` fails with `[inMemoryWorkflowToFileFormat] Refusing to serialize a vX workflow to the v<current> file format`, run:

```bash
uip maestro flow migrate new.flow --output json
```

`migrate` is lossless, walks the per-version migration chain (for example, `=js:` expression strings become rich expression objects), and bumps the file to the current version. Then run `flow format` and `flow validate`; both should pass. `flow validate` does not re-serialize and therefore does not check the version guard enforced by `format`. When this refusal appears, always migrate; do not assume the edit was wrong.
<!--skill-flavor:brownfield-migrate-section:end-->

<!--skill-flavor:brownfield-whats-next-dropdown:start-->
| **Publish** | Publish the open solution with `uip solution publish --location "<key or name>"`. Read the destinations from `uip solution publish --help` (`PublishLocations`) and ask the user which one when more than one exists and none was named; with no `--location` the host publishes to the personal workspace immediately and without a second confirmation. |
| **Debug** | Run the saved project with `uip flow debug` (two-token verb). Consent comes from the mandate, not from this menu — see the `flow debug` rule in [SKILL.md](../../SKILL.md). Selecting it here is the user asking for a run. |
<!--skill-flavor:brownfield-whats-next-dropdown:end-->
