# uipath-rpa — UIA Boundary Rules

This skill must work against every future version of `UiPath.UIAutomation.Activities`. UIA CLI subcommands, skill invocation arguments, internal procedure step numbers, and artifact filenames all evolve with the UIA package — the skill must not encode any of them.

## Boundary

**Stays in `skills/uipath-rpa/`:** policy, decision logic, critical rules, skill names, data-model names, public UIA API surface (`NApplicationCard`, `Descriptors`, `uiAutomation` service, etc.), and pointers to UIA docs.

**Lives in the UIA package docs** (ships to `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/`): CLI subcommand syntax, skill invocation arguments, internal procedure step numbers, artifact filenames, bash blocks invoking `uip rpa uia ...`, flag tables, troubleshooting entries.

## Forbidden in skill files

None of these may appear under `skills/uipath-rpa/`:

- **Internal step numbering:** `TARGET-<digit>`
- **UIA subcommands:** `interact click`, `interact type`, `snapshot capture`, `snapshot filter`, `resolve-default-selector`, `get-screens`, `get-elements`, `link-element`, `link-screen`, `get-screen-xaml`, `get-elements-xaml`, `create-screen`, `create-elements`, `indicate-application`, `indicate-element`
- **UIA-specific flags:** `--window`, `--elements`, `--semantic`, `--no-improve`, `--folder-path` (UIA), `--parent-id`, `--parent-name`, `--reference-id`, `--definition-file-path`, `--activity-id` (UIA), `--target-property`, `--from-snapshot`, `--mode recover`, `--mode improve`
- **Artifact filenames:** `Target_Definition.json`, `WindowDefinition.json`, `ApplicationLevelNodeTreeInfo.json`, etc.
- **Bash blocks invoking `uip rpa uia <subcommand>`**

Non-UIA `uip rpa` commands (`focus-activity`, `add-test-data-queue`, `run-file`, `get-errors`, `get-default-activity-xaml`, `install-or-update-packages`, etc.) are generic and acceptable — they're stable across UIA versions.

## Correct pattern — category pointers

Describe capability at the category level and route to UIA docs for concrete syntax:

- "the internal `uip rpa uia` CLIs that `uia-configure-target` uses" — not an enumerated subcommand list
- "the OR CLI" — not `object-repository get-screens` / `get-elements`
- "the indication commands" — not `indicate-application` / `indicate-element`
- "recover mode" — not `--mode recover`
- "the target definition file" — not `Target_Definition.json`
- Path pointers: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/<path>`

## Example

**Incorrect** (couples skill to UIA CLI details):

> Run `uip rpa uia object-repository get-screens` to list screens, then `link-screen --reference-id <id> --activity-id NApplicationCard_1`.

**Correct** (points at UIA docs for concrete syntax):

> Query existing screens via the OR CLI, then attach the screen per `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md`.

## Where to put new content

| New content | Home |
|-------------|------|
| CLI subcommand syntax, flag tables, troubleshooting | UIA package: `docs/references/cli-reference.md` |
| CLI workflow recipe | UIA package: `docs/references/<workflow>.md` |
| Skill invocation guide for callers | UIA package: `docs/skills/<skill>/USAGE.md` |
| Skill internal procedure | UIA package: `docs/skills/<skill>/SKILL.md` |
| Policy, decision logic, orchestration, critical rules | `skills/uipath-rpa/references/` with pointer to UIA docs for concrete syntax |

New UIA docs go into the UIA package's source repo under `UiPath.UIAutomation.Activities.Package/docs/`. When the package is installed in a project, these docs land at `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/`.

## Rationale

`UiPath.UIAutomation.Activities` ships its own skill docs, CLI reference, and workflow guides — all co-versioned with the package. Duplication in `skills/uipath-rpa/` causes drift: when UIA evolves, stale duplicates mislead agents into invoking commands that no longer exist or using wrong flag names. Route agents to the co-versioned docs instead.

## No Meta-Commentary

Do NOT write sentences that describe the document's own editorial behavior, reconcile differences between documents, or announce why a structure exists. Prose must carry information the reader needs — not commentary about the prose itself.

Patterns to cut:

- "The rest of this guide presumes X"
- "For brevity, we do not repeat Y here"
- "This section exists because Z"
- "The other doc lists this as conditional because ..."
- "Note that we use X terminology instead of Y"

**Incorrect** (explains a cross-document discrepancy instead of stating what to pass):

> Every `Write-<N>` task: `A, B, C, D, E`. In the pipeline every write task has activities to insert, so the last two are always populated here — the agent's contract lists them as conditional because it also supports a scaffold-only mode the pipeline does not use.

**Correct** (states only what is passed):

> Every `Write-<N>` task: `A, B, C, D, E`.

If two documents disagree, fix one of them — do not explain the disagreement in prose.
