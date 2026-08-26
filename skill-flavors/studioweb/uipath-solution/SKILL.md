<!--skill-flavor:solution-lifecycle-host:start-->
**In Studio Web the lifecycle is different — there is no `pack` step, and coded apps are created through the platform, not `uip codedapp init`.**

```
1. Create projects   → Use the CreateProjects tool / New Project UI (NOT `uip codedapp init`)
2. resources refresh → Sync bundled artefacts with cloud state (if needed)
3. publish           → `uip solution publish` (bare — packaging is handled by Studio Web)
4. deploy run        → Promote to Orchestrator (auto-activates by default)
```

> **Do NOT run `uip solution pack`.** It is excluded from the Studio Web browser bundle (the packager is Node-only) — calling it fails with "command not available." Packaging is not a step you invoke here.

> **Publish with a bare `uip solution publish`** (no package argument, no prior pack). In Studio Web this is routed to Studio Web's own publish flow, which packages the solution client-side from a server-side snapshot. The desktop `pack → publish` sequence does not apply. If the CLI publish does not complete, use Studio Web's **Publish** button in the toolbar / the **Manage → Deploy** wizard, which does the same thing through the UI. Publish is asynchronous — packaging continues after the request is accepted; do not treat "submitted" as "shipped."

> **Coded apps (AppV2) must be created through Studio Web's project creation** (the CreateProjects tool or New Project → Coded App), which generates the coded-app solution resource. Do **not** use `uip codedapp init` inside a solution here: its resource generation is Node-only and stubbed out of the browser bundle, so the project would register as AppV2 with **no app resource**, Studio Web would classify it as a `process`, and it would never publish as a coded app (the CLI now fails this loudly with `INIT_ARTIFACTS_UNAVAILABLE`). A coded app needs a non-confidential OAuth external application before deploy — create one with `uip admin external-apps create … --non-confidential` and pass it to `uip codedapp deploy --client-id`, or select it in the Deploy wizard's External application field.
<!--skill-flavor:solution-lifecycle-host:end-->
