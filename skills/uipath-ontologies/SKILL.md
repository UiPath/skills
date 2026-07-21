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

When you read the SDD, tell the user you are **analysing the SDD** — do not mention step numbers or internal workflow stages to the user. Step labels (Step 0, Step 1, …) are for your own navigation only.

### Step 0 — Gather intent before starting

**GATE: Confirm name, display name, description, and functions files before running any commands.**

Collect the following from the user or infer from the SDD:

**1. Machine name**
- If the user provides a name explicitly → use it as-is. Validate: lowercase, hyphens and alphanumeric only, ≤ 64 chars, no `/`.
- If not provided → derive from the SDD title: lowercase, replace any non-`[a-z0-9]` character with `-`, collapse consecutive hyphens, strip leading/trailing hyphens, truncate to 64 chars.
- Show the proposed name in backticks and wait for confirmation before proceeding.

**2. Display name**
- Propose the SDD title as-is (or convert the machine name: replace `-` with spaces, title-case each word).
- Confirm with the user.

**3. Description**
- Propose a one-sentence summary from the SDD purpose/abstract section.
- The confirmed description is **not just metadata** — use it to drive artifact generation. A description like _"Tracks invoice and claim processing for construction AP"_ implies classes like `Invoice`, `Claim`, `LineItem` and their properties. Always derive schema classes, SHACL constraints, YARRRML mappings, and JSON-LD context from the description and SDD together.
- Confirm or ask the user to supply one.

**4. Functions files (optional)**
- Ask: "Does this ontology include SPARQL or OWL function definitions? If yes, how many files and what names?"
- Record confirmed file names (e.g. `validation-functions.ttl`, `scoring-functions.ttl`). If none, skip `functions` in Step 4.

**Step 0 completion gate — show the full plan and wait for a clear yes before moving on:**

```
Plan confirmed:
  name:         construction-phase1
  display name: Construction Phase 1
  description:  Tracks invoice and claim processing for Meriton AP.

  Artifacts to create:
    1. construction-phase1.ofn                 (schema,      text/owl-functional)
    2. construction-phase1-constraints.ttl      (constraints, text/turtle)
    3. construction-phase1-mapping.yarrrml.yml  (mapping,     application/yaml)
    4. construction-phase1-context.json         (context,     application/json)
    5. validation-functions.ttl                 (functions,   text/turtle)  ← if confirmed

Ready to start? (yes / no)
```

**Send this plan to the user and stop. Do not run any commands, do not proceed to Step 1, and do not narrate what comes next. Wait for the user's explicit reply (yes / no) in a separate message. The user's earlier "let's go" or similar reply to your Step 0 proposals does NOT count — they must see and approve the full plan block first.**

### Step 1 — Discover existing entities in the folder

> **Step 1/5 — Discovering existing Data Fabric entities...**

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

> **Step 2/5 — `<N>` entities already exist, `<M>` missing. [Creating missing entities... / All present.]**

**Do not advance to Step 3 until the user explicitly confirms one of:**
- All missing entities have been created, OR
- The user has deliberately chosen to skip specific entities (record which ones and why).

If the user tries to skip Steps 1–2, explain: *"Steps 1 and 2 are required — the mapping artifact references Data Fabric entity fields. If those entities don't exist, the mapping upsert will fail with HTTP 404 and the ontology state will not transition to DEPLOYED."*

### Step 3 — Verify ontology does not already exist, then create

> **Step 3/5 — Checking for existing ontology, then creating...**

Before running any commands, show a pre-flight summary using the confirmed values from Step 0:

```
Pre-flight summary
──────────────────
name:         construction-phase1
display name: Construction Phase 1
description:  Tracks invoice and claim processing for Meriton AP.
Entities:     3 already existed, 2 created in Step 2
Artifacts:    5 planned (schema, constraints, mapping, context, 1× functions)

Proceed? (yes / no)
```

Wait for explicit approval, then check if the ontology already exists:

```bash
uip ont get <name>
```

