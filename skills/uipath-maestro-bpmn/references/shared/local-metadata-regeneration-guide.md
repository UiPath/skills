# Local Metadata Regeneration

Use this guide when BPMN source changed and local package metadata must be refreshed or verified: after binding a connection, or before packaging, upload, debug, publish, or deploy.

**Do NOT apply it to an Integration Service draft or boundary handoff.** When the user asked for a local BPMN draft that hands connector enrichment to the CLI (a request that only says to validate is not one), `entry-points.json`, `bindings_v2.json`, `operate.json`, and `package-descriptor.json` stay CLI-owned — do not hand-author or pre-generate them. Author only the `.bpmn` source shape plus a `.md` notes file **inside the project directory** naming the CLI-owned blockers. The regeneration workflow below reaches such a project only once its connectors are enriched.

The BPMN `refresh` command is the authoritative local source-to-derived-state
boundary. It requires exactly one project-root `.bpmn` file
and atomically regenerates the complete package metadata set. The command is
offline and provider-neutral: it does not log in, discover a tenant, invoke a
connector, or resolve an account. It consumes only identities already authored
into the supported BPMN contract.

Read the part covering your step:

- [local-metadata-regeneration-workflow.md](local-metadata-regeneration-workflow.md) — ownership, the local project contract, regeneration inputs, the safe local `refresh` workflow, the source-only fallback when the CLI is unavailable
- [local-metadata-regeneration-rules.md](local-metadata-regeneration-rules.md) — entry-point, binding, and Integration Service enrichment rules, drift handling
