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

Every ontology response includes a `state` field. State is informational — an ontology is available to consume as soon as it is created, regardless of state.

| State | Meaning |
|---|---|
| `DRAFT` | Newly created or artifacts have changed since last state update |
| `DEPLOYED` | Artifacts are consistent and the ontology is in a stable state |
| `BROKEN` | A previously stable ontology has had an artifact change that left it inconsistent |

State transitions are driven automatically by artifact changes — not by any user action.

## Artifact Types

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

**Media type is the dispatch key**, not the file extension. Extensions are cosmetic. `text/turtle` and `application/json` are ambiguous (multiple types accept them) so `--type` is required when using those. `text/owl-functional` and `text/markdown` are unambiguous — `--type` is optional for those.

**Mapping format:** use `application/yaml` for YARRRML (recommended, requires a `mappings:` root section) or `text/turtle` for R2RML. The architecture skill uses YARRRML (`{name}-mapping.yarrrml.yml`).

> **`mapping` upsert may return HTTP 404.** If you get HTTP 404 on a `mapping` upsert, check the API response for the specific error — one possible cause is that the referenced Data Fabric entities have not been created yet. Complete Steps 1–2 of the SDD workflow (entity discovery and creation) before retrying.

## Hard Rules

These apply at all times, not just during the SDD workflow:

1. **Never skip Steps 1 and 2.** Data Fabric entities must exist before any ontology artifact referencing them is created. Uploading a mapping artifact for entities that don't exist causes HTTP 404 and leaves the ontology broken.
2. **Never create a duplicate ontology.** Always run `uip ont get <name>` before `uip ont create`. If it exists, show it and ask.
3. **Never upsert a `mapping` artifact before Steps 1–2 are confirmed complete.** The mapping links ontology IRIs to Data Fabric source fields — those fields must exist first.
4. **Surface the checklist explicitly.** Before starting Step 3, show the user a summary of what was found in Step 1 and what was created/skipped in Step 2. Get a clear go-ahead before proceeding.

---

## Workflow: Creating an Ontology from a Source Document (e.g. SDD)

When a user provides a source document (SDD, data model, spec) and asks to create an ontology from it, follow these steps in order. **STOP at each gate — do not advance until the gate condition is met.**

### Step 1 — Discover existing entities in the folder

**GATE: This step must run before any other step. No exceptions.**

Use the Data Fabric skill to list what entities already exist:

```bash
uip df entities list --native-only --output json
```

Extract entity names from the response (`Data[].Name`). Keep this list — you will diff against it in Step 2.

### Step 2 — Diff against SDD objects, surface gaps, and create missing entities

**GATE: Do not proceed to Step 3 until this step is fully resolved.**

Parse the source document to identify all objects/entities it defines. Compare against the list from Step 1:

- **Present** — show the user which entities already exist (no action needed).
- **Missing** — list every entity from the SDD that has no match.

Show this diff to the user as a clear table. For each missing entity, get explicit user approval, then create it using the Data Fabric skill:

```bash
uip df entities create <name> --body '{"fields":[...]}' --output json
```

After creating each entity, confirm it with `uip df entities list` and show the result.

**Do not advance to Step 3 until the user explicitly confirms one of:**
- All missing entities have been created, OR
- The user has deliberately chosen to skip specific entities (record which ones and why).

If the user tries to skip Steps 1–2, explain: *"Steps 1 and 2 are required — the mapping artifact references Data Fabric entity fields. If those entities don't exist, the mapping upsert will fail with HTTP 404 and the ontology state will not transition to DEPLOYED."*

### Step 3 — Verify ontology does not already exist, then create

Check if the ontology already exists by name before creating:

```bash
uip ont get <name>
```

- If it **exists**: show the returned record to the user and ask whether to use it as-is or update it. Do not create a duplicate.
- If it **does not exist**: proceed to create:

```bash
uip ont create <name> [--description <text>]
```

### Step 4 — Generate and upsert artifacts

Analyse the source document to extract entities, relationships, and constraints. Always create these four artifacts for a complete ontology:

| Artifact | Type | Media type | File name pattern |
|---|---|---|---|
| OWL 2 QL schema | `schema` | `text/owl-functional` | `{name}.ofn` |
| SHACL constraints | `constraints` | `text/turtle` | `{name}-constraints.ttl` |
| YARRRML mapping | `mapping` | `application/yaml` | `{name}-mapping.yarrrml.yml` |
| JSON-LD context | `context` | `application/json` | `{name}-context.json` |

**`mapping` vs `context` — never confuse these:**
- `context` (`application/json`) is a JSON-LD vocabulary file. It maps short term names to full IRIs so JSON consumers understand the ontology's vocabulary. It is always JSON.
- `mapping` (`application/yaml`) is a YARRRML (R2RML) file. It maps relational source fields to RDF triples. It must be YAML with a `mappings:` root section and `.yml` extension. This is the R2RML file.

Both must be created. Creating only `context` and skipping `mapping` is incomplete.

**YARRRML structure** (one `mappings:` entry per entity):

```yaml
prefixes:
  base: "https://ontology.uipath.com/{name}#"
  xsd: "http://www.w3.org/2001/XMLSchema#"
  rdf: "http://www.w3.org/1999/02/22-rdf-syntax-ns#"

mappings:
  EntityName:
    sources:
      - [EntityName~csv]
    s: base:EntityName/$(Id)
    po:
      - [a, base:EntityName~iri]
      - [base:fieldName, $(SourceFieldName), xsd:string]
      - [base:relatedEntity, base:OtherEntity/$(ForeignKeyId)~iri]
```

Upsert commands:

```bash
uip ont artifact upsert <name> <name>.ofn --type schema --media-type text/owl-functional --file <path>
uip ont artifact upsert <name> <name>-constraints.ttl --type constraints --media-type text/turtle --file <path>
uip ont artifact upsert <name> <name>-mapping.yarrrml.yml --type mapping --media-type application/yaml --file <path>
uip ont artifact upsert <name> <name>-context.json --type context --media-type application/json --file <path>
```

After each upsert, validate:

```bash
uip ont artifact validate <name> <file> --type <type> --media-type <mime> --file <path>
```

### Step 5 — Confirm with the user

List the uploaded artifacts and report back:

```bash
uip ont artifact list <name>
```

---

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
uip ont artifact list <idOrName> [--type <type>]
uip ont artifact get <idOrName> <fileName>
uip ont artifact upsert <idOrName> <fileName> --type schema --media-type text/owl-functional [--file <path> | --content <text>]
uip ont artifact upload-bulk <idOrName> --file <array.json>
uip ont artifact validate <idOrName> <fileName> --type <type> --media-type <mime> (--file <path> | --content <text>)
uip ont artifact delete <idOrName> <fileName> --yes --reason <reason>
```

`validate` requires artifact content — pass either `--file <path>` or `--content <text>` (both are accepted; neither is optional). The server always returns HTTP 200 once reached — check `Data.valid`, not exit code.

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
| HTTP 404 on `mapping` upsert | Unknown — check the API error response for details; one possible cause is missing Data Fabric entities | Inspect the response body, then create any missing entities (Step 2) and retry |
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
2. **`validateArtifact` requires content** — pass `content` (string) or `file` path; omitting it causes a client-side error before the server is reached. Once the server is reached it always returns HTTP 200 — read `result.valid`, never rely on thrown error or exit code.
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
