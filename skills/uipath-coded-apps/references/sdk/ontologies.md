# Ontologies Reference

## Imports

```typescript
import { Ontologies, ArtifactType } from '@uipath/uipath-typescript/ontologies';
```

## Anti-shapes & gotchas (read first)

1. **`type` is required on first upsert — silently inferred on updates.** On the very first `upsertArtifact` call for a `fileName`, the server cannot infer the artifact type and returns 400 if `type` is omitted. On subsequent calls (the file already exists), `type` is inferred from the stored artifact — you may omit it. Always pass `type` on first upload to be safe.

2. **Single-file types allow exactly one file per ontology.** `schema`, `mapping`, `summary`, and `context` are single-file: uploading a second file of the same type replaces the first via `upsertArtifact`. Multi-file types (`constraints`, `business-rules`) allow many files. Do not assume an ontology has only one artifact — call `listArtifacts()` to inspect what's there.

3. **`validateArtifact` always returns HTTP 200 — never rely on exit code or thrown error.** The server signals validation failure through `result.valid === false` and `result.violations`. A valid artifact with no issues also returns 200 with `valid: true` and an empty `violations` array. Always read `result.valid`.

4. **`uploadArtifacts` is additive — unlisted files are untouched.** Only the files in the `items` array are created or replaced. Files already stored on the ontology that are not in `items` remain unchanged. To remove a file, call `deleteArtifact` separately.

5. **`uploadArtifacts` throws 409 if a `fileName` already exists under a different `type`.** You cannot reclassify an artifact in a bulk call. Delete the old file first, then re-upload with the correct type.

6. **`OntologySummary` has bound methods — prefer them over passing IDs manually.** Every object returned from `create`, `getAll`, or `getById` has `listArtifacts`, `upsertArtifact`, `uploadArtifacts`, `getArtifact`, `deleteArtifact`, `validateArtifact`, `update`, `deleteById`, and `exportOntology` bound to its own ID. Calling `onto.listArtifacts()` is safer than `ontologies.listArtifacts(onto.id)` — the ID can't be wrong.

7. **`getAll` returns one page even with no options.** The server applies its own page cap when no `pageSize` is set. `result.items.length` after a bare `getAll()` is NOT the total ontology count. Loop with a cursor to collect all (see [pagination.md](pagination.md)).

8. **Ontology `name` is unique per tenant/folder, max 64 chars, no `/`.** A 409 is thrown on duplicate. The `id` (GUID) never changes even on rename via `update({ name: '...' })`.

9. **`exportOntology` returns `Uint8Array`, not a `Blob` or `File`.** The archive contains every artifact at its `fileName` plus `ontology.json` (metadata manifest). An ontology with no artifacts yields a zip containing only `ontology.json`. Write with `fs.writeFile(path, Buffer.from(bytes))` in Node or create a `Blob` for browser download.

## Types to Import

```typescript
import { ArtifactType, OntologyState, ValidationSeverity } from '@uipath/uipath-typescript/ontologies';
import type {
  OntologySummary,
  RawOntologySummary,
  OntologyMethods,
  OntologyCreateOptions,
  OntologyUpdateOptions,
  OntologyGetAllOptions,
  ArtifactMetadata,
  ArtifactEnvelope,
  ArtifactListOptions,
  ArtifactUpsertRequest,
  ArtifactBulkItem,
  ValidationResult,
  ValidationViolation,
} from '@uipath/uipath-typescript/ontologies';
```

## Enums

