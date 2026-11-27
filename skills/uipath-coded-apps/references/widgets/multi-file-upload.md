# Multi-File Upload Widget

React widget that uploads multiple files concurrently to an **Orchestrator Storage Bucket** — drag-and-drop, file-type/size validation, per-file error tracking, partial-success handling.

Package: [`@uipath/ui-widgets-multi-file-upload`](https://www.npmjs.com/package/@uipath/ui-widgets-multi-file-upload). Full prop/API surface lives in the package README — this file covers only the integration steps that are easy to get wrong inside a Coded App.

> **Publish status — check the peer range first:** `npm view @uipath/ui-widgets-multi-file-upload version peerDependencies`. The published **1.0.0** pins `@uipath/uipath-typescript@1.1.1` **exactly** and is runtime-broken on SDK >= 1.5: `npm install` fails with ERESOLVE, and forcing it in fails at upload time with `telemetryClient.track is not a function` (the widget calls a telemetry API removed from newer SDKs). It also cannot coexist with the chat widget (peer `^1.5.5`) in one app. Until a version with peer `^1.4.1` ships, install a tarball built from the `uipath-ui-widgets` repo, or hand-roll the upload via `Buckets.uploadFile()` and say why.

## When to Use

- User asks to **upload files/documents** from the app into a storage bucket (e.g., feeding a DU or RPA pipeline's input folder).
- Replaces a hand-rolled `<input type="file">` + `Buckets.uploadFile()` loop — the widget already handles concurrency, validation, retry-of-failed, and error display.
- To *display* an uploaded PDF afterwards, pair with the PDF Viewer widget ([pdf-viewer.md](pdf-viewer.md)).

## Critical Rules

1. **Peer versions are hard requirements.** `react >= 19.2.0`, `react-dom >= 19.2.0`, `@uipath/uipath-typescript >= 1.4.1` — the SDK floor applies to widget versions **newer than 1.0.0**; see the publish-status warning above.
2. **Import the stylesheet once**: `import '@uipath/ui-widgets-multi-file-upload/MultiFileUpload.css'`. Body needs `light` or `dark` class.
3. **Required scope: `OR.Buckets`** — upload is a write; read-only `OR.Buckets.Read` is insufficient. Add to the `scope` field in `uipath.json` before first run; mismatch fails with 401/403. See [../oauth-scopes.md](../oauth-scopes.md).
4. **`bucketId` and `folderId` are numbers.** `folderId` is the Orchestrator folder containing the bucket — a numeric id, **not** the folder GUID (`folderKey`). At runtime resolve via `new Buckets(sdk).getAll({ folderId })`; never `parseInt(folderKey)` (bridge via [Bridging folderKey ↔ folderId](../sdk/orchestrator.md#bridging-folderkey--folderid)). CLI lookup: bucket ids via `uip or buckets list --all-folders --output json` (`Id` field); the numeric folder id via `uip or folders get <FOLDER_KEY_OR_PATH> --output json` → `Data.Id` — `folders list` returns only GUID `Key`s, and `folders get` 404s for personal workspaces (resolve those at runtime instead).
5. **Handle BOTH callbacks — partial success is a first-class outcome.** `onUploadSuccess(files)` receives **only the files that uploaded**; failed files stay in the list (with per-file errors) for the user to retry. `onUploadError` fires when the whole batch fails. Wiring only `onUploadSuccess` hides partial failures from your app logic.
6. **Reuse the app's initialized `UiPath` instance** (`useAuth()` in web apps); do not construct a second SDK.
7. **No special `vite.config.ts` setup** — no asset plugins or `optimizeDeps` changes needed.

## Install

From inside the scaffolded app directory:

```bash
npm install @uipath/ui-widgets-multi-file-upload --@uipath:registry=https://registry.npmjs.org
```

Registry flag forces the public npm registry (skill default — users may have `@uipath` scoped to GitHub Packages).

## Key Props

| Prop | Required | Notes |
|------|----------|-------|
| `sdk` | Yes | Initialized `UiPath` instance from `useAuth()`. |
| `bucketId` | Yes | Numeric storage bucket id. |
| `folderId` | Yes | Numeric id of the folder containing the bucket. |
| `path` | No | Key prefix for uploads (e.g. `"uploads/"` — trailing slash added if missing). |
| `accept` | No | Comma-separated extensions/MIME types (standard HTML `accept` semantics). |
| `maxFileSizeInMb` | No | Per-file size cap; oversize files are rejected client-side. |
| `onUploadSuccess` | No | `(uploadedFiles: File[]) => void` — successful files only (may be a subset). |
| `onUploadError` | No | `(error: Error) => void` — whole-batch failure. |

## Integration: Web App

Upload into a bucket and refresh a listing on success:

```typescript
import { MultiFileUpload } from '@uipath/ui-widgets-multi-file-upload';
import '@uipath/ui-widgets-multi-file-upload/MultiFileUpload.css';
import { Buckets } from '@uipath/uipath-typescript/buckets';
import { useCallback, useMemo } from 'react';
import { useAuth } from '../hooks/useAuth';

function UploadPage({ bucketId, folderId }: { bucketId: number; folderId: number }) {
  const { sdk } = useAuth();
  const buckets = useMemo(() => new Buckets(sdk), [sdk]);

  const refresh = useCallback(async () => {
    const page = await buckets.getFiles(bucketId, { folderId });
    // render page.items (filter out f.isDirectory); loop cursor for full listings
  }, [buckets, bucketId, folderId]);

  return (
    <MultiFileUpload
      sdk={sdk}
      bucketId={bucketId}
      folderId={folderId}
      path="uploads/"
      accept=".pdf,.png,.jpg"
      maxFileSizeInMb={10}
      onUploadSuccess={refresh}
      onUploadError={(e) => console.error('Upload failed:', e)} // surface in your UI
    />
  );
}

export default UploadPage;
```

Resolve a bucket id by name:

```typescript
const page = await new Buckets(sdk).getAll({ folderId });
const bucket = page.items.find((b) => b.name === 'Invoices');
```

## Anti-patterns

- **Do not hand-roll a multi-file upload loop over `Buckets.uploadFile()`** when this widget fits.
- **Do not pass a folder GUID as `folderId`** — it is the numeric Orchestrator folder id.
- **Do not wire only `onUploadSuccess`** — partial failures keep files in the list silently unless your app also reacts (`onUploadError` fires only when *all* files fail; per-file errors render inside the widget).
- **Do not assume the callback means "all selected files uploaded"** — `uploadedFiles` may be a subset; compare against what the user selected if completeness matters.
- **Do not ship with `OR.Buckets.Read`** — uploads need the full `OR.Buckets` scope.
