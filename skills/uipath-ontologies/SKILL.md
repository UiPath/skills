---
name: uipath-ontologies
description: "Use when managing existing UiPath Ontologies and their artifacts via the `uip ont` CLI or `Ontologies` from `@uipath/uipath-typescript` in a Coded App. Covers ontology and artifact CRUD, upsert/validate/bulk-upload, file type→ArtifactType mappings, pagination, and common errors. For creating a new ontology from an SDD use uipath-ontology-authoring; from a domain prompt use uipath-ontology-modeler."
when_to_use: "User wants to manage existing ontologies via `uip ont` CLI (list, get, update, delete, export) or manage artifacts (upsert, validate, delete, upload-bulk). Also use for `OntologyService` / `Ontologies` SDK service in Coded Apps, `datafabric_/api/ontology` API errors, or questions about ontology state, artifact types, and CLI command syntax."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
user-invocable: true
---

# UiPath Ontologies

Manage UiPath Ontologies and their artifacts via the `uip ont` CLI or the `Ontologies` SDK service.

---

## Prerequisites

Resolve these before running any ontology commands.

### Login

```bash
# Cloud (default)
uip login

# Alpha environment
uip login --authority https://alpha.uipath.com --organization <org>
# Then set tenant if needed:
uip login tenant set <tenantName>

# Named alpha profile alongside prod
uip login --authority https://alpha.uipath.com --profile alpha
# --profile is a login flag only — uip ont commands don't accept it

# Override base URL for a local backend (UIPATH_URL, not UIPATH_BASE_URL)
UIPATH_URL=http://localhost:5002 uip login --authority http://localhost:5002
UIPATH_URL=http://localhost:5002 uip ont list
```

### Folder

`uip ont list` and `uip ont create` scope to a folder. Resolve it before any other step.
Commands that operate by ID (`get`, `update`, `delete`, `export`, artifact commands) do not need a folder key.

**Step 1 — Check what is already set:**

```bash
echo $UIPATH_FOLDER_KEY
```

**Step 2 — Confirm or replace:**

- **If set** — ask the user in the conversation before proceeding:
  > "Current folder is `<value>`. Continue with this folder, or pick a different one?"
  - Confirm → use it and move on.
  - Different → run Step 3.

- **If not set** — ask the user before doing anything else:
  > "Which UiPath folder should ontologies be scoped to? I can list your available folders."

**Step 3 — Discover available folders (when needed):**

The interactive folder picker in `uip ont` only works in a real terminal — it does not run in Claude Code's tool context. List folders programmatically using the orchestrator tool:

```bash
uip or folders list --output json
```

Present the folder names to the user, ask them to confirm, then export:

```bash
export UIPATH_FOLDER_KEY=<confirmed-key>
```

**Step 4 — Pass the key explicitly:**

Once confirmed, always pass `--folder-key` on `list` and `create`:

```bash
uip ont list --folder-key $UIPATH_FOLDER_KEY
uip ont create <name> --folder-key $UIPATH_FOLDER_KEY
```

---

## Creating an Ontology

Use the right skill based on what you have:

| Starting point | Skill to use |
|---|---|
| An SDD, PDD, or design document | **`uipath-ontology-authoring`** — reads the document, sets up Data Fabric entities, invokes the modeler, and deploys |
| A domain described in a prompt ("I have Orders, Customers, Products…") | **`uipath-ontology-modeler`** — builds the domain model from your description and generates all artifacts |

This skill covers **operations on existing ontologies only**.

---

## Reference

### Command Prefix

`uip ont` — not `uip onto` or `uip ontologies`.

```bash
uip ont --help               # ✅
uip onto --help              # ❌ "unknown command 'onto'"
uip ontologies --help        # ❌ "unknown command 'ontologies'"
```

### Ontology State

Every ontology response includes a `state` field. State is informational — an ontology is available to consume as soon as it is created, regardless of state.

| State | Meaning |
|---|---|
| `DRAFT` | Newly created or artifacts have changed since last state update |
| `DEPLOYED` | Artifacts are consistent and the ontology is in a stable state |
| `BROKEN` | A previously stable ontology has had an artifact change that left it inconsistent |

State transitions are driven automatically by artifact changes — not by any user action.

### Artifact Types

