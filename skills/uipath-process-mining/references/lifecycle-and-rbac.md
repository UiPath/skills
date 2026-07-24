# Stages (dev vs published) & RBAC

## The two stages

A process app has two stages, selected by `--stage` on data / transformation /
query commands (default `dev`):

- **`dev`** — the development stage. Iterate on the data mapping and the dbt
  transformations here. **Keep it fast by loading a small, representative subset**
  of the data: ingest a sample, get the mapping + `Cases.sql` + your custom models
  and data-model tables right, verify with `query`, then move on. Short feedback
  loops matter — a full re-transform on a large dataset is slow.
- **`published`** — the stage consumers use, carrying the **full dataset**.
  Dashboards and shared analysis read published data.

Typical loop: develop and validate on `--stage dev` with a subset → publish →
run the real analysis / share on `--stage published` with everything.

> **Publishing** promotes the validated dev app (mapping + transformations + data
> model) to the published stage and loads the full data there. Confirm the current
> `uip pm` surface for this (`uip pm apps --help` / `uip pm --help`); if there is
> no publish verb yet, publishing is done from the Process Mining app UI. Either
> way, the mental model above (develop-on-dev-subset, publish-full) holds, and
> `--stage published` targets the published data once it exists.

## RBAC — configured at the platform layer, not in `uip pm`

Access to a process app is **not** granted by `uip pm`. A process app lives in a
**folder**, and who can see / edit / publish it is governed by Orchestrator +
Identity **roles and folder assignments**:

- **Roles & assignments** — create/inspect roles and assign them to users/groups,
  and check effective access, with [`uipath-admin`](/uipath:uipath-admin)
  (Identity Server, Authorization, check-access PDP).
- **Folders** — organize apps and scope access with folders via
  [`uipath-platform`](/uipath:uipath-platform).

Quick guidance:

1. Put the process app in a dedicated folder for the audience that should see it.
2. Assign a **view** role to consumers (they read published dashboards / run
   `query --stage published`) and an **edit/publish** role to the small team that
   maintains the mapping and transformations.
3. Verify with an effective-access / check-access query before sharing.

Keep least privilege: most users need view on published only; editing dev
transformations is a maintainer capability.
