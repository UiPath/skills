# Validation Station Widget

React wrapper around the UiPath Document Understanding **Validation Station** web component. Use when the app must let a human review and correct extraction results from a DU document.

Package: [`@uipath/ui-widgets-validation-station`](https://www.npmjs.com/package/@uipath/ui-widgets-validation-station). Full prop/API surface lives in the package README — this file covers only the integration steps that are easy to get wrong inside a Coded App.

## When to Use

- User asks to **validate, review, correct, or approve** Document Understanding extraction results.
- App receives a `ContentValidationData` payload (bucket paths + document ID) — either from an Action Center task created by a DU workflow, or fetched at runtime in a web app.
- Replaces a hand-rolled PDF viewer + field editor. Do **not** rebuild this UI from scratch — the widget already handles PDF rendering, bounding boxes, table editing, translations, and save/discard plumbing.

If the user just wants a generic form (no DU document), use the standard Action App form pattern in [../create-action-app.md](../create-action-app.md) instead.

## Critical Rules

1. **Peer versions are hard requirements.** Widget requires `react >= 19.2.0`, `react-dom >= 19.2.0`, `@uipath/uipath-typescript >= 1.4.2`. The Vite scaffold pins React 19.2+, but verify in `package.json` before installing.
2. **Copy all runtime files into build output — not just `du-assets/`.** The web component `fetch`es four things at runtime via `import.meta.url`: `du-assets/` (PDF.js worker, cmaps, wasm, i18n), `styles.css` (adopted into its **shadow root** — this styles the icons), `fonts.css`, and `media/` (font files). Missing files 404 silently — no build error. Symptoms: PDFs don't render; **icons render as empty boxes or raw text** (shadow root never got `styles.css`). See "Static assets" below. Do NOT add `styles.css`/`fonts.css` ES-module imports yourself — the wrapper already does that for the light DOM; the copy step is only about the runtime `fetch`.
3. **Dev server must serve raw CSS for the WC's `fetch`.** Vite rewrites `.css` requests into JS modules, so the WC's `fetch("styles.css")` gets JavaScript, `CSSStyleSheet.replaceSync()` parses nothing, and shadow-root styles never load (**broken icons in dev**). Add the dev middleware from "Static assets" below. webpack-dev-server serves copied files verbatim — not affected.
4. **Set `optimizeDeps.exclude: ['@uipath/du-validation-station-wc']` in `vite.config.ts`.** Vite's pre-bundler rewrites `import.meta.url` and breaks runtime asset resolution.
5. **Body needs `light` or `dark` class** for theming. Match it to the `theme` prop. Action apps already manage this via `onInitTheme` from `CodedActionAppService.getTask()`.
6. **`sdk` must already be initialized.** Pass the same `UiPath` instance produced by `useAuth()` (web app) or constructed in `src/uipath.ts` (action app). Do not construct a second SDK just for the widget — auth state will diverge.
7. **Required SDK scopes:** `OR.Buckets` (the widget fetches the document and extraction artifacts from a storage bucket). Add `OR.Tasks` as well when the widget is rendered inside an Action Center task (action app, or web app that completes a task on save). Add to `VITE_UIPATH_SCOPE` before first run; mismatch fails silently with 401/403. See [../oauth-scopes.md](../oauth-scopes.md).
8. **Widget does NOT surface failures.** `onSubmitComplete` / `onSaveAsDraftComplete` fire with `{ success: false, error }` on failure but render no toast — the host owns all UI feedback (toast, retry, log). Wire these callbacks or failures are silent.
9. **Report-as-exception makes no API call.** `onReportExceptionComplete(documentId, reason)` only hands the host the data — it does NOT persist. The host must call `OrchestratorDuModule.submitExceptionReport(taskId, documentId, reason, { folderId })` itself, or the user's "Report as exception" click is a no-op. Needs `OR.Tasks`.

## Install

From inside the scaffolded app directory:

```bash
npm install @uipath/ui-widgets-validation-station --@uipath:registry=https://registry.npmjs.org
```

Registry flag forces the public npm registry (skill default — users may have `@uipath` scoped to GitHub Packages).

## Static Assets — Vite Plugins

The WC resolves four things **at runtime** relative to its served bundle (`import.meta.url`): `du-assets/` (PDF.js worker, cmaps, wasm, i18n), `styles.css` (fetched as raw CSS, adopted into the **shadow root** — styles the `<mat-icon>` glyphs), `fonts.css`, and `media/` (font files). The React wrapper already imports `styles.css`/`fonts.css` as ES modules for the **light DOM** (`@font-face`, CDK overlays) — you do NOT add those imports. You DO have to make the same files reachable by the WC's runtime `fetch`, which needs two plugins:

- `copyDuValidationStationAssets` (**build**) — copy the four runtime files next to the emitted JS chunks.
- `serveDuValidationStationRawCss` (**dev**) — return raw CSS for the WC's `fetch("styles.css")`, which Vite would otherwise serve as a JS module (→ broken icons in dev). Distinguish the raw fetch (`Sec-Fetch-Dest: empty`) from genuine ES-module imports (`Sec-Fetch-Dest: script`).

Replace `vite.config.ts` with the full file below:

```typescript
import react from '@vitejs/plugin-react';
import { cp, readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, resolve } from 'node:path';
import { defineConfig, type Plugin } from 'vite';

const require = createRequire(import.meta.url);

const WC_ROOT = dirname(
  require.resolve('@uipath/du-validation-station-wc/package.json'),
);

// Stylesheets the WC fetches (as raw CSS) at runtime to adopt into its shadow root.
const WC_RUNTIME_CSS = ['styles.css', 'fonts.css'];

function copyDuValidationStationAssets(): Plugin {
  let assetsDir = '';
  return {
    name: 'copy-du-validation-station-assets',
    apply: 'build',
    configResolved(config) {
      assetsDir = resolve(config.root, config.build.outDir, config.build.assetsDir);
    },
    async closeBundle() {
      await Promise.all([
        cp(resolve(WC_ROOT, 'du-assets'), resolve(assetsDir, 'du-assets'), { recursive: true }),
        cp(resolve(WC_ROOT, 'media'), resolve(assetsDir, 'media'), { recursive: true }),
        ...WC_RUNTIME_CSS.map((css) => cp(resolve(WC_ROOT, css), resolve(assetsDir, css))),
      ]);
    },
  };
}

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
  plugins: [react(), copyDuValidationStationAssets(), serveDuValidationStationRawCss()],
  base: './',
  optimizeDeps: {
    exclude: ['@uipath/du-validation-station-wc'],
  },
});
```

Verify after `npm run build`: `ls dist/assets/` must contain `du-assets/` (with `pdfjs/`, `cmaps/`, `wasm/`, `i18n/`), `media/`, `styles.css`, and `fonts.css`. Missing any → plugin did not run. In dev, confirm icons render as glyphs (not empty boxes) — broken icons mean the raw-CSS middleware isn't firing.

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

## Anti-patterns

- **Do not copy only `du-assets/` and forget the stylesheets.** The WC also fetches `styles.css`, `fonts.css`, and `media/` at runtime. Miss them and PDFs 404 and **icons render as empty boxes** — no build error. Copy all four (build) and serve raw CSS (dev).
- **Do not construct a second `UiPath` SDK** for the widget. Reuse the app's authenticated instance.
- **Do not call `setTaskData` and try to drive a custom form alongside the widget.** The widget owns the data contract end-to-end; mixing produces stale state and double saves.
- **Do not pass a `tasks.getAll()` row straight into the widget.** `getAll()` rows omit `data` — the viewer renders empty. Hydrate with `tasks.getById(id, { taskType: TaskType.DocumentValidation }, folderId)` first.
- **Do not call `completeTask` inside the `save` setter.** Always wait for `onSubmitComplete` with `success: true` — submit may fail validation, and completing early submits unvalidated data.
- **Do not assume the widget shows an error on failure — it does not.** `onSubmitComplete`/`onSaveAsDraftComplete` with `success: false` render no UI; surface the error yourself (`showMessage`, toast, etc.).
- **Do not treat `onReportExceptionComplete` like the save callbacks.** It receives `(documentId, reason)`, not `SaveValidatedDataResult`, and persists nothing — you must call `OrchestratorDuModule.submitExceptionReport(...)` before completing the task.
