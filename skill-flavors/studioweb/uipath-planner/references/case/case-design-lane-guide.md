<!--skill-flavor:build-handoff-row:start-->
| Build handoff (`uipath-maestro-case` asked for a build, no `sdd.md`) | `sdd.md` at the working root — NEVER overwrite an existing one; abort and surface it | Do NOT stop. The Build answer already carried consent: the build's phases start immediately in this conversation (Phase 1 directly — the open Studio Web solution already exists and project creation happens at Step 6.0 — verifying the resolved identities instead of re-discovering them) |
<!--skill-flavor:build-handoff-row:end-->
<!--skill-flavor:task-types-stop-remedy:start-->
tell the user the Studio Web CLI in this session does not declare the case task types. It ships with Studio Web, so there is nothing for them to install; ask them to reload Studio Web and ask again.
<!--skill-flavor:task-types-stop-remedy:end-->
