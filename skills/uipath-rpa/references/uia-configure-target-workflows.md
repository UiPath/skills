# Configure Target Workflows

**Always use the `uia-configure-target` skill** to create or find targets in the Object Repository. This skill handles the full flow: capturing the application, discovering elements, generating selectors, improving them, and registering them in the OR.

> **Working directory:** run every `uip rpa uia` CLI call from the project directory — the folder containing `project.json`.

## Execution Model

**Execute `uia-configure-target` steps inline in the main conversation.** Do NOT delegate the entire skill to a subagent. The skill's internal steps already spawn their own subagents.

Why this matters:
- **OR references** must be visible in the main conversation so they can be attached to workflow activities as the workflow is created. See `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md`.
- **Context continuity** — as the main conversation proceeds, it already knows which screens and elements are registered: the references were returned in earlier turns, and the OR itself is queryable via the OR CLI. This is what "knowing what's registered" means here — the in-conversation state plus live OR queries — so duplicate captures are avoided and the workflow build stays coherent.

Read the SKILL.md, then execute each step of the internal procedure yourself. Only spawn `Agent` where the skill explicitly says to.

## Invocation

The `uia-configure-target` skill lives at `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-configure-target/` — read `SKILL.md` for the internal procedure and `USAGE.md` for invocation modes (TargetAnchorable, TargetApp, and the batch `|` pattern for multiple elements on the same screen). These are **reference docs to read and follow** — they are NOT invocable as slash commands via the Skill tool.

Before invoking, check the unsupported-activities list in `USAGE.md`. If the activity you need to target is on that list, skip `uia-configure-target` for it and use the [Indication Fallback](#indication-fallback) instead.

## Rules

**Do NOT manually call the internal `uip rpa uia` CLIs** that `uia-configure-target` uses to build selectors. These are internal tools used *by* the skill — calling them directly skips selector improvement and OR registration, producing fragile selectors that aren't registered in the Object Repository. The skill's SKILL.md defines the proper flow; anything outside that flow is out of bounds.

## Multi-Step UI Flows

Some UI elements only become visible after interacting with earlier elements (e.g., a compose form appears after clicking "New mail", a confirmation dialog appears after submitting). Since `uia-configure-target` works from the current screen state, you need to **advance the application to each state** before capturing its elements.

> **CRITICAL: Complete-then-advance.** Finish ALL `uia-configure-target` calls for elements visible in the current screen state — including OR registration (the full skill flow) — before advancing to the next state. Interactions change the app state irreversibly. If you advance before registering, elements from the previous state may no longer be visible, causing OR registration to fail.
>
> **Do NOT use the `uip rpa uia interact` CLI to "test" element interactions** (e.g., verifying autocomplete behavior, checking what happens when you click a button) during the capture phase. Testing happens later, when running the completed workflow. During capture, these commands are ONLY for advancing the app to the next screen so you can capture the newly revealed elements.

### Advancing UI State

After registering an element in the Object Repository, interact with it (or a sibling element) to reveal the next screen via the `uip rpa uia interact` CLI. See the skill at `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-interact/SKILL.md`.

**Reuse refs from the current `uia-configure-target` capture — do not re-inspect.** The `uip rpa uia interact` CLI resolves element refs against the most recent snapshot in memory regardless of which CLI wrote it (the two write to different folders, but the snapshot is shared). Pass the same e-refs (`e28`, `e35`, etc.) directly to `uip rpa uia interact click`/`type`/`select`. Running `uip rpa uia snapshot inspect` just to re-mint refs for an unchanged UI is wasted work — the refs you have are still live.

Re-inspect (or re-run `uip rpa uia snapshot capture`) only when the UI has actually advanced since the last capture; refs from a pre-advance snapshot will not resolve against the new state. Full flag reference: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`.

### Capture Loop

1. **Capture current state completely:** Run `uia-configure-target` for ALL elements visible on the current screen. Let the skill run through to OR registration for each element. Do not stop after getting a raw selector.
2. **Advance the UI** to the next state via the `uip rpa uia interact` CLI.
3. **Capture the new state:** Run `uia-configure-target` again for elements now visible on the new screen (full skill flow).
4. **Repeat** until all workflow targets are registered in the OR.

**Do NOT use `uip rpa run-file` with partial workflows to advance UI state** — the workflow lifecycle may close the target application when execution ends. The `uip rpa uia interact` CLI is stateless: it performs one action and leaves the app in the resulting state.

## Indication Fallback

> **Use indication when elements appear only after user interaction** (e.g., a compose form that opens after clicking a button), so `uia-configure-target`'s automated capture cannot see them. Indication requires the user to physically click on the target.

Workflow steps, response shape, downstream OR regeneration for coded vs XAML, and pointers to the full CLI flag reference: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/indication-fallback-workflow.md`.

## Attaching Targets to Workflow Activities

Once targets are registered in the OR (via `uia-configure-target` or indication fallback), attach them to XAML activities per `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md`.

### Multi-Screen Workflows

For XAML workflows spanning multiple capture screens, add each screen's activities to the workflow as its OR references become available. Each batch aligns with the Complete-then-advance rule in § Multi-Step UI Flows — everything configured before the next `uip rpa uia interact` advance belongs to one batch. Validate with `get-errors` after each batch. Attach each target per `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md`.

## CLI Pitfalls

Runtime symptoms that have wasted entire capture sessions. Canonical flag list, accepted values, and artifact filenames for every UIA subcommand: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`.

- **Filter mode of the UIA snapshot CLI fails with a missing-argument error.** It requires a target definition file argument in addition to the folder argument.
- **Selector resolution rejects bare element refs (`Invalid --refs entry`).** Each ref must be paired with the definition file that owns it.
- **OR element-creation rejects inline JSON.** The OR CLI consumes pre-written per-element definition files only. Generate the definition files first, then invoke create-elements with their paths.
- **UIA interact actions reject discovery and global flags (`unknown option`).** Interact subcommands accept only interaction-shape flags. Folder, ref, and project-dir style flags belong to other UIA subcommand families.
