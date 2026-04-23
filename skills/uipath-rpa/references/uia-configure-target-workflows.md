# Configure Target Workflows

**Always use the `uia-configure-target` skill** to create or find targets in the Object Repository. This skill handles the full flow: capturing the application, discovering elements, generating selectors, improving them, and registering them in the OR.

## Execution Model

**Execute `uia-configure-target` steps inline in the main conversation.** Do NOT delegate the entire skill to a subagent. The skill's internal steps already spawn their own subagents.

Why this matters:
- **OR references** must be visible in the main conversation so they can be attached to workflow activities as the workflow is created — either inline (for single-file workflows) or handed off to write agents (for multi-screen pipelines). See `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md`.
- **Context continuity** — as the main conversation proceeds, it already knows which screens and elements are registered: the references were returned in earlier turns, and the OR itself is queryable via the OR CLI. This is what "knowing what's registered" means here — the in-conversation state plus live OR queries — so duplicate captures are avoided and the workflow build stays coherent.

Read the SKILL.md, then execute each step of the internal procedure yourself. Only spawn `Agent` where the skill explicitly says to.

## Invocation

The `uia-configure-target` skill lives at `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-configure-target/` — read `SKILL.md` for the internal procedure and `USAGE.md` for invocation modes (TargetAnchorable, TargetApp, and the batch `|` pattern for multiple elements on the same screen). These are **reference docs to read and follow** — they are NOT invocable as slash commands via the Skill tool.

## Rules

**Do NOT manually call the internal `uip rpa uia` CLIs** that `uia-configure-target` uses to build selectors. These are internal tools used *by* the skill — calling them directly skips selector improvement and OR registration, producing fragile selectors that aren't registered in the Object Repository. The skill's SKILL.md defines the proper flow; anything outside that flow is out of bounds.

**Do NOT launch the target application before running `uia-configure-target`.** The skill's first steps capture the top-level window tree and search for the app. Only if the app is not found in the window list should you launch it — and then re-run the capture. Launching preemptively creates duplicate instances and risks targeting the wrong window.

## Indication Fallback

> **Use indication when elements appear only after user interaction** (e.g., a compose form that opens after clicking a button), so `uia-configure-target`'s automated capture cannot see them. Indication requires the user to physically click on the target.

Workflow steps, response shape, downstream OR regeneration for coded vs XAML, and pointers to the full CLI flag reference: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/indication-fallback-workflow.md`.

## Interacting with a Registered Target

See [uia-multi-step-flows.md](uia-multi-step-flows.md) for when to use `uia interact` vs servo and the full capture loop.

## Attaching Targets to Workflow Activities

Once targets are registered in the OR (via `uia-configure-target` or indication fallback), attach them to XAML activities per `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md`.

### Multi-Screen Workflows

For XAML workflows spanning multiple screens, use the parallel authoring pipeline. The main conversation passes only OR reference IDs to each write agent — no XAML snippets. The agent handles attachment itself per the shared guide.

See [uia-parallel-xaml-authoring-guide.md](uia-parallel-xaml-authoring-guide.md) for prompt templates and the chained dependency model.
