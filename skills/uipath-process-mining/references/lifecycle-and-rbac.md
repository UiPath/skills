# Stages (dev vs published) & RBAC

## The two stages

A process app has two stages, selected by `--stage` on data / transformation /
query commands (default `dev`):

- **`dev`** — the development stage. Iterate on the data mapping and the dbt
  transformations here. **Keep it fast by loading a small, representative subset**
  of the data: ingest a sample, get the mapping + `Cases.sql` + your custom models
  and data-model tables right, verify with `query`, then move on. Short feedback
  loops matter — a full re-transform on a large dataset is slow.
- **`published`** — the stage consumers use through the **dashboards / shared UI**,
  carrying the **full dataset**. `apps publish` promotes the definition here.

Typical loop: develop and validate on `--stage dev` with a subset → publish → let
consumers read the **dashboards** on the published data.

> **CLI caveat:** `uip pm query --stage published` is currently **not reachable** —
> `/query/{id}/published` needs a completed ingestion on that stage and no `uip pm`
> path produces one (`apps publish` answers `IngestionNeeded: true`, but a following
> `ingestions create --wait` still leaves published querying at
> `UserError_InvalidOrNoIngestion`; verified against a live tenant). So publishing
> promotes the app to the **dashboards**, but **CLI-driven `query` stays on `dev`**.

## Publishing

**`uip pm apps publish <app-id>`** promotes the validated dev app (mapping +
transformations + data model) to the published stage, so dashboards and the query
layer see it.

The command reads the app's current model version off the data-model ETag and
sends it as the publish precondition, so a stale caller fails instead of
clobbering a newer model. The result envelope carries:

- **`Changes`** — what the publish moved.
- **`IngestionNeeded`** — when `true`, the published stage still needs a
  re-ingestion before the change reaches the **data**. Dev transformation *or*
  data-model changes (including `apps data-model add-table`) only become queryable
  after a re-ingest; publishing alone promotes the definition, not the rows.

So the full promote loop is: validate on `dev` → `uip pm apps publish <app>` →
`uip pm ingestions create <app> --wait` when `IngestionNeeded` → analyse on
`--stage published`.

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