```typescript
import { ArtifactType, OntologyState, ValidationSeverity } from '@uipath/uipath-typescript/ontologies';

// ArtifactType — semantic kind of an artifact
ArtifactType.Schema        // 'schema'        — OWL ontology (e.g. .ofn); one per ontology
ArtifactType.Constraints   // 'constraints'   — SHACL shapes (e.g. .ttl); many per ontology
ArtifactType.Mapping       // 'mapping'       — R2RML / JSON mapping; one per ontology
ArtifactType.BusinessRules // 'business-rules'— rule files (e.g. .ttl); many per ontology
ArtifactType.Summary       // 'summary'       — plain-text summary; one per ontology
ArtifactType.Context       // 'context'       — JSON context; one per ontology

// OntologyState — lifecycle state returned on every OntologySummary
OntologyState.Draft     // 'DRAFT'    — newly created or after artifact changes; not deployed
OntologyState.Deployed  // 'DEPLOYED' — validated and deployed for use
OntologyState.Broken    // 'BROKEN'   — was deployed but a later artifact change invalidated it

// ValidationSeverity
ValidationSeverity.Error   // 'ERROR'
ValidationSeverity.Warning // 'WARNING'
```

## Ontologies Service

### OntologySummary fields

Every `OntologySummary` includes: `id`, `name`, `displayName`, `description?`, `state` (`OntologyState`), `createdBy`, `createTime`, `updatedBy?`, `updateTime?` — plus bound artifact methods.

Check `onto.state` to know if an ontology is ready (`Deployed`) or needs attention (`Draft`, `Broken`).

### create(name, options?)

Returns `Promise<OntologySummary>`. Name must be ≤ 64 chars, no `/`, unique per tenant/folder — 409 on duplicate.

Options: `displayName?`, `description?`, `folderKey?` (GUID; omit for tenant-level scope).

### getAll(options?)

Returns `NonPaginatedResponse<OntologySummary>` or `PaginatedResponse<OntologySummary>` when pagination options are passed.

Options: `search?` (name fragment), `folderKey?`, `pageSize?`, `cursor?`, `jumpToPage?`.

> **A bare `getAll()` does NOT return all ontologies.** The server caps results at its own page size when no `pageSize` is passed, wrapped in a misleadingly-named `NonPaginatedResponse`. To list every ontology, loop until `!page.hasNextPage` (see Usage Example).

### getById(idOrName)

Returns `Promise<OntologySummary>`. Accepts GUID or name — GUID is checked first.

### update(idOrName, updates)

Returns `Promise<OntologySummary>`. Only supplied fields change. Use `name` to rename — the GUID stays stable. 409 if the new name is already taken.

Updates: `name?`, `displayName?`, `description?`.

### deleteById(idOrName)

Returns `Promise<void>`. Cascades the delete to all artifacts — irreversible.

### exportOntology(idOrName)

Returns `Promise<Uint8Array>`. Zip archive: every artifact at its stored `fileName` + `ontology.json` manifest. An ontology with no artifacts produces a zip containing only `ontology.json`.

> Write to disk: `await fs.writeFile('out.zip', Buffer.from(await onto.exportOntology()))`.
> Browser download: `const blob = new Blob([bytes], { type: 'application/zip' }); const url = URL.createObjectURL(blob)`.

### listArtifacts(idOrName, options?)

Returns `Promise<ArtifactMetadata[]>`. Metadata only — no `content` field.

Options: `type?: ArtifactType` to filter by kind.

### getArtifact(idOrName, fileName)

Returns `Promise<ArtifactEnvelope>` — `ArtifactMetadata` plus `content: string`.

### upsertArtifact(idOrName, fileName, request)

Returns `Promise<ArtifactMetadata>`. First call inserts; subsequent calls replace content. Content is NOT echoed back.

Request: `{ mediaType, content, type? }`. `type` is required on first insert; inferred from the stored artifact on updates.

> Type resolution order: `request.type` → `?type=` query param → Content-Type inference. If still ambiguous, the server returns 400.

### uploadArtifacts(idOrName, items)

Returns `Promise<ArtifactMetadata[]>` — the full resulting artifact set (no content). Additive: files not in `items` are untouched.

Each item: `{ fileName, type, mediaType, content }`. `type` is required for every item (becomes the multipart part name).

