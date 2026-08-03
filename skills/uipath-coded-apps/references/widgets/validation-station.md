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

1. **Peer versions are hard requirements.** Widget requires `react >= 19.2.0`, `react-dom >= 19.2.0`, `@uipath/uipath-typescript >= 1.4.1`. The Vite scaffold pins React 19.2+, but verify in `package.json` before installing.
2. **The widget's web component loads its CSS, fonts, and assets at runtime, not at build time.** So `vite.config.ts` must *copy* those files next to the build output (for prod) and *serve them as raw CSS* in dev — use the config under "Static Assets" below. Skip it and you get 404s for PDF/fonts/styling in prod, or icons that render as their names (`warning`, `error`, `circle`) in dev. A green `npm run build` hides both — run the app to confirm.
3. **Set `optimizeDeps.exclude: ['@uipath/du-validation-station-wc']` in `vite.config.ts`.** Vite's pre-bundler rewrites `import.meta.url` and breaks runtime asset resolution.
4. **Body needs `light` or `dark` class** for theming. Match it to the `theme` prop. Action apps already manage this via `onInitTheme` from `CodedActionAppService.getTask()`.
5. **`sdk` must already be initialized.** Pass the same `UiPath` instance produced by `useAuth()` (web app) or constructed in `src/uipath.ts` (action app). Do not construct a second SDK just for the widget — auth state will diverge.
6. **Required SDK scopes:** `OR.Buckets` (the widget fetches the document and extraction artifacts from a storage bucket). Add `OR.Tasks` as well when the widget is rendered inside an Action Center task (action app, or web app that completes a task on save). Add to the `scope` field in `uipath.json` before first run; mismatch fails silently with 401/403. See [../oauth-scopes.md](../oauth-scopes.md).
7. **Widget does NOT surface failures.** `onSubmitComplete` / `onSaveAsDraftComplete` fire with `{ success: false, error }` on failure but render no toast — the host owns all UI feedback (toast, retry, log). Wire these callbacks or failures are silent.
8. **Report-as-exception makes no API call.** `onReportExceptionComplete(documentId, reason)` only hands the host the data — it does NOT persist. The host must call `OrchestratorDuModule.submitExceptionReport(taskId, documentId, reason, { folderId })` itself, or the user's "Report as exception" click is a no-op. Needs `OR.Tasks`.

## Install

From inside the scaffolded app directory:

```bash
npm install @uipath/ui-widgets-validation-station --@uipath:registry=https://registry.npmjs.org
```

Registry flag forces the public npm registry (skill default — users may have `@uipath` scoped to GitHub Packages).

## Static Assets — Vite Plugin