| Type | CLI `--type` | Accepted media-types | File ext | Single file per ontology |
|---|---|---|---|---|
| `ArtifactType.Schema` | `schema` | `text/owl-functional` | `.ofn` | Yes |
| `ArtifactType.Constraints` | `constraints` | `text/turtle` | `.ttl` | No |
| `ArtifactType.Mapping` | `mapping` | `text/turtle`, `application/yaml` | `.ttl` / `.yml` | Yes |
| `ArtifactType.Functions` | `functions` | `text/turtle` | `.ttl` | No |
| `ArtifactType.Actions` | `actions` | `text/turtle` | `.ttl` | No |
| `ArtifactType.BusinessRules` | `business-rules` | `text/markdown`, `application/json` | `.md` / `.json` | No |
| `ArtifactType.Summary` | `summary` | `application/json` | `.json` | Yes |
| `ArtifactType.Context` | `context` | `application/json` | `.json` | Yes |

`--type` is required on first upsert — inferred from the stored artifact on subsequent updates.

**Media type is the dispatch key**, not the file extension. `text/turtle` and `application/json` are ambiguous (multiple types accept them) so `--type` is always required when using those. `text/owl-functional` and `text/markdown` are unambiguous — `--type` is optional for those.

**Mapping format:** use `application/yaml` for YARRRML (requires a `mappings:` root section) or `text/turtle` for R2RML.

> **`mapping` upsert may return HTTP 404.** Check the API response for the specific error — one possible cause is that the referenced Data Fabric entities have not been created yet.

### CLI Commands

```bash
# Ontologies
uip ont list [--search <term>] [--folder-key <key>] [--limit <n>]
uip ont get <idOrName>
uip ont create <name> [--display-name <name>] [--description <text>] [--folder-key <key>]
uip ont update <idOrName> [--name <newName>] [--display-name <name>] [--description <text>]
uip ont delete <idOrName> --yes --reason <reason>
uip ont export <idOrName> --file <path.zip>

# Artifacts
uip ont artifact list <idOrName> [--type <type>]
uip ont artifact get <idOrName> <fileName>
uip ont artifact upsert <idOrName> <fileName> --type <type> --media-type <mime> (--file <path> | --content <text>)
uip ont artifact upload-bulk <idOrName> --file <array.json>
uip ont artifact validate <idOrName> <fileName> --type <type> --media-type <mime> (--file <path> | --content <text>)
uip ont artifact delete <idOrName> <fileName> --yes --reason <reason>
```

`validate` always returns HTTP 200 once reached — check `Data.valid`, not exit code.

`delete` (ontology and artifact) requires both `--yes` and `--reason`. No confirmation prompt.

### Common Errors

| Error message | Cause | Fix |
|---|---|---|
| `"fetch failed"` | Not logged in / no valid token | `uip login` |
| `"Not Found"` | `datafabric_` service not running on target env | Start the Ontologies / Data Fabric service |
| HTTP 404 on `mapping` upsert | Missing Data Fabric entities or other API error | Inspect the response body, ensure all referenced Data Fabric entities exist, then retry |
| `"unknown command 'onto'"` | Wrong prefix | Use `uip ont`, not `uip onto` or `uip ontologies` |

Service URL pattern: `https://<baseUrl>/<org>/<tenant>/datafabric_/api/ontology`

### SDK — `Ontologies` in Coded Apps

For full SDK reference including types, bound methods, and gotchas, see [references/sdk/ontologies.md](../uipath-coded-apps/references/sdk/ontologies.md) in the `uipath-coded-apps` skill.

```typescript
import { Ontologies, ArtifactType } from '@uipath/uipath-typescript/ontologies';
import type { OntologySummary, ArtifactMetadata, ValidationResult } from '@uipath/uipath-typescript/ontologies';

// React component
const ontologies = useMemo(() => new Ontologies(sdk), [sdk]);

// Outside React
const ontologies = new Ontologies(sdk);
```

Do **not** use `sdk.ontologies.*` — dot-chain access is deprecated.

**Key gotchas:**

1. **`uploadArtifacts` is additive** — files not in the `items` array are untouched. Delete separately to remove.
2. **`OntologySummary` has bound methods** — use `onto.listArtifacts()` instead of `ontologies.listArtifacts(onto.id)`.
3. **`getAll` returns one page** — loop with cursor to collect all ontologies.

**Pagination:**

```typescript
const all: OntologySummary[] = [];
let cursor;
do {
  const page = await ontologies.getAll({ pageSize: 100, cursor });
  all.push(...page.items);
  cursor = page.hasNextPage ? page.nextCursor : undefined;
} while (cursor);
```
