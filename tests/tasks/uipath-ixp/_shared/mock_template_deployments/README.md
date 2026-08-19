# uipath-ixp deployment-serving mock

Overlay for smoke tasks whose correct path **starts with a read**. Overlays the
base [`mock_template`](../mock_template/README.md) — list it SECOND so its
`mocks/uip` wins:

```yaml
sandbox:
  mock_path_dirs: [mocks]
  template_sources:
    - {type: template_dir, path: ../_shared/mock_template}
    - {type: template_dir, path: ../_shared/mock_template_deployments}
```

## Why it exists

`deployments upgrade` addresses a deployment by `DeploymentName` — a
backend-minted slug that **cannot be derived from the title**
(`invoices` → `invoices-08963f00-ixp`, and the suffix is generated per
deployment, matching neither the project name's suffix nor the folder key).

On the base mock, which fails every invocation, `deployments list` returns
nothing, so there is no name to carry into the graded write. An agent that
declines to invent the slug **correctly stops** — and would be graded as a fail.
Serving the read makes the graded shape reachable, and lets criteria assert the
carried-over *name* rather than mere flag presence.

## Fixture

Project `my_invoices-f1afa9ef-ixp`, folder `3f0a91c7-1111-2222-3333-444455556666`:

| DeploymentTitle | DeploymentName | ModelVersion |
|-----------------|----------------|--------------|
| `invoices`      | `invoices-08963f00-ixp` | 13 |

Two folders exist, so a task can exercise key-only addressing:

| FullyQualifiedName | Key | Hosts a deployment |
|--------------------|-----|--------------------|
| `Finance/Invoices` | `3f0a91c7-1111-2222-3333-444455556666` | yes, `invoices` on v13 |
| `Finance/Archive`  | `8c22d4e1-9999-8888-7777-666655554444` | no |

Versions 13 and 14 are both deployable in `projects list-models`, so moving to
14 is legitimate — the task is not accidentally testing the
`404 [ModelVersionNotFoundError]` path. `DeployedAt` carries the service's
`+00:00` offset, not `…Z`.

Served: `projects list`, `projects list-models`, `deployments list`,
`deployments upgrade`, `deployments create`, and `or folders list` — the
documented source of folder keys, so a task may name a folder and require the
agent to resolve it. Everything else falls through to the base mock's offline
failure, so a task can still guard against unwanted verbs.

## deployments list is stateful

`upgrade` echoes the **requested** version without re-reading, so only `list`
proves the move landed — and the skill tells the agent to make that call. An
agent that does so must see its own write, not stale v13 it would then try to
re-apply:

| After | `ModelVersion` | `DeployedAt` |
|-------|----------------|--------------|
| — | 13 | `2026-08-18T11:26:25.367124+00:00` |
| `deployments upgrade` | 14 | moved |

State lives in a dot-prefixed marker file beside `calls.log`, so it stays out of
graded globs and CI artifact uploads.

## Only the real name resolves

`upgrade` addressed by the **title** answers `404 [DeploymentNotFoundError]`,
as the service does — so a task can grade the name/title distinction on
behavior instead of trusting the log alone.

`upgrade` to a version outside `list_models` (13, 14) answers
`404 [ModelVersionNotFoundError]`, and the version is checked **before** the
deployment is resolved, as the service does — so the stale-version path is a
distinct error from an unknown name, and `upgrade` is provably not a rollback
path.

`create` is **folder-aware**, because the folder is part of the deployment
identity: into `Finance/Invoices` it answers the real
`409 [DeploymentAlreadyExistsError]` carrying the CLI's conflict hint, while the
same title deploys cleanly into `Finance/Archive` and returns a *different*
slug (`invoices-5d41402b-ixp`) — the suffix is minted per deployment. Serving
the faithful conflict rather than the generic offline failure is what lets a
task trap repointing-by-create, the mis-model the command split exists to
prevent. Note the `409` and both `404`s all surface `Code: invalid_argument` —
`400`/`409`/`422` map alike — which is why the skill tells callers to branch on
`Context.HttpStatus`.

## Grading: `cli_called` over the JSONL sink

Tasks grade with `cli_called`, pointed at this overlay's structured sink:

```yaml
- type: cli_called
  log: "mocks/calls.jsonl"
  verb: "ixp deployments upgrade"
  positional: ["my_invoices-f1afa9ef-ixp", "invoices-08963f00-ixp"]
  flags:
    version: "14"
```

`log:` is required here — it defaults to `cli_mocks/calls.jsonl`, where
`sandbox.record_cli` writes, and this overlay is not a generated recorder.

This mock is **Python, not sh**, for the reason the base mock is: `cli_called`
reads `argv` as a LIST, and sh cannot emit correct JSON without hand-rolled
escaping. Both sinks are written, in the base mock's exact formats — `calls.log`
flat for any legacy regex criterion, `calls.jsonl` structured for `cli_called`.

Matching per-facet rather than over a rendered string is what lets a task assert
the name/title distinction directly: `positional: [project, "invoices"]` on a
`max_count: 0` guard catches the title in the deployment slot, and does **not**
match `invoices-08963f00-ixp`. Guards that do not declare `--version` /
`--folder-key` under `flags` should list them in `value_flags`, so a flag value
cannot leak into the positional list and let argument ordering dodge the guard.

## Why not `sandbox.record_cli`

`record_cli` replaces a hand-written mock only when every response is static.
`RecordedCli.stdout` is one string per tool, while this overlay is a
**dispatcher**: `deployments list` is stateful, `create` is folder-aware, and
`upgrade` validates the version before the name. Those per-invocation responses
are the whole reason the read-before-write path is gradeable, so this stays a
hand-written mock. A task that only needs "every call fails offline" should use
`record_cli` instead and skip this overlay entirely — `smoke/deploy_to_folder.yaml`
does.

## Constraints

Logging matches the base mock exactly — same `uip ` prefix, same newline
normalization, same JSONL record schema — so criteria written against either
sink keep matching. Change one and change both. `mocks/uip` must stay mode
`755`, and must stay valid under the `python3` the smoke image provides.
