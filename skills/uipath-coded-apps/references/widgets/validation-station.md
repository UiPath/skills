# Validation Station Widget

React wrapper around the UiPath Document Understanding **Validation Station** web component. Use when the app must let a human review and correct extraction results from a DU document.

Package: [`@uipath/ui-widgets-validation-station`](https://www.npmjs.com/package/@uipath/ui-widgets-validation-station). Full prop/API surface lives in the package README — this file covers only the integration steps that are easy to get wrong inside a Coded App.

## When to Use

- User asks to **validate, review, correct, or approve** Document Understanding extraction results.
- App receives a `ContentValidationData` payload (bucket paths + document ID) — either from an Action Center task created by a DU workflow, or fetched at runtime in a web app.
- Replaces a hand-rolled PDF viewer + field editor. Do **not** rebuild this UI from scratch — the widget already handles PDF rendering, bounding boxes, table editing, translations, and save/discard plumbing.

**Two integration shapes.** The all-in-one `ValidationStation` component (standard layout, fastest — most apps want this) covers the sections below. When you need a **custom layout** — rearrange, hide, or embed individual panels (viewer, fields form, table editor, doc-type field, business rules) — the package also exports those as composable **subcomponents**. See [Compose-your-own layout: subcomponents](#compose-your-own-layout-subcomponents).

If the user just wants a generic form (no DU document), use the standard Action App form pattern in [../create-action-app.md](../create-action-app.md) instead.

## Critical Rules

1. **Peer versions are hard requirements.** Widget requires `react >= 19.2.0`, `react-dom >= 19.2.0`, `@uipath/uipath-typescript >= 1.4.2`. The Vite scaffold pins React 19.2+, but verify in `package.json` before installing.
2. **Call `configureValidationStationWc({ includeFonts: true })` once at startup**, before rendering anything from the package. The widget is a separately loaded bundle, not an import: without this call no custom element is registered and every component renders **nothing** — no error, no empty state. `includeFonts` pulls in `fonts.css`, the bundle's only source of `@font-face`; omit it and the icons render blank.
3. **Stage that bundle at `<app base>/du-vs-wc`** — where the loader looks for it by default. See "Static Assets" below.
4. **Body needs `light` or `dark` class** for theming. Match it to the `theme` prop. Action apps already manage this via `onInitTheme` from `CodedActionAppService.getTask()`.
5. **Reuse the app's own `UiPath` instance** — from `useAuth()` (web app) or `src/uipath.ts` (action app). Do not construct a second SDK for the widget; auth state will diverge.
6. **Required SDK scopes:** `OR.Buckets` (the widget fetches the document and extraction artifacts from a storage bucket). Add `OR.Tasks` as well when the widget is rendered inside an Action Center task (action app, or web app that completes a task on save). Add to the `scope` field in `uipath.json` before first run; mismatch fails silently with 401/403. See [../oauth-scopes.md](../oauth-scopes.md).
7. **Widget does NOT surface failures.** `onSubmit` / `onSaveAsDraft` receive `(request, result?)` and render no toast on failure — the host owns all UI feedback. **`result` is optional**: it is only populated when the widget owned the write-back (i.e. it was given `sdk` + `data`). A missing `result` means nothing was persisted, so treat it as a failure — never complete a task on it, or you close the task over unsaved edits.
8. **Report-as-exception makes no API call.** `onReportException(request)` only hands the host the data — it does NOT persist. Read the reason off `request.exceptionReport` (typed `unknown`, carrying the `IReportAsExceptionDTO` shape) and call `OrchestratorDuModule.submitExceptionReport(taskId, request.documentId, reason, { folderId })` yourself, or the user's click is a no-op. Needs `OR.Tasks`.

## Install

From inside the scaffolded app directory:

```bash
npm install @uipath/ui-widgets-validation-station@1.1.0 --save-exact --@uipath:registry=https://registry.npmjs.org
```

Registry flag forces the public npm registry (skill default — users may have `@uipath` scoped to GitHub Packages).

Pinned exactly on purpose: this package has changed its API in a minor before (1.0.1 → 1.1.0), so a `^` range is not safe. This file documents the 1.1 API.

## Static Assets — staging the web component

The widget is a thin React wrapper; the UI itself is a prebuilt Angular bundle shipped in
`@uipath/du-validation-station-wc`, which `configureValidationStationWc()` loads **at runtime** from
`<app base>/du-vs-wc`. Stage it into `public/`, not through an import: Vite passes `public/` through
untouched in dev and copies it to `dist/` on build, which is what a prebuilt bundle needs.

Add `scripts/stage-du-wc.mjs`:

```javascript
#!/usr/bin/env node
import { access, cp, readFile, rm, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const appRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');

const manifest = require.resolve('@uipath/du-validation-station-wc/package.json');
const wcRoot = dirname(manifest);
const destination = resolve(appRoot, 'public/du-vs-wc');
// Records the staged version so a repeat `npm run dev` doesn't re-copy tens of megabytes.
const stamp = resolve(destination, '.version');

// npm packaging metadata and the bundle's own index shell. None of it is served.
const NOT_DEPLOYED = new Set([
  'package.json', 'README.md', 'CHANGELOG.md', 'LICENSE', 'types.d.ts', 'index.html',
]);

// Entry points and the assets they pull in. A partial copy is invisible until the app 404s.
const REQUIRED = ['main.js', 'polyfills.js', 'styles.css', 'fonts.css', 'du-assets'];

const { version } = JSON.parse(await readFile(manifest, 'utf8'));

if ((await readFile(stamp, 'utf8').catch(() => null)) === version) {
  console.log(`du-vs-wc ${version} already staged in public/du-vs-wc.`);
  process.exit(0);
}

// Full replace, not merge: a version bump renames the hashed chunks.
await rm(destination, { recursive: true, force: true });
await cp(wcRoot, destination, {
  recursive: true,
  filter: (src) => !NOT_DEPLOYED.has(relative(wcRoot, src)),
});

const missing = [];
for (const entry of REQUIRED) {
  await access(resolve(destination, entry)).catch(() => missing.push(entry));
}
if (missing.length > 0) {
  throw new Error(`du-vs-wc staged incompletely - missing ${missing.join(', ')}.`);
}

// Written last, so an interrupted copy leaves no stamp and the next run retries.
await writeFile(stamp, version);
console.log(`Staged du-vs-wc ${version} -> public/du-vs-wc.`);
```

Wire it to run automatically, and gitignore the staged copy:

```jsonc
// package.json
"scripts": {
  "stage-du-wc": "node scripts/stage-du-wc.mjs",
  "predev": "npm run stage-du-wc",
  "dev": "vite",
  "prebuild": "npm run stage-du-wc",
  "build": "npm run typecheck && vite build"
}
```

```gitignore
public/du-vs-wc
```

- **Declare `@uipath/du-validation-station-wc` as a devDependency.** The script resolves it directly;
  relying on it being hoisted out of the widget package breaks the day it isn't.
- **Exclude `public/du-vs-wc` from eslint** (`globalIgnores`) — the bundle ships `.ts` sources under
  `du-assets/` that are not yours to lint.

`vite.config.ts` needs no widget-specific code:

```typescript
import react from '@vitejs/plugin-react';
import { uipathCodedApps } from '@uipath/coded-apps-dev/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react(), uipathCodedApps()],
  base: './',
  optimizeDeps: { include: ['@uipath/uipath-typescript'] },
});
```

**Verify (a green build isn't enough):**
- **Build:** `dist/du-vs-wc/` contains `main.js`, `polyfills.js`, `styles.css`, `fonts.css`, `du-assets/`.
- **Dev:** run the app — the widget renders, and icons are glyphs rather than the words `warning` / `error` / `circle`.

> **Size.** The staged bundle is ~75 MB, most of it fonts under `media/`. Do not trim them — an app in
> an iframe inherits no `@font-face` rules from the page around it, so the icons go blank.

## Key Props

Full table in the package README. Inside a coded app you usually only touch:

| Prop | Required | Notes |
|------|----------|-------|
| `sdk` | Yes* | `UiPath` instance — from `useAuth()` or `src/uipath.ts`. *Required only in self-fetching mode (`sdk` + `data`); omit when passing pre-fetched `artifacts`. |
| `data` | Yes* | `ContentValidationData` — for action apps, from the task payload. **It must name the folder** (`FolderId` or `FolderKey`): there is no `folderId` prop, so merge the task's folder in when the payload arrives without one. |
| `artifacts` | No | Pre-fetched artifacts from `useDuDocumentArtifacts`. When supplied, no fetch happens and `sdk`/`data` are not needed. |
| `theme` | No | `'light' \| 'dark' \| 'light-hc' \| 'dark-hc'`. Keep in sync with body class. |
| `language` | No | `ValidationStationLanguage` enum exported from the package (e.g. `English`, `German`, `Japanese`, `ChineseSimplified`). |
| `isReadonly` | No | `true` to render in read-only mode (e.g., audit view). |
| `options` | No | `IValidationStationOptions` — fine-grained WC feature flags. Set `emitDtoStateChanges: true` to enable save-as-draft. |
| `save` | No | Controlled trigger from a button. `{ validate: true }` = **submit** (validate, then save). `{ validate: false }` = **save as draft** (requires `options.emitDtoStateChanges: true`, else no-op). |
| `discardChanges` | No | Controlled trigger: `{ value: true }` to discard pending edits. Pass a fresh object each time — the widget watches for the new reference, so repeated `{ value: true }` calls all fire. |
| `onSubmit` | No | Fires after **submit** (`save={{ validate: true }}`): ProcessExtractedData + bucket upload. `(request, result?)` — `result` only when the widget owned the write-back. Complete the task here. |
| `onSaveAsDraft` | No | Fires after **save as draft** (`save={{ validate: false }}`): uploads in-progress data, no ProcessExtractedData. Same `(request, result?)` shape. |
| `onReportException` | No | Fires when the user reports an exception. Receives `(request)` — the reason is on `request.exceptionReport`, the document id on `request.documentId`. Widget makes **no API call**; persist via `OrchestratorDuModule.submitExceptionReport(...)`. |

The widget surfaces three flows. **Submit** and **save as draft** are owned end-to-end by the widget and hand the host `(request, result?)`; `result` is a `SaveValidatedDataResult` — `{ success: true }` or `{ success: false, error: string }` — and is present only when the widget did the write-back itself. **Report as exception** is forwarded as a request object with no API call. The widget renders no failure UI for any flow — handle it in the callback yourself (toast, retry, log).

## Integration: Action App (most common)

Validation Station as the form inside an Action Center DU validation task. Replaces `src/components/Form.tsx` from the standard action-app scaffold.

```typescript
// src/components/Form.tsx
import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  ValidationStation,
  ValidationStationLanguage,
  type IVsSaveExceptionReportRequest,
  type IVsSaveValidatedDataRequest,
  type SaveValidatedDataResult,
} from '@uipath/ui-widgets-validation-station';
import type { DuFramework } from '@uipath/uipath-typescript/document-understanding';
import { OrchestratorDuModule } from '@uipath/uipath-typescript/orchestrator-du-module';
import { MessageSeverity, Theme } from '@uipath/coded-action-app';
import { sdk, codedActionAppService } from '../uipath';

const isDarkTheme = (t: Theme) =>
  t === Theme.Dark || t === Theme.DarkHighContrast;

interface FormProps {
  onInitTheme: (isDark: boolean) => void;
}

function Form({ onInitTheme }: FormProps) {
  // Keep the bag: contentValidationData has to go back to completeTask untouched.
  const [taskData, setTaskData] = useState<{
    contentValidationData?: DuFramework.ContentValidationData | null;
  } | null>(null);
  const [taskId, setTaskId] = useState<number | undefined>(undefined);
  const [folderId, setFolderId] = useState<number | undefined>(undefined);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [isReadonly, setIsReadonly] = useState(false);
  const [save, setSave] = useState<{ validate: boolean } | undefined>(undefined);

  useEffect(() => {
    codedActionAppService.getTask().then((task) => {
      // task.data is typed `unknown`; it is the inputs bag from action-schema.json.
      setTaskData(task.data as { contentValidationData?: DuFramework.ContentValidationData });
      setTaskId(task.taskId);
      setFolderId(task.folderId);
      setIsReadonly(task.isReadOnly);
      const dark = isDarkTheme(task.theme);
      setTheme(dark ? 'dark' : 'light');
      onInitTheme(dark);
    });
  }, [onInitTheme]);

  // The widget scopes its bucket calls to the folder named on the payload, so fill the task's
  // folder in when the payload arrived without one.
  const data = useMemo(() => {
    const payload = taskData?.contentValidationData;
    if (!payload) return null;
    if (payload.FolderId != null || payload.FolderKey != null) return payload;
    return folderId == null ? payload : { ...payload, FolderId: folderId };
  }, [taskData, folderId]);

  // The widget shows no error toast, so handle failure here. `result` is absent unless the widget
  // owned the write-back — treat that as a failure rather than completing over unsaved edits.
  const handleSubmit = useCallback(
    async (_request: IVsSaveValidatedDataRequest, result?: SaveValidatedDataResult) => {
      if (!result?.success) {
        codedActionAppService.showMessage(
          result?.error ?? 'Failed to submit the document.',
          MessageSeverity.Error,
        );
        return;
      }
      // completeTask REPLACES the task's data. contentValidationData must go back exactly as
      // getTask() gave it; any other field can carry what the reviewer changed.
      await codedActionAppService.completeTask('Submit', taskData);
    },
    [taskData],
  );

  // Report-as-exception is not persisted by the widget — the host calls the SDK itself.
  const handleReportException = useCallback(
    async (request: IVsSaveExceptionReportRequest) => {
      if (taskId === undefined) return;
      // `exceptionReport` is typed `unknown`; it carries the IReportAsExceptionDTO shape.
      const { Reason } = (request.exceptionReport ?? {}) as { Reason?: string };
      const response = await new OrchestratorDuModule(sdk).submitExceptionReport(
        taskId,
        request.documentId,
        Reason || 'Reported via Validation Station',
        { folderId },
      );
      if (!response.IsSuccessful) {
        codedActionAppService.showMessage(
          response.ErrorMessage ?? 'Failed to report exception',
          MessageSeverity.Error,
        );
        return;
      }
      // Do NOT complete the task for submitExceptionReport.
      codedActionAppService.showMessage('Exception reported.', MessageSeverity.Success);
    },
    [taskId, folderId],
  );

  if (!data) return null; // wait for task payload

  return (
    <>
      <button type="button" onClick={() => setSave({ validate: true })} disabled={isReadonly}>
        Validate &amp; submit
      </button>
      <ValidationStation
        sdk={sdk}
        data={data}
        theme={theme}
        language={ValidationStationLanguage.English}
        isReadonly={isReadonly}
        save={save}
        onSubmit={handleSubmit}
        onReportException={handleReportException}
      />
    </>
  );
}

export default Form;
```

Adjust `src/uipath.ts` to export the initialized `sdk` alongside `codedActionAppService`:

```typescript
import { UiPath } from '@uipath/uipath-typescript/core';
import { CodedActionAppService } from '@uipath/coded-action-app';

export const sdk = new UiPath();
export const codedActionAppService = new CodedActionAppService();
```

And register the web component once, at the app's entry point (`src/main.tsx`), before anything
renders:

```typescript
import { configureValidationStationWc } from '@uipath/ui-widgets-validation-station';

// Loads the bundle from `<app base>/du-vs-wc` and registers its custom elements. Fire-and-forget:
// the components wait on it themselves, and this promise is the only place a load failure surfaces.
configureValidationStationWc({ includeFonts: true }).catch((err: unknown) => {
  console.error('Failed to load the Validation Station web component.', err);
});
```

> **No `sdk.initialize()`** (Critical Rule 17). The SDK authenticates silently against the External
> Application's registered redirect URI, so that URI is **not** optional — see
> [../create-action-app.md](../create-action-app.md) for the form it takes.


**The widget's only schema requirement is one `ContentValidationData` input** — the dedicated type
the CLI maps to `UiPath.DocumentProcessing.Contracts.Actions.ContentValidationData`. That field is
the entire contract between the automation and the widget: it reads the document from the bucket
and writes the validated result back itself, so it needs nothing in `outputs`, `inOuts`, or
`outcomes`.

Everything else is up to the action. The widget can sit alongside the host's own controls, so add
whatever outputs, inOuts, and outcomes that action needs. For a widget-only app, default to a
single `Submit` outcome.

```json
{
  "inputs": {
    "type": "object",
    "properties": {
      "contentValidationData": { "type": "ContentValidationData", "required": true }
    }
  },
  "outputs": { "type": "object", "properties": {} },
  "inOuts":  { "type": "object", "properties": {} },
  "outcomes": {
    "type": "object",
    "properties": {
      "Submit": { "type": "string" }
    }
  }
}
```

> **Never model that input as `"type": "object"` with the members inlined** — the members are
> dropped and the field degrades to `System.Object`.

## What the host still owns

**Size it.** The widget renders the bare custom element
`<ui-du-validation-station-standalone-wc-element>`, which is `display: inline` — an auto-height
host collapses the viewer to nothing.

```css
.validation-host { position: relative; flex: 1; min-height: 0; display: flex; }
/* `persistent: true` swaps the tag for its `-persistent-element` sibling, so match both. */
.validation-host > ui-du-validation-station-standalone-wc-element,
.validation-host > ui-du-validation-station-standalone-wc-persistent-element {
  display: block; flex: 1; min-width: 0;
}
```

**Its loading/error states are unstyled `<div>`s** (`Loading...`, `Failed to load document
artifacts: …`) and there is no prop to override them.

**Its theme tokens are sealed in the shadow root** (`:host(.light)`), so `var(--color-background)`
does not resolve in host CSS. To match the widget's surface, use `#ffffff` light / `#182027` dark.

## Integration: Web App

Same widget, sdk comes from `useAuth()`. Typical flow: list `TaskType.DocumentValidation` tasks with `tasks.getAll(...)`, **then hydrate the selected row with `tasks.getById(...)` to load `task.data`** — `getAll()` returns task summaries without `data` populated, so passing a `getAll` row straight into the widget produces an empty viewer.

```typescript
import { useEffect, useMemo, useState } from 'react';
import {
  ValidationStation,
  ValidationStationLanguage,
  type IVsSaveValidatedDataRequest,
  type SaveValidatedDataResult,
} from '@uipath/ui-widgets-validation-station';
import type { DuFramework } from '@uipath/uipath-typescript/document-understanding';
import { Tasks, TaskType } from '@uipath/uipath-typescript/tasks';
import type { TaskGetResponse } from '@uipath/uipath-typescript/tasks';
import { useAuth } from '../hooks/useAuth';

function ValidatePage({ taskId, folderId }: { taskId: number; folderId: number }) {
  const { sdk } = useAuth();
  const tasks = useMemo(() => new Tasks(sdk), [sdk]);
  const [selectedTask, setSelectedTask] = useState<TaskGetResponse | null>(null);

  // getAll() rows don't carry `data` — fetch the full task by id.
  useEffect(() => {
    tasks.getById(taskId, { taskType: TaskType.DocumentValidation }, folderId).then(setSelectedTask);
  }, [tasks, taskId, folderId]);

  const handleSubmit = async (
    _request: IVsSaveValidatedDataRequest,
    result?: SaveValidatedDataResult,
  ) => {
    // No result means nothing was persisted — widget renders no error UI, surface it yourself.
    if (!result?.success || !selectedTask) return;
    await selectedTask.complete({
      action: 'Completed',
      type: TaskType.DocumentValidation,
    });
  };

  if (!selectedTask) return null;

  return (
    <ValidationStation
      sdk={sdk}
      // The payload must name the folder; for a task, its own folder is the one.
      data={{ ...(selectedTask.data as DuFramework.ContentValidationData), FolderId: selectedTask.folderId }}
      theme="light"
      language={ValidationStationLanguage.English}
      onSubmit={handleSubmit}
    />
  );
}

export default ValidatePage;
```

Two things to lock in:

- **Always call `tasks.getById(id, { taskType: TaskType.DocumentValidation }, folderId)` before rendering the widget.** Even if you already have a `TaskGetResponse` from `getAll()`, its `data` field is undefined. Re-fetch by id.
- **DU validation tasks are `TaskType.DocumentValidation`** — do not pass `TaskType.Form`, `App`, or `External`. The action string for a successful validation is `"Completed"`. Prefer the task-attached `selectedTask.complete(...)` over the service-level `tasks.complete(...)` — no `taskId`/`folderId` to thread through. See [../sdk/action-center.md](../sdk/action-center.md) for the broader Tasks API.

Body theme class — toggle on the document body (e.g., from `useAuth` user preferences or a theme switcher):

```typescript
useEffect(() => {
  document.body.classList.toggle('dark', isDark);
  document.body.classList.toggle('light', !isDark);
}, [isDark]);
```

## Compose-your-own layout: subcomponents

When the standard layout doesn't fit — you need to rearrange panels, hide some, or embed one piece inside your own screen — the package also exports the Validation Station as **five composable subcomponents** plus a data hook, instead of the all-in-one `ValidationStation`. Same document, same bucket artifacts, same save flows; you own the layout.

Exports (from the same `@uipath/ui-widgets-validation-station` package):

| Export | Kind | Role |
|--------|------|------|
| `useDuDocumentArtifacts(sdk, data)` | hook | Fetches the document + extraction artifacts **once**; returns `{ artifacts, error }`. Feed `artifacts` to every subcomponent. Scopes itself to the folder named on `data`. |
| `DocumentViewer` | component | PDF/text viewer with bounding boxes. Read-only. |
| `CompactFieldsForm` | component | Extraction fields, editable. The **only** subcomponent that persists — give it `sdk` + `data` and it runs Submit / Save-draft / Report-exception (same callbacks as the monolithic widget). |
| `CompactTableEditor` | component | Inline editor for table (line-item) fields. Edit-only. |
| `CompactDocTypeField` | component | Document-type selector dropdown. |
| `CompactBusinessRules` | component | Read-only evaluated business rules. |

**How they link — one shared `instanceId`.** Give every subcomponent the same `instanceId` string and they share a single store: selecting a field in the form highlights it in the viewer, selecting a table field opens the table editor, clicking a rule focuses the offending field. No cross-wiring — the shared id *is* the wiring. Different ids → independent, unlinked panels.

Must-knows (all easy to get wrong):

0. **Requires `@uipath/ui-widgets-validation-station >= 1.1.0`** — earlier versions expose a different subcomponent API.
1. **Fetch artifacts once, share them — and memoise the `data` you pass in.** Call `useDuDocumentArtifacts` in the parent and pass the same `artifacts` object to all subcomponents; calling it per-subcomponent re-downloads the document once per panel. The hook keys its fetch on `data`'s **identity**, so building that object inline in render (e.g. `{ ...raw, FolderId: task.folderId }`) refetches forever. Wrap it in `useMemo`.
2. **Only `CompactFieldsForm` gets `sdk`/`data`.** It owns persistence. The other four take the pre-fetched `artifacts` only.
3. **Set `persistent: false` for static layouts.** These panels sit in a fixed grid and are never re-parented. Leaving `persistent` on makes React StrictMode's throwaway unmount call `forceDestroy()`, tearing down the underlying element so it renders **blank**. Only set `persistent: true` if you actually move a subcomponent between DOM parents.
4. **Drop duplicated panels via `options`.** When you render `CompactBusinessRules` / `CompactDocTypeField` standalone, tell the fields form to hide its built-in copies: `options={{ hideBusinessRules: true, hideDocumentTypeField: true, emitDtoStateChanges: true }}`. (`emitDtoStateChanges` is still required for save-as-draft, same as the monolithic widget.)

The same staging and `configureValidationStationWc()` setup as the monolithic widget applies (see [Static Assets](#static-assets--staging-the-web-component)) — the subcomponents come from the same bundle. Peer versions and SDK scopes are identical too.

```typescript
import {
  DocumentViewer,
  CompactDocTypeField,
  CompactFieldsForm,
  CompactTableEditor,
  CompactBusinessRules,
  useDuDocumentArtifacts,
  ValidationStationLanguage,
  type IVsSaveValidatedDataRequest,
  type SaveValidatedDataResult,
} from '@uipath/ui-widgets-validation-station';
import type { DuFramework } from '@uipath/uipath-typescript/document-understanding';
import { TaskType } from '@uipath/uipath-typescript/tasks';
import type { TaskGetResponse } from '@uipath/uipath-typescript/tasks';
import { useMemo } from 'react';
import { useAuth } from '../hooks/useAuth';

// `task` is already hydrated via tasks.getById(...) — see "Integration: Web App".
function ReviewWorkspace({ task }: { task: TaskGetResponse }) {
  const { sdk } = useAuth();
  // Memoised: the fetch keys off this object's identity, so a fresh one each render refetches
  // the document forever. The payload is also what names the folder.
  const data = useMemo(() => {
    const raw = task.data as DuFramework.ContentValidationData;
    if (raw.FolderId != null || raw.FolderKey != null || task.folderId == null) return raw;
    return { ...raw, FolderId: task.folderId };
  }, [task]);
  const { artifacts, error } = useDuDocumentArtifacts(sdk, data);

  if (error) return <div>Failed to load document: {error}</div>;
  if (!artifacts) return <div>Loading document…</div>;

  // One shared store for the whole screen, scoped to this document.
  const instanceId = `review-${data.DocumentId ?? task.id}`;
  const shared = {
    artifacts,
    documentId: data.DocumentId,
    instanceId,
    theme: 'light' as const, // also set body class to match — see Critical Rule #4
    language: ValidationStationLanguage.English,
    persistent: false, // static grid — see must-know #3
  };

  const handleSubmit = async (
    _request: IVsSaveValidatedDataRequest,
    result?: SaveValidatedDataResult,
  ) => {
    if (!result?.success) return; // widget renders no error UI — surface it yourself
    await task.complete({ action: 'Completed', type: TaskType.DocumentValidation });
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: 8, height: '100%' }}>
      <DocumentViewer {...shared} style={{ height: '100%' }} />
      <CompactDocTypeField {...shared} />
      <CompactFieldsForm
        {...shared}
        sdk={sdk}
        data={data}
        // Keeps the built-in Submit/Report buttons. Add hideSubmitButton +
        // hideReportAsExceptionButton (and omit enableSaveAsDraft) if you render
        // your own toolbar — see the anti-patterns below.
        options={{ hideBusinessRules: true, hideDocumentTypeField: true, emitDtoStateChanges: true }}
        onSubmit={handleSubmit}
      />
      <CompactTableEditor {...shared} />
      <CompactBusinessRules {...shared} />
    </div>
  );
}
```

Runnable end-to-end example (task list + selection + all five subcomponents wired to Submit / Save-draft / Report-exception): the [`document-validation-subcomponents-app` sample](https://github.com/UiPath/uipath-typescript/tree/main/samples/document-validation-subcomponents-app) in the SDK repo.

## Anti-patterns

- **Do not forget `configureValidationStationWc()`.** Without it no custom element is registered and every component renders nothing — no error boundary, no empty state. A green `npm run build` hides it; run the app.
- **Do not skip staging the bundle, or trim its fonts.** `public/du-vs-wc` must hold the whole package. Dropping `fonts.css` / `media/` to save ~40 MB leaves every icon blank, because an iframed app inherits no `@font-face` rules from the page around it.
- **Pick one source of action buttons — built-in or custom — never both.** The monolithic `ValidationStation` renders its own action bar (Submit, Save-draft, Discard, Report). Either rely on those built-ins (drop the controlled `save`/`discardChanges` props — the callbacks still fire), **or** drive the flows from your own toolbar via the controlled props. If you build a custom toolbar, hide the built-in buttons so they don't show twice — but note `IValidationStationOptions` only exposes `hideSubmitButton` and `hideReportAsExceptionButton`, with **no** flag for the built-in Discard or Save-draft, so a fully custom bar isn't achievable with the all-in-one widget.
- **Do not construct a second `UiPath` SDK** for the widget. Reuse the app's authenticated instance.
- **Do not call `setTaskData` and try to drive a custom form alongside the widget.** The widget owns the data contract end-to-end; mixing produces stale state and double saves.
- **Do not pass a `tasks.getAll()` row straight into the widget.** `getAll()` rows omit `data` — the viewer renders empty. Hydrate with `tasks.getById(id, { taskType: TaskType.DocumentValidation }, folderId)` first.
- **Do not call `completeTask` inside the `save` setter.** Always wait for `onSubmitComplete` with `success: true` — submit may fail validation, and completing early submits unvalidated data.
- **Do not assume the widget shows an error on failure — it does not.** `onSubmit`/`onSaveAsDraft` render no UI on failure; surface the error yourself (`showMessage`, toast, etc.).
- **Do not treat a missing `result` as success.** `onSubmit`/`onSaveAsDraft` pass `result` only when the widget owned the write-back. `if (!result?.success) return;` — completing on an absent result closes the task over unsaved edits.
- **Do not treat `onReportException` like the save callbacks.** It receives one `request`, not `(request, result?)`, and persists nothing — read the reason off `request.exceptionReport` and call `OrchestratorDuModule.submitExceptionReport(...)` yourself.
- **Do not complete the task after reporting an exception.** The `SubmitExceptionReport` endpoint completes the task server-side, so calling `completeTask` as well closes an already-closed task.
- **Always pass `contentValidationData` back to `completeTask` verbatim.** `completeTask(outcome, data)` **replaces** the task's data, so `{}` — or any payload missing that field — wipes it. Every other field is free to change: send whatever the action's own controls collected alongside it. (`Tasks.complete()` in a web app differs: `data` is optional for `TaskType.DocumentValidation`, and omitting it is not the same as passing `{}`.)

Subcomponents (compose-your-own layout) only:

- **Do not call `useDuDocumentArtifacts` inside each subcomponent.** Fetch once in the parent and pass the same `artifacts` down, or you refetch the whole document per panel.
- **Do not build the `data` object inline in render.** The hook keys its fetch on identity; an unmemoised `{ ...raw, FolderId }` refetches the document on every render, without end.
- **Do not give more than one subcomponent `sdk`/`data`.** Only `CompactFieldsForm` persists.
- **Do not leave `persistent` on for a static grid.** StrictMode's throwaway unmount calls `forceDestroy()` and the panel renders blank. Use `persistent: false` unless you actually re-parent the subcomponent.
- **Do not give subcomponents different `instanceId`s** and expect them to sync — the shared id is what links the store; mismatched ids leave the panels independent.
- **Do not render `CompactBusinessRules`/`CompactDocTypeField` standalone without hiding the form's built-in copies** (`options.hideBusinessRules` / `hideDocumentTypeField`) — you'll get each panel twice.
- **Do not add your own Submit / Save-draft / Report-exception controls without hiding the form's built-in buttons** (`options.hideSubmitButton` / `hideReportAsExceptionButton`, and omit the `enableSaveAsDraft` prop) — `CompactFieldsForm` ships its own action bar, so every action renders twice. The controlled `save` / `discardChanges` props still drive the flows once the built-ins are hidden. (`enableSaveAsDraft` only exposes the built-in draft button; the controlled `save={{ validate: false }}` trigger keeps working via `options.emitDtoStateChanges`. There is no flag to hide the built-in discard control — drop your own Discard button if it would duplicate.)
