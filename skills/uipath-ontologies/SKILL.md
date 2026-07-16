---
name: uipath-ontologies
description: "Use when managing UiPath Ontologies and their artifacts via the `uip ont` CLI or `Ontologies` from `@uipath/uipath-typescript` in a Coded App. Covers ontology CRUD, artifact upsert/validate/bulk-upload, file type→ArtifactType mappings (.ofn, .ttl), pagination, and common errors (datafabric service not running, wrong command prefix `ont` not `onto` or `ontologies`)."
when_to_use: "User mentions ontologies / `uip ont` / OntologyService / Ontologies service / `@uipath/uipath-typescript/ontologies` / `schema.ofn` / `.ttl` artifact / ontology artifacts / 'upsert schema' / 'validate artifact' / 'export ontology' / 'list ontologies' / `datafabric_/api/ontology`."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
user-invocable: true
---

# UiPath Ontologies

Manage UiPath Ontologies and their artifacts via the `uip ont` CLI or the `Ontologies` SDK service.

## Critical: Command Prefix Is `ont`, Not `onto` or `ontologies`

```bash
uip ont --help               # ✅
uip onto --help              # ❌ "unknown command 'onto'"
uip ontologies --help        # ❌ "unknown command 'ontologies'"
```

## Ontology State

Every ontology response includes a `state` field:

| State | Meaning |
|---|---|
| `DRAFT` | Newly created or after artifact changes — not yet validated/deployed |
| `DEPLOYED` | Validated and deployed for use |
| `BROKEN` | Previously deployed but a subsequent artifact change invalidated it |

## Artifact Types

| Type | CLI `--type` | Typical media-type | File ext | One per ontology |
|---|---|---|---|---|
| `ArtifactType.Schema` | `schema` | `text/owl-functional` | `.ofn` | Yes |
| `ArtifactType.Constraints` | `constraints` | `text/turtle` | `.ttl` | No |
| `ArtifactType.Mapping` | `mapping` | `application/json` | `.json` | Yes |
| `ArtifactType.BusinessRules` | `business-rules` | `text/turtle` | `.ttl` | No |
| `ArtifactType.Summary` | `summary` | `text/plain` | `.txt` | Yes |
| `ArtifactType.Context` | `context` | `application/json` | `.json` | Yes |

`--type` is required on first upsert — inferred from the stored artifact on subsequent updates.

## CLI — `uip ont`

### Ontologies

```bash
uip ont list [--search <term>] [--folder-key <key>] [--limit <n>]
uip ont get <idOrName>
uip ont create <name> [--display-name <name>] [--description <text>] [--folder-key <key>]
uip ont update <idOrName> [--name <newName>] [--display-name <name>] [--description <text>]
uip ont delete <idOrName> --yes --reason <reason>
uip ont export <idOrName> --file <path.zip>
```

### Artifacts

```bash
uip ont artifacts list <idOrName> [--type <type>]
uip ont artifacts get <idOrName> <fileName>
uip ont artifacts upsert <idOrName> <fileName> --type schema --media-type text/owl-functional [--file <path> | --content <text>]
uip ont artifacts upload-bulk <idOrName> --file <array.json>
uip ont artifacts validate <idOrName> <fileName> --type <type> --media-type <mime> [--file <path> | --content <text>]
uip ont artifacts delete <idOrName> <fileName> --yes --reason <reason>
```

`validate` always returns HTTP 200 — check `Data.valid`, not exit code.

`delete` (ontology and artifact) requires both `--yes` and `--reason`. No confirmation prompt.

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
uip ont list --profile alpha

# Override base URL for local backend (UIPATH_URL, not UIPATH_BASE_URL)
UIPATH_URL=http://localhost:5002 uip login --authority http://localhost:5002
UIPATH_URL=http://localhost:5002 uip ont list
```

## Common Errors

| Error message | Cause | Fix |
|---|---|---|
| `"fetch failed"` | Not logged in / no valid token | `uip login` |
| `"Not Found"` | `datafabric_` service not running on target env | Start the Ontologies / Data Fabric service |
| `"unknown command 'onto'"` | Wrong prefix | Use `uip ont`, not `uip onto` or `uip ontologies` |

Service URL pattern: `https://<baseUrl>/<org>/<tenant>/datafabric_/api/ontology`

## SDK — `Ontologies` in Coded Apps

For full SDK reference including types, bound methods, and gotchas, see [references/sdk/ontologies.md](../uipath-coded-apps/references/sdk/ontologies.md) in the `uipath-coded-apps` skill.

### Import

```typescript
import { Ontologies, ArtifactType } from '@uipath/uipath-typescript/ontologies';
import type { OntologySummary, ArtifactMetadata, ValidationResult } from '@uipath/uipath-typescript/ontologies';
```

### Instantiation

```typescript
// React component
const ontologies = useMemo(() => new Ontologies(sdk), [sdk]);

// Outside React
const ontologies = new Ontologies(sdk);
```

Do **not** use `sdk.ontologies.*` — dot-chain access is deprecated.

### Key Gotchas

1. **`type` required on first upsert** — server returns 400 if omitted on a new file; inferred on updates.
2. **`validateArtifact` always returns HTTP 200** — read `result.valid`, never rely on thrown error or exit code.
3. **`uploadArtifacts` is additive** — files not in the `items` array are untouched. Delete separately to remove.
4. **`OntologySummary` has bound methods** — use `onto.listArtifacts()` instead of `ontologies.listArtifacts(onto.id)`.
5. **`getAll` returns one page** — loop with cursor to collect all ontologies.

### Pagination

```typescript
const all: OntologySummary[] = [];
let cursor;
do {
  const page = await ontologies.getAll({ pageSize: 100, cursor });
  all.push(...page.items);
  cursor = page.hasNextPage ? page.nextCursor : undefined;
} while (cursor);
```
