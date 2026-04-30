# Author — Create and edit `.flow` files

Capability index for building new flows (greenfield) and editing existing flows (brownfield). Author owns everything that happens on disk, locally, without `uip login`. Authoring journeys terminate at `validate` + `tidy`; from there, hand off to [OPERATE.md](OPERATE.md) to publish, run, or debug.

> **Phase 1a scaffold** — this index is a placeholder. Subsequent phases populate the sections below by extracting content from SKILL.md and moving existing reference files into [author/](author/).

## When to use this capability

- Create a new Flow project with `uip maestro flow init`
- Edit a `.flow` file — adding nodes, edges, or logic
- Explore available node types via the registry
- Validate a Flow file locally
- Manage variables, subflows, expressions, and output wiring
- Choose between Direct JSON and CLI editing strategies
- Configure connector, connector-trigger, or inline-agent nodes
- Plan a complex flow before building

## Critical rules

> Populated in Phase 2 with the 16 author-scoped rules extracted from SKILL.md (rules 1, 2, 3, 5, 6, 7, 8, 10, 11, 12, 13, 16, 17, 18, 21).

## Workflow

> Populated in Phase 2. Planned journey docs (links activate when files land):
>
> - Create a new flow from scratch → `author/greenfield.md`
> - Edit an existing flow → `author/brownfield.md`

## Common tasks

> Populated in Phase 2 (extracted from SKILL.md Common Edits + Task Navigation tables).

## Anti-patterns

> Populated in Phase 2 with the author-scoped subset of today's SKILL.md anti-patterns.

## References

> Populated in Phase 2 as files move into [author/](author/):
>
> - `author/greenfield.md` — create-new-flow journey
> - `author/brownfield.md` — edit-existing-flow journey
> - `author/editing-operations.md` — strategy selection
> - `author/editing-operations-json.md` — Direct JSON recipes (default)
> - `author/editing-operations-cli.md` — CLI carve-outs
> - `author/planning-arch.md` — capability discovery, plugin index, topology design
> - `author/planning-impl.md` — registry lookups, connection binding, wiring rules
> - `author/plugins/` — per-node-type planning + impl docs
>
> Cross-capability references in [shared/](shared/):
>
> - `shared/file-format.md` — `.flow` JSON schema
> - `shared/commands.md` — flat CLI lookup
> - `shared/cli-conventions.md` — CLI mechanics every capability needs
> - `shared/variables-and-expressions.md` — variable system + `=js:` Jint expressions
> - `shared/node-output-wiring.md` — canonical `=js:$vars.X.output.Y` rule