> 409 if a `fileName` already exists on the ontology under a **different** `type`. Delete first, then re-upload.

### deleteArtifact(idOrName, fileName)

Returns `Promise<void>`. Irreversible.

### validateArtifact(idOrName, fileName, request)

Returns `Promise<ValidationResult>`. **Always HTTP 200** — check `result.valid`, never the status code or thrown error.

Request: `{ mediaType, content, type? }`.

`ValidationResult`: `{ valid: boolean, type: ArtifactType, violations: ValidationViolation[] }`.
`ValidationViolation`: `{ severity: ValidationSeverity, message: string, line?: number }`.

## Bound Methods on OntologySummary

Every `OntologySummary` returned from `create`, `getAll`, or `getById` has these methods bound to its own `id` — no need to pass `idOrName` again:

| Bound method | Equivalent service call |
|---|---|
| `onto.update(updates)` | `ontologies.update(onto.id, updates)` |
| `onto.deleteById()` | `ontologies.deleteById(onto.id)` |
| `onto.exportOntology()` | `ontologies.exportOntology(onto.id)` |
| `onto.listArtifacts(options?)` | `ontologies.listArtifacts(onto.id, options)` |
| `onto.getArtifact(fileName)` | `ontologies.getArtifact(onto.id, fileName)` |
| `onto.upsertArtifact(fileName, request)` | `ontologies.upsertArtifact(onto.id, fileName, request)` |
| `onto.uploadArtifacts(items)` | `ontologies.uploadArtifacts(onto.id, items)` |
| `onto.deleteArtifact(fileName)` | `ontologies.deleteArtifact(onto.id, fileName)` |
| `onto.validateArtifact(fileName, request)` | `ontologies.validateArtifact(onto.id, fileName, request)` |

## Usage Example

```typescript
import { useMemo, useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Ontologies, ArtifactType } from '@uipath/uipath-typescript/ontologies';
import type { OntologySummary, ArtifactMetadata, ValidationResult } from '@uipath/uipath-typescript/ontologies';

function OntologyViewer({ ontologyName }: { ontologyName: string }) {
  const { sdk } = useAuth();
  const ontologies = useMemo(() => new Ontologies(sdk), [sdk]);
  const [onto, setOnto] = useState<OntologySummary | null>(null);
  const [artifacts, setArtifacts] = useState<ArtifactMetadata[]>([]);

  useEffect(() => {
    const load = async () => {
      // getById accepts name or GUID
      const o = await ontologies.getById(ontologyName);
      setOnto(o);

      // Use bound method — no need to pass the ID again
      const arts = await o.listArtifacts();
      setArtifacts(arts);
    };
    load();
  }, [ontologies, ontologyName]);

  const handleUpsertSchema = async (content: string) => {
    if (!onto) return;
    // type required on first insert; omit on subsequent updates
    await onto.upsertArtifact('schema.ofn', {
      type: ArtifactType.Schema,
      mediaType: 'text/owl-functional',
      content,
    });
  };

  const handleValidate = async (draft: string): Promise<ValidationResult> => {
    if (!onto) throw new Error('not loaded');
    // Always 200 — read result.valid, never rely on thrown error
    return onto.validateArtifact('schema.ofn', {
      type: ArtifactType.Schema,
      mediaType: 'text/owl-functional',
      content: draft,
    });
  };

  return <div>{artifacts.map(a => <div key={a.fileName}>{a.fileName} ({a.type})</div>)}</div>;
}

// Collect all ontologies across pages
async function getAllOntologies(ontologies: Ontologies): Promise<OntologySummary[]> {
  const all: OntologySummary[] = [];
  let cursor;
  do {
    const page = await ontologies.getAll({ pageSize: 100, cursor });
    all.push(...page.items);
    cursor = page.hasNextPage ? page.nextCursor : undefined;
  } while (cursor);
  return all;
}
```
