# SDK Reference Protocol

The installed package is the authoritative reference for the `@uipath/uipath-typescript` SDK. This folder's files contain ONLY knowledge the package cannot carry; everything else is read from `node_modules`.

## Where to look things up

| Need | Source (inside `node_modules/@uipath/uipath-typescript/`) |
|---|---|
| Which subpaths exist | `ls dist/` — every directory is an import subpath: `@uipath/uipath-typescript/<dir>` |
| Which subpath exports a class | `grep -l "class <Name>" dist/*/index.d.ts` |
| Method signatures, params, return types, usage examples | `dist/<subpath>/index.d.ts` — full JSDoc, matches the installed version exactly (call only members NOT tagged `@internal` — see rule 5) |
| Per-method OAuth scopes | `docs/oauth-scopes.md` (shipped with newer SDK versions; fallback: [../oauth-scopes.md](../oauth-scopes.md) § Per-method scope lookup) |
| Types, enums, option interfaces | same `dist/<subpath>/index.d.ts` as their service class — use `import type` for type-only imports |
| Version a capability was introduced in (when it is **absent** from the installed types) | `release-metadata.json` — see *When a capability is missing from the installed types* below |

Rules:

1. Before calling a service you have not used in this session, Read its `dist/<subpath>/index.d.ts`.
2. If `node_modules` is absent, run the install step first (the app cannot build without it — see the scaffold workflow).
3. NEVER guess or recall method names, signatures, or scopes from memory — SDK versions differ; the installed package is the contract.
4. Task-level scope **bundles** and widget scopes: [../oauth-scopes.md](../oauth-scopes.md). Cross-service traps and server-side behavior the types cannot express: the per-domain files in this folder.
5. **Call only methods that are NOT tagged `@internal`.** The shipped `.d.ts` includes members whose JSDoc carries an `@internal` tag — these are not a supported API and may change or disappear without notice. Ignore them when picking a method. This restricts *calling* `@internal` **methods**; referencing an `@internal` **type** that a public method's signature already exposes is unavoidable and fine.
6. If a capability you expect is **absent** from the installed `.d.ts`, do not conclude it is impossible or invent it — resolve the required SDK version via *When a capability is missing from the installed types* below.

## When a capability is missing from the installed types

A subpath, service class, method, or enum member you need is not in the installed `.d.ts`. It may require a newer SDK. Resolve the version to upgrade to from **`release-metadata.json`** — a map the SDK ships of public capabilities → the version each was introduced in:

- Installed copy: `node_modules/@uipath/uipath-typescript/release-metadata.json` (matches the installed version).
- Latest copy: `https://unpkg.com/@uipath/uipath-typescript@latest/release-metadata.json` (needed to see capabilities newer than what is installed).

Find the service by `name` in the `services` array (its methods in that service's `methods` array; enum members in the matching `enums[].values`). A method with no entry **inherits its service's `since`**. Then:

1. **Present in the installed `.d.ts`** → use it (you are not in this flow).
2. **Absent locally, in the latest metadata with `since` = `V`** → tell the user: *"`<capability>` requires `@uipath/uipath-typescript` ≥ `V`; installed is `<version>` — upgrade to use it."*
3. **`since: null`** → baseline (shipped in every tracked version); absence locally means the install predates tracking or is corrupt — advise reinstall / upgrade to latest.
4. **Absent from the latest metadata entirely** → the capability does not exist in the SDK. Do not fabricate it; route to the correct skill or tell the user it is unavailable.
5. **Cannot fetch the latest copy (offline / no network)** → read the installed `release-metadata.json`; if it also lacks the capability, tell the user it is not in their installed SDK and may need a newer version — point them to the changelog or `npm view @uipath/uipath-typescript`.

Name the exact `since` when metadata has it; never silently build a lesser version or guess a number.

## Version history (frozen)

<!-- FROZEN: historical "requires SDK >= x.y.z" minimums, snapshot at the release-metadata.json cutover. Do NOT add NEW version gates here — from now on a capability's introduction version lives ONLY in the SDK's release-metadata.json (resolved via the fallback above). This table is a frozen convenience for pre-cutover minimums; release-metadata.json is authoritative. -->

Pre-cutover minimums (authoritative source: `release-metadata.json`):

| Capability | Min SDK |
|---|---|
| `agents`, `agent-memory`, `traces`, `governance` subpaths (Insights RTM) | 1.4.1 |
| Agents Insights aggregates — `getSummary`, `getTopErrorCount`, `getTopConsumption`, `getIncidentDistribution`, `getUnitConsumptionSummary` | 1.5.0 |
| AgentTraces governance — `getGovernanceDecisions`, `getGovernanceSummary` | 1.5.1 |
| `EntityFieldDataType.MULTILINE_MAX` | 1.5.2 |
| Maestro analytics on `MaestroProcesses` / `Cases` — `getTop*`, `getInstanceStatusTimeline`, `getElementStats`, `getInstanceStats`, `getIncidentsTimeline` | 1.3.9 to 1.5.1 by method — see `release-metadata.json` |
| `Notifications` service | 1.5.1 |

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

### Never call methods tagged `@internal`

The SDK does not strip `@internal` from its published types, so `@internal` methods are visible in `dist/<subpath>/index.d.ts` right alongside the public ones. They are internal plumbing — unsupported, undocumented, and subject to change without a version bump. A method being *readable* in the `.d.ts` does not make it callable API.

```typescript
// A method whose JSDoc carries an @internal tag:
/**
 * ...
 * @internal
 */
someInternalMethod(...)

// ❌ Wrong — it is in the types, but @internal means "not for you"
await service.someInternalMethod(...);

// ✓ Correct — use the public method that does the job
await service.getAll(...);
```

Referencing an `@internal` **type** in a signature you cannot avoid (e.g. a public method returns one) is fine — the rule is about not **calling** `@internal` **methods**.
