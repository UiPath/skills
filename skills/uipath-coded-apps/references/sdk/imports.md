# SDK Reference Protocol

The installed package is the authoritative reference for the `@uipath/uipath-typescript` SDK. This folder's files contain ONLY knowledge the package cannot carry; everything else is read from `node_modules`.

## Where to look things up

| Need | Source (inside `node_modules/@uipath/uipath-typescript/`) |
|---|---|
| Which subpaths exist | `ls dist/` — every directory is an import subpath: `@uipath/uipath-typescript/<dir>` |
| Which subpath exports a class | `grep -l "class <Name>" dist/*/index.d.ts` |
| Method signatures, params, return types, usage examples | `dist/<subpath>/index.d.ts` — full JSDoc, matches the installed version exactly |
| Per-method OAuth scopes | `docs/oauth-scopes.md` (shipped with newer SDK versions; fallback: [../oauth-scopes.md](../oauth-scopes.md) § Per-method scope lookup) |
| Types, enums, option interfaces | same `dist/<subpath>/index.d.ts` as their service class — use `import type` for type-only imports |

Rules:

1. Before calling a service you have not used in this session, Read its `dist/<subpath>/index.d.ts`.
2. If `node_modules` is absent, run the install step first (the app cannot build without it — see the scaffold workflow).
3. NEVER guess or recall method names, signatures, or scopes from memory — SDK versions differ; the installed package is the contract.
4. Task-level scope **bundles**, version gates, org-admin notes, and widget scopes: [../oauth-scopes.md](../oauth-scopes.md). Cross-service traps and server-side behavior the types cannot express: the per-domain files in this folder.

## Anti-patterns

### Never import service classes from the package root

Service classes are only available via subpath imports. Root-level imports fail at build time.

```typescript
// ❌ Wrong — service classes are not exported from the root
import { Entities } from '@uipath/uipath-typescript';

// ✓ Correct — use the subpath
import { Entities } from '@uipath/uipath-typescript/entities';
```

### Never use the deprecated dot-chain access pattern

The `sdk.entities.getAll()` style is deprecated. Use constructor dependency injection instead.

```typescript
// ❌ Wrong — dot-chain is deprecated
const items = await sdk.entities.getAll();

// ✓ Correct — constructor DI
const entities = new Entities(sdk);
const items = await entities.getAll();
```
