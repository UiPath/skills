# PDF Viewer Widget

React PDF viewer for coded apps. Renders PDFs from **Orchestrator Storage Buckets**, **Data Fabric entity attachments**, or plain **URLs/Blobs** — toolbar (pagination, zoom, rotate, download), selectable text, password-protected PDFs, built-in loading/error states. Built on react-pdf (Mozilla pdf.js) with the worker **shipped inside the package** — no CDN, works behind the enterprise CSP on `*.uipath.host`.

Package: [`@uipath/ui-widgets-pdf-viewer`](https://www.npmjs.com/package/@uipath/ui-widgets-pdf-viewer). Full prop/API surface lives in the package README — this file covers only the integration steps that are easy to get wrong inside a Coded App.

> **Publish status:** this package is newer than the other widgets. Before recommending it, verify it resolves: `npm view @uipath/ui-widgets-pdf-viewer version`. On a 404 the package is not yet on the public registry — tell the user and fall back to the hand-rolled react-pdf pattern in [create-action-app.md § PDF viewer](../create-action-app.md#pdf-viewer-when-displaying-pdf-documents) rather than inventing an install path. Do **not** fall back to `<iframe>`/`<embed>`/`<object>` PDF tags — Action Center loads coded apps in a sandboxed iframe whose CSP blocks browser-native PDF rendering, and the react-pdf pattern works in web apps too.

## When to Use

- User asks to **display/preview a PDF** stored in a bucket, on a Data Fabric record, or behind a URL — e.g., the document pane beside an approval form in an action app.
- Replaces hand-rolled react-pdf/pdf.js wiring (worker setup, fetch plumbing, toolbar, password prompts).
- **Not for Document Understanding validation.** Review/correct DU extraction results → [validation-station.md](validation-station.md) (its viewer adds bounding boxes and field linkage). This widget is display-only.

## Critical Rules

1. **Peer versions are hard requirements.** `react >= 19.2.0`, `react-dom >= 19.2.0`, `@uipath/uipath-typescript >= 1.4.1`.
2. **Import the stylesheet once**: `import '@uipath/ui-widgets-pdf-viewer/PdfViewer.css'`. Body needs `light` or `dark` class.
3. **One `source` prop, four shapes — the fields you pass select the adapter.** `bucketId` → storage bucket, `entityId` → Data Fabric entity attachment, `url` → direct URL, `data` → pre-fetched `Blob`/`ArrayBuffer`.
4. **Bucket sources scope the folder with EXACTLY ONE of** `folderId` (number), `folderKey` (GUID — what coded apps usually have), or `folderPath` (e.g. `"Shared/Finance"`).
5. **`sdk` is required for `bucket`/`entity` sources** — pass the app's initialized instance from `useAuth()`. Missing sdk doesn't throw; the widget renders its own error card.
6. **Required scopes:** bucket source → `OR.Buckets.Read` (or `OR.Buckets`); entity source → `DataFabric.Data.Read`. `url`/`data` sources need no scopes (for `url`, CORS/same-origin rules apply — the browser fetches it). See [../oauth-scopes.md](../oauth-scopes.md).
7. **Never point pdf.js at a CDN worker.** The worker ships in the package and is version-locked to it; the platform CSP blocks external hosts anyway. Production builds need zero config — the worker is emitted as a same-origin asset. **Vite dev needs an `optimizeDeps` PAIR** (pre-bundling rewrites the widget's `import.meta.url` worker resolution):

   ```typescript
   optimizeDeps: {
     // Keep the widget's import.meta.url intact so its packaged worker resolves.
     exclude: ['@uipath/ui-widgets-pdf-viewer'],
     // REQUIRED with the exclude: the widget imports react-pdf, whose ESM build
     // imports CommonJS deps ('warning') that only interop when pre-bundled.
     // Exclude alone blank-pages the app at module load:
     // "does not provide an export named 'default'".
     include: ['react-pdf'],
   },
   ```

   Alternative (no exclude): override the worker once at app startup, after importing the widget:

   ```typescript
   import { pdfjs } from 'react-pdf';
   pdfjs.GlobalWorkerOptions.workerSrc = new URL(
     'pdfjs-dist/build/pdf.worker.min.mjs',
     import.meta.url,
   ).toString();
   ```

   Verify by rendering a PDF in dev AND in the built app — a green build does not prove the worker resolves.
8. **Inline `source` object literals are safe.** The widget keys sources internally, so a new object per render does NOT retrigger fetches (the classic react-pdf `file`-prop identity trap is solved inside).
9. **Non-Latin (CJK) PDFs may render blank glyphs** — v1 does not bundle pdf.js cMap assets. Warn the user if their documents are Chinese/Japanese/Korean.

## Install

From inside the scaffolded app directory (after the publish check above):

```bash
npm install @uipath/ui-widgets-pdf-viewer --@uipath:registry=https://registry.npmjs.org
```

Registry flag forces the public npm registry (skill default — users may have `@uipath` scoped to GitHub Packages).

## Key Props

| Prop | Required | Notes |
|------|----------|-------|
| `source` | Yes | `{ bucketId, folderId\|folderKey\|folderPath, path }` \| `{ entityId, recordId, fieldName }` \| `{ url }` \| `{ data }`. |
| `sdk` | No* | *Required for bucket/entity sources. |
| `toolbar` | No | Per-feature toggles `pagination`/`zoom`/`rotate`/`download` (all default `true`); disable all four to hide the toolbar. |
| `fileName` | No | Toolbar label + download filename. |
| `maxHeight` | No | Canvas max height (default `640`); the canvas scrolls internally — the widget fills its parent's width. |
| `onLoadSuccess` | No | `({ numPages }) => void`. |
| `onLoadError` | No | `(error) => void` — fetch or render failure (widget also shows its own error + Retry UI). |

## Integration: Action App (document beside the form)

Designed for a narrow split pane beside an approval form — fills its container, scrolls internally, failures stay inside the widget's box:

```typescript
import { PdfViewer } from '@uipath/ui-widgets-pdf-viewer';
import '@uipath/ui-widgets-pdf-viewer/PdfViewer.css';
import { sdk } from '../uipath'; // action app: new UiPath() with host-injected session

function DocumentPane({ folderKey, path }: { folderKey: string; path: string }) {
  return (
    <PdfViewer
      sdk={sdk}
      source={{ bucketId: 123, folderKey, path }}
      fileName={path.split('/').pop()}
      maxHeight="100%"
    />
  );
}
```

Action apps get `folderId` from `codedActionAppService.getTask()` — `source={{ bucketId, folderId, path }}` works equally; pass whichever folder identifier you already have (rule 4).

## Integration: Web App

```typescript
import { PdfViewer } from '@uipath/ui-widgets-pdf-viewer';
import '@uipath/ui-widgets-pdf-viewer/PdfViewer.css';
import { useAuth } from '../hooks/useAuth';

function InvoiceViewer({ entityId, recordId }: { entityId: string; recordId: string }) {
  const { sdk } = useAuth();

  return (
    <PdfViewer
      sdk={sdk}
      source={{ entityId, recordId, fieldName: 'InvoicePdf' }}
      onLoadError={(e) => console.error('PDF failed:', e)} // widget shows its own error card + Retry
    />
  );
}
```

## Anti-patterns

- **Do not configure a CDN `workerSrc`** — CSP blocks it and versions drift; the packaged worker is the supported path.
- **Do not fetch the PDF yourself for bucket/entity sources** — pass the source descriptor; the widget resolves the read-URI/attachment. If you already hold bytes from another flow, pass them as `{ data }`.
- **Do not use this widget for DU validation review** — that is [validation-station.md](validation-station.md); this one has no bounding boxes or field editing.
- **Do not pass two folder identifiers in a bucket source** — exactly one of `folderId`/`folderKey`/`folderPath`.
- **Do not wrap the viewer in your own loading/error/password UI** — loading, error-with-Retry, empty, and password-prompt states are built in; wire `onLoadError` for logging/telemetry, not for rendering a duplicate error screen.