The widget (both the all-in-one `ValidationStation` and the subcomponents) wraps a web component — `@uipath/du-validation-station-wc` — that fetches its own stylesheets and fonts at runtime, so `vite.config.ts` must do two things (plus `optimizeDeps.exclude` — the WC's `import.meta.url` breaks under pre-bundling):

- **Build:** copy the WC's `du-assets/`, `media/`, and raw `styles.css`/`fonts.css` next to the emitted chunks.
- **Dev:** serve those `.css` requests as raw CSS — Vite otherwise returns a JS module, which the WC can't read (icons then render as words).

**Add these to your existing `vite.config.ts` — merge them in, don't overwrite the whole file, so you keep `uipathCodedApps()` and anything else the scaffold generated:**

```typescript
import react from '@vitejs/plugin-react';
import { uipathCodedApps } from '@uipath/coded-apps-dev/vite';
import { cp, readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, resolve } from 'node:path';
import { defineConfig, type Plugin } from 'vite';

const require = createRequire(import.meta.url);

const WC_ROOT = dirname(
  require.resolve('@uipath/du-validation-station-wc/package.json')
);

const WC_RUNTIME_CSS = ['styles.css', 'fonts.css']; // the WC fetches these as raw CSS at runtime

// BUILD: copy the WC's runtime files next to the emitted chunks (it resolves them via import.meta.url).
function copyDuValidationStationAssets(): Plugin {
  let assetsDir = '';
  return {
    name: 'copy-du-validation-station-assets',
    apply: 'build',
    configResolved(config) {
      assetsDir = resolve(
        config.root,
        config.build.outDir,
        config.build.assetsDir,
      );
    },
    async closeBundle() {
      await cp(resolve(WC_ROOT, 'du-assets'), resolve(assetsDir, 'du-assets'), {
        recursive: true,
      });
      await cp(resolve(WC_ROOT, 'media'), resolve(assetsDir, 'media'), {
        recursive: true,
      });
      for (const css of WC_RUNTIME_CSS) {
        await cp(resolve(WC_ROOT, css), resolve(assetsDir, css));
      }
    },
  };
}

// DEV: Vite serves .css as a JS module — return raw CSS for the WC's fetch (Sec-Fetch-Dest: empty).
function serveDuValidationStationRawCss(): Plugin {
  const pattern = new RegExp(
    `/@uipath/du-validation-station-wc/(${WC_RUNTIME_CSS.join('|')})$`,
  );
  return {
    name: 'serve-du-validation-station-raw-css',
    apply: 'serve',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (req.headers['sec-fetch-dest'] !== 'empty') return next();
        const match = pattern.exec((req.url ?? '').split('?')[0]);
        if (!match) return next();
        readFile(resolve(WC_ROOT, match[1]), 'utf8').then((css) => {
          res.setHeader('Content-Type', 'text/css');
          res.end(css);
        }, next);
      });
    },
  };
}

export default defineConfig({
  plugins: [
    react(),
    uipathCodedApps(),
    copyDuValidationStationAssets(),
    serveDuValidationStationRawCss(),
  ],
  base: './',
  define: {
    global: 'globalThis',
  },
  optimizeDeps: {
    include: ['@uipath/uipath-typescript'],
    exclude: ['@uipath/du-validation-station-wc'],
  },
});
```

> Mirrors the widget's own `README.md` "Vite" section — re-check it if the widget version changes.

**Verify (a green build isn't enough):**
- **Build:** `dist/assets/` contains `du-assets/`, `media/`, `styles.css`, and `fonts.css`.
- **Dev:** run the app — icons render as glyphs, not the words `warning`/`error`/`circle`.

## Key Props

Full table in the package README. Inside a coded app you usually only touch:

| Prop | Required | Notes |
|------|----------|-------|
| `sdk` | Yes | `UiPath` instance — from `useAuth()` or `src/uipath.ts`. Must be initialized. |
| `data` | Yes | `ContentValidationData` — for action apps, this comes from the task payload. For web apps, fetch and pass yourself. |
| `folderId` | No* | Falls back to `data.FolderId`. One of the two must resolve to a value or the widget errors — pass explicitly when the payload omits it. |
| `theme` | No | `'light' \| 'dark' \| 'light-hc' \| 'dark-hc'`. Keep in sync with body class. |
| `language` | No | `ValidationStationLanguage` enum exported from the package (e.g. `English`, `German`, `Japanese`, `ChineseSimplified`). |
| `isReadonly` | No | `true` to render in read-only mode (e.g., audit view). |
| `options` | No | `IValidationStationOptions` — fine-grained WC feature flags. Set `emitDtoStateChanges: true` to enable save-as-draft. |
| `save` | No | Controlled trigger from a button. `{ validate: true }` = **submit** (validate, then save). `{ validate: false }` = **save as draft** (requires `options.emitDtoStateChanges: true`, else no-op). |
| `discardChanges` | No | Controlled trigger: `{ value: true }` to discard pending edits. Pass a fresh object each time — the widget watches for the new reference, so repeated `{ value: true }` calls all fire. |
| `onSubmitComplete` | No | Fires after **submit** (`save={{ validate: true }}`): ProcessExtractedData + bucket upload. Receives `SaveValidatedDataResult`. Use to complete the task with the approve action. |
| `onSaveAsDraftComplete` | No | Fires after **save as draft** (`save={{ validate: false }}`): uploads in-progress data, no ProcessExtractedData. Receives `SaveValidatedDataResult`. |
| `onReportExceptionComplete` | No | Fires when the user reports an exception. Signature `(documentId, reason)`, **not** `SaveValidatedDataResult`. Widget makes **no API call** — host must persist via `OrchestratorDuModule.submitExceptionReport(...)`. |

The widget surfaces three flows. **Submit** and **save as draft** are owned end-to-end by the widget and hand the host a `SaveValidatedDataResult` — `{ success: true }` or `{ success: false, error: string }`. **Report as exception** is forwarded to the host as raw `(documentId, reason)` strings with no API call. The widget renders no failure UI for any flow — handle `success: false` in the callback yourself (toast, retry, log).

## Integration: Action App (most common)

Validation Station as the form inside an Action Center DU validation task. Replaces `src/components/Form.tsx` from the standard action-app scaffold.

```typescript
// src/components/Form.tsx
import { useState, useEffect, useCallback } from 'react';
import {
  ValidationStation,
  ValidationStationLanguage,
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
  const [data, setData] = useState<DuFramework.ContentValidationData | null>(null);
  const [taskId, setTaskId] = useState<number | undefined>(undefined);
  const [folderId, setFolderId] = useState<number | undefined>(undefined);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [isReadonly, setIsReadonly] = useState(false);
  const [save, setSave] = useState<{ validate: boolean } | undefined>(undefined);

  useEffect(() => {
    codedActionAppService.getTask().then((task) => {
      // task.data is typed `unknown`; the payload is ContentValidationData
      setData(task.data as DuFramework.ContentValidationData);
      setTaskId(task.taskId);
      setFolderId(task.folderId);
      setIsReadonly(task.isReadOnly);
      const dark = isDarkTheme(task.theme);
      setTheme(dark ? 'dark' : 'light');
      onInitTheme(dark);
    });
  }, [onInitTheme]);

  // Submit succeeded → approve the task. Widget shows no error toast — handle failure here.
  const handleSubmitComplete = useCallback(
    async (result: SaveValidatedDataResult) => {
      if (!result.success) {
        codedActionAppService.showMessage(result.error, MessageSeverity.Error);
        return;
      }
      await codedActionAppService.completeTask('Approve', {});
    },
    [],
  );

  // Report-as-exception is not persisted by the widget — call the SDK, then reject the task.
  const handleReportException = useCallback(
    async (documentId: string, reason: string) => {
      if (taskId === undefined) return;
      const response = await new OrchestratorDuModule(sdk).submitExceptionReport(
        taskId,
        documentId,
        reason || 'Reported via Validation Station',
        { folderId },
      );
      if (!response.IsSuccessful) {
        codedActionAppService.showMessage(
          response.ErrorMessage ?? 'Failed to report exception',
          MessageSeverity.Error,
        );
        return;
      }
      await codedActionAppService.completeTask('Reject', {});
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
        folderId={folderId}
        theme={theme}
        language={ValidationStationLanguage.English}
        isReadonly={isReadonly}
        save={save}
        onSubmitComplete={handleSubmitComplete}
        onReportExceptionComplete={handleReportException}
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
await sdk.initialize();
export const codedActionAppService = new CodedActionAppService();
```

`action-schema.json` for a DU validation task typically has no `inputs`/`outputs` — the widget owns the data contract. A minimal schema:

```json
{
  "inputs":  { "type": "object", "properties": {} },
  "outputs": { "type": "object", "properties": {} },
  "inOuts":  { "type": "object", "properties": {} },
  "outcomes": {
    "type": "object",
    "properties": {
      "Approve": { "type": "string" },
      "Reject":  { "type": "string" }
    }
  }
}
```

## Integration: Web App

Same widget, sdk comes from `useAuth()`. Typical flow: list `TaskType.DocumentValidation` tasks with `tasks.getAll(...)`, **then hydrate the selected row with `tasks.getById(...)` to load `task.data`** — `getAll()` returns task summaries without `data` populated, so passing a `getAll` row straight into the widget produces an empty viewer.

```typescript
import { useEffect, useMemo, useState } from 'react';
import {
  ValidationStation,
  ValidationStationLanguage,
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

  const handleSubmitComplete = async (result: SaveValidatedDataResult) => {
    if (!result.success || !selectedTask) return; // widget renders no error UI — surface it yourself
    await selectedTask.complete({
      action: 'Completed',
      type: TaskType.DocumentValidation,
    });
  };

  if (!selectedTask) return null;

  return (
    <ValidationStation
      sdk={sdk}
      data={selectedTask.data as DuFramework.ContentValidationData}
      folderId={selectedTask.folderId}
      theme="light"
      language={ValidationStationLanguage.English}
      onSubmitComplete={handleSubmitComplete}
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
| `useBucketArtifacts(sdk, data, folderId)` | hook | Fetches the document + extraction artifacts **once**; returns `{ artifacts, error }`. Feed `artifacts` to every subcomponent. |
| `DocumentViewer` | component | PDF/text viewer with bounding boxes. Read-only. |
| `CompactFieldsForm` | component | Extraction fields, editable. The **only** subcomponent that persists — give it `sdk` + `data` + `folderId` and it runs Submit / Save-draft / Report-exception (same callbacks as the monolithic widget). |
| `CompactTableEditor` | component | Inline editor for table (line-item) fields. Edit-only. |
| `CompactDocTypeField` | component | Document-type selector dropdown. |
| `CompactBusinessRules` | component | Read-only evaluated business rules. |

**How they link — one shared `instanceId`.** Give every subcomponent the same `instanceId` string and they share a single store: selecting a field in the form highlights it in the viewer, selecting a table field opens the table editor, clicking a rule focuses the offending field. No cross-wiring — the shared id *is* the wiring. Different ids → independent, unlinked panels.

Must-knows (all easy to get wrong):

0. **Requires a package version that exports the subcomponents** (`@uipath/ui-widgets-validation-station >= 1.0.1`). Earlier versions export only `ValidationStation`.
1. **Fetch artifacts once, share them.** Call `useBucketArtifacts` in the parent and pass the same `artifacts` object to all subcomponents. Calling it per-subcomponent re-downloads the same unchanged document once per panel.
2. **Only `CompactFieldsForm` gets `sdk`/`data`/`folderId`.** It owns persistence. The other four can take the pre-fetched `artifacts` only.
3. **Set `persistent: false` for static layouts.** These panels sit in a fixed grid and are never re-parented. Leaving `persistent` on makes React StrictMode's throwaway unmount call `forceDestroy()`, tearing down the underlying element so it renders **blank**. Only set `persistent: true` if you actually move a subcomponent between DOM parents.
4. **Drop duplicated panels via `options`.** When you render `CompactBusinessRules` / `CompactDocTypeField` standalone, tell the fields form to hide its built-in copies: `options={{ hideBusinessRules: true, hideDocumentTypeField: true, emitDtoStateChanges: true }}`. (`emitDtoStateChanges` is still required for save-as-draft, same as the monolithic widget.)

Same static-asset copy and `optimizeDeps.exclude` setup as the monolithic widget applies (see [Static Assets](#static-assets--vite-plugin)) — the subcomponents load the same web component under the hood. Peer versions and SDK scopes are identical too.

```typescript
import {
  DocumentViewer,
  CompactDocTypeField,
  CompactFieldsForm,
  CompactTableEditor,
  CompactBusinessRules,
  useBucketArtifacts,
  ValidationStationLanguage,
  type SaveValidatedDataResult,
} from '@uipath/ui-widgets-validation-station';
import type { DuFramework } from '@uipath/uipath-typescript/document-understanding';
import { TaskType } from '@uipath/uipath-typescript/tasks';
import type { TaskGetResponse } from '@uipath/uipath-typescript/tasks';
import { useAuth } from '../hooks/useAuth';

// `task` is already hydrated via tasks.getById(...) — see "Integration: Web App".
function ReviewWorkspace({ task }: { task: TaskGetResponse }) {
  const { sdk } = useAuth();
  const data = task.data as DuFramework.ContentValidationData;
  const { artifacts, error } = useBucketArtifacts(sdk, data, task.folderId);

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

  const handleSubmit = async (result: SaveValidatedDataResult) => {
    if (!result.success) return; // widget renders no error UI — surface it yourself
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
        folderId={task.folderId}
        // Keeps the built-in Submit/Report buttons. Add hideSubmitButton +
        // hideReportAsExceptionButton (and omit enableSaveAsDraft) if you render
        // your own toolbar — see the anti-patterns below.
        options={{ hideBusinessRules: true, hideDocumentTypeField: true, emitDtoStateChanges: true }}
        onSubmitComplete={handleSubmit}
      />
      <CompactTableEditor {...shared} />
      <CompactBusinessRules {...shared} />
    </div>
  );
}
```

Runnable end-to-end example (task list + selection + all five subcomponents wired to Submit / Save-draft / Report-exception): the [`document-validation-subcomponents-app` sample](https://github.com/UiPath/uipath-typescript/tree/main/samples/document-validation-subcomponents-app) in the SDK repo.

## Anti-patterns

- **Do the full static-asset setup and verify by running the app.** Both plugins (copy `du-assets/` + `media/` + raw CSS; serve raw CSS in dev) are required — a green `npm run build` hides a broken result because the WC loads its styles at runtime, not at build.
- **Pick one source of action buttons — built-in or custom — never both.** The monolithic `ValidationStation` renders its own action bar (Submit, Save-draft, Discard, Report). Either rely on those built-ins (drop the controlled `save`/`discardChanges` props — the callbacks still fire), **or** drive the flows from your own toolbar via the controlled props. If you build a custom toolbar, hide the built-in buttons so they don't show twice — but note `IValidationStationOptions` only exposes `hideSubmitButton` and `hideReportAsExceptionButton`, with **no** flag for the built-in Discard or Save-draft, so a fully custom bar isn't achievable with the all-in-one widget.
- **Do not construct a second `UiPath` SDK** for the widget. Reuse the app's authenticated instance.
- **Do not call `setTaskData` and try to drive a custom form alongside the widget.** The widget owns the data contract end-to-end; mixing produces stale state and double saves.
- **Do not pass a `tasks.getAll()` row straight into the widget.** `getAll()` rows omit `data` — the viewer renders empty. Hydrate with `tasks.getById(id, { taskType: TaskType.DocumentValidation }, folderId)` first.
- **Do not call `completeTask` inside the `save` setter.** Always wait for `onSubmitComplete` with `success: true` — submit may fail validation, and completing early submits unvalidated data.
- **Do not assume the widget shows an error on failure — it does not.** `onSubmitComplete`/`onSaveAsDraftComplete` with `success: false` render no UI; surface the error yourself (`showMessage`, toast, etc.).
- **Do not treat `onReportExceptionComplete` like the save callbacks.** It receives `(documentId, reason)`, not `SaveValidatedDataResult`, and persists nothing — you must call `OrchestratorDuModule.submitExceptionReport(...)` before completing the task.

Subcomponents (compose-your-own layout) only:

- **Do not call `useBucketArtifacts` inside each subcomponent.** Fetch once in the parent and pass the same `artifacts` down, or you refetch the whole document per panel.
- **Do not give more than one subcomponent `sdk`/`data`.** Only `CompactFieldsForm` persists.
- **Do not leave `persistent` on for a static grid.** StrictMode's throwaway unmount calls `forceDestroy()` and the panel renders blank. Use `persistent: false` unless you actually re-parent the subcomponent.
- **Do not give subcomponents different `instanceId`s** and expect them to sync — the shared id is what links the store; mismatched ids leave the panels independent.
- **Do not render `CompactBusinessRules`/`CompactDocTypeField` standalone without hiding the form's built-in copies** (`options.hideBusinessRules` / `hideDocumentTypeField`) — you'll get each panel twice.
- **Do not add your own Submit / Save-draft / Report-exception controls without hiding the form's built-in buttons** (`options.hideSubmitButton` / `hideReportAsExceptionButton`, and omit the `enableSaveAsDraft` prop) — `CompactFieldsForm` ships its own action bar, so every action renders twice. The controlled `save` / `discardChanges` props still drive the flows once the built-ins are hidden. (`enableSaveAsDraft` only exposes the built-in draft button; the controlled `save={{ validate: false }}` trigger keeps working via `options.emitDtoStateChanges`. There is no flag to hide the built-in discard control — drop your own Discard button if it would duplicate.)
