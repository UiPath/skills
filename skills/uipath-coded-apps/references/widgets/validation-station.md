# Validation Station Widget

React wrapper around the UiPath Document Understanding **Validation Station** web component. Use when the app must let a human review and correct extraction results from a DU document.

Package: [`@uipath/ui-widgets-validation-station`](https://www.npmjs.com/package/@uipath/ui-widgets-validation-station). Full prop/API surface lives in the package README — this file covers only the integration steps that are easy to get wrong inside a Coded App.

## When to Use

- User asks to **validate, review, correct, or approve** Document Understanding extraction results.
- App receives a `ContentValidationData` payload (bucket paths + document ID) — either from an Action Center task created by a DU workflow, or fetched at runtime in a web app.
- Replaces a hand-rolled PDF viewer + field editor. Do **not** rebuild this UI from scratch — the widget already handles PDF rendering, bounding boxes, table editing, translations, and save/discard plumbing.

If the user just wants a generic form (no DU document), use the standard Action App form pattern in [../create-action-app.md](../create-action-app.md) instead.

## Critical Rules

1. **Peer versions are hard requirements.** Widget requires `react >= 19.2.0`, `react-dom >= 19.2.0`, `@uipath/uipath-typescript >= 1.4.1`. The Vite scaffold pins React 19.2+, but verify in `package.json` before installing.
2. **Copy `du-assets/` into build output.** The underlying web component loads PDF.js worker, cmaps, wasm, and i18n from a sibling `du-assets/` directory resolved via `import.meta.url`. Without this, **PDF rendering and translations silently 404 in production** — no build error. See "Static assets" below.
3. **Set `optimizeDeps.exclude: ['@uipath/du-validation-station-wc']` in `vite.config.ts`.** Vite's pre-bundler rewrites `import.meta.url` and breaks runtime asset resolution.
4. **Body needs `light` or `dark` class** for theming. Match it to the `theme` prop. Action apps already manage this via `onInitTheme` from `CodedActionAppService.getTask()`.
5. **`sdk` must already be initialized.** Pass the same `UiPath` instance produced by `useAuth()` (web app) or constructed in `src/uipath.ts` (action app). Do not construct a second SDK just for the widget — auth state will diverge.
6. **Required SDK scopes:** `OR.Buckets` (the widget fetches the document and extraction artifacts from a storage bucket). Add `OR.Tasks` as well when the widget is rendered inside an Action Center task (action app, or web app that completes a task on save). Add to `VITE_UIPATH_SCOPE` before first run; mismatch fails silently with 401/403. See [../oauth-scopes.md](../oauth-scopes.md).
7. **Widget does NOT surface failures.** `onSubmitComplete` / `onSaveAsDraftComplete` fire with `{ success: false, error }` on failure but render no toast — the host owns all UI feedback (toast, retry, log). Wire these callbacks or failures are silent.
8. **Report-as-exception makes no API call.** `onReportExceptionComplete(documentId, reason)` only hands the host the data — it does NOT persist. The host must call `OrchestratorDuModule.submitExceptionReport(taskId, documentId, reason, { folderId })` itself, or the user's "Report as exception" click is a no-op. Needs `OR.Tasks`.

## Install

From inside the scaffolded app directory:

```bash
npm install @uipath/ui-widgets-validation-station --@uipath:registry=https://registry.npmjs.org
```

Registry flag forces the public npm registry (skill default — users may have `@uipath` scoped to GitHub Packages).

## Static Assets — Vite Plugin

Replace `vite.config.ts` with the full file below. The plugin runs after `build` and copies the WC's `du-assets/` next to the emitted JS chunks:

```typescript
import react from '@vitejs/plugin-react';
import { cp } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, resolve } from 'node:path';
import { defineConfig, type Plugin } from 'vite';

const require = createRequire(import.meta.url);

function copyDuValidationStationAssets(): Plugin {
  let destDir = '';
  return {
    name: 'copy-du-validation-station-assets',
    apply: 'build',
    configResolved(config) {
      destDir = resolve(
        config.root,
        config.build.outDir,
        config.build.assetsDir,
        'du-assets',
      );
    },
    async closeBundle() {
      const wcRoot = dirname(
        require.resolve('@uipath/du-validation-station-wc/package.json'),
      );
      await cp(resolve(wcRoot, 'du-assets'), destDir, { recursive: true });
    },
  };
}

export default defineConfig({
  plugins: [react(), copyDuValidationStationAssets()],
  base: './',
  optimizeDeps: {
    exclude: ['@uipath/du-validation-station-wc'],
  },
});
```

Verify after `npm run build`: `ls dist/assets/du-assets/` must list `pdfjs/`, `cmaps/`, `wasm/`, `i18n/`. Empty or missing → plugin did not run.

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

- **Do not skip the `du-assets/` copy step.** PDF rendering and translations 404 silently in prod; "works on my machine" because dev serves from `node_modules`.
- **Do not construct a second `UiPath` SDK** for the widget. Reuse the app's authenticated instance.
- **Do not call `setTaskData` and try to drive a custom form alongside the widget.** The widget owns the data contract end-to-end; mixing produces stale state and double saves.
- **Do not pass a `tasks.getAll()` row straight into the widget.** `getAll()` rows omit `data` — the viewer renders empty. Hydrate with `tasks.getById(id, { taskType: TaskType.DocumentValidation }, folderId)` first.
- **Do not call `completeTask` inside the `save` setter.** Always wait for `onSubmitComplete` with `success: true` — submit may fail validation, and completing early submits unvalidated data.
- **Do not assume the widget shows an error on failure — it does not.** `onSubmitComplete`/`onSaveAsDraftComplete` with `success: false` render no UI; surface the error yourself (`showMessage`, toast, etc.).
- **Do not treat `onReportExceptionComplete` like the save callbacks.** It receives `(documentId, reason)`, not `SaveValidatedDataResult`, and persists nothing — you must call `OrchestratorDuModule.submitExceptionReport(...)` before completing the task.