- If it **exists**: show the returned record to the user and ask whether to use it as-is or update it. Do not create a duplicate.
- If it **does not exist**: create it with the confirmed name, display name, and description:

```bash
uip ont create <name> --display-name "<displayName>" --description "<description>"
```

`--display-name` is required here — always include it.

### Step 4 — Generate and upsert artifacts

Analyse the source document and the confirmed description to generate artifact content. Always create these artifacts for a complete ontology:

| Artifact | Type | Media type | File name pattern | Multi-file |
|---|---|---|---|---|
| OWL 2 QL schema | `schema` | `text/owl-functional` | `{name}.ofn` | No |
| SHACL constraints | `constraints` | `text/turtle` | `{name}-constraints.ttl` | No |
| YARRRML mapping | `mapping` | `application/yaml` | `{name}-mapping.yarrrml.yml` | No |
| JSON-LD context | `context` | `application/json` | `{name}-context.json` | No |
| SPARQL/OWL functions | `functions` | `text/turtle` | user-confirmed name (e.g. `{name}-validation-functions.ttl`) | **Yes** |

**`mapping` vs `context` — never confuse these:**
- `context` (`application/json`) is a JSON-LD vocabulary file. It maps short term names to full IRIs so JSON consumers understand the ontology's vocabulary. It is always JSON.
- `mapping` (`application/yaml`) is a YARRRML (R2RML) file. It maps relational source fields to RDF triples. It must be YAML with a `mappings:` root section and `.yml` extension. This is the R2RML file.

Both must be created. Creating only `context` and skipping `mapping` is incomplete.

**`functions` files** — multiple `.ttl` files are allowed. The user confirmed names in Step 0. Upsert each:
```bash
uip ont artifact upsert <name> <file.ttl> --type functions --media-type text/turtle --file <path>
```
Count each functions file separately in the artifact progress counter.

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

**Validate-then-upsert for each artifact:**

For each artifact (`i` of `total`):

> **Step 4/5 — Upserting artifacts (`<i>` of `<total>`: `<type>` — `<fileName>`)...**

1. Validate first:
   ```bash
   uip ont artifact validate <name> <file> --type <type> --media-type <mime> --file <path>
   ```
2. **The server always returns HTTP 200 for validate — check `Data.valid`, not the exit code.**
3. If `Data.valid === true` → upsert, then emit: `` `<fileName>` — validated OK, upserted ✓ ``
   ```bash
   uip ont artifact upsert <name> <file> --type <type> --media-type <mime> --file <path>
   ```
4. If `Data.valid === false` → **do NOT upsert**. Format `Data.violations` as a numbered list:
   ```
   Validation failed for construction-phase1-constraints.ttl (2 violations):
     1. [ERROR] line 14: unrecognized XSD type 'xsd:dateTimeStamp'
     2. [WARNING] line 22: sh:minCount 0 is the default — can be omitted

   Fix and retry, or skip?  (fix / skip)
   ```
   - **fix** → revise the artifact content, re-validate, re-upsert. Loop until valid or user chooses to skip.
   - **skip** → record as `skipped (invalid)`. Note: skipping `mapping` will leave ontology state at `DRAFT`.

### Step 5 — Final summary

> **Step 5/5 — Done. Here is what was created:**

Run `uip ont get <name>` and `uip ont artifact list <name>`, then format as a table:

| Artifact | Type | Size | Status |
|---|---|---|---|
| `{name}.ofn` | schema | 3.2 KB | valid |
| `{name}-constraints.ttl` | constraints | 820 B | valid |
| `{name}-mapping.yarrrml.yml` | mapping | 1.4 KB | valid |
| `{name}-context.json` | context | 2.1 KB | valid |
| `validation-functions.ttl` | functions | 650 B | valid |

Then report the ontology state:

```
Ontology state: DEPLOYED
```

If the state is not `DEPLOYED`, explain:
- `DRAFT` — mapping artifact is missing or not yet accepted. Re-run Step 4 for the `mapping` artifact.
- `BROKEN` — a required artifact was removed or skipped. Re-run Step 4 for the missing artifact.

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
