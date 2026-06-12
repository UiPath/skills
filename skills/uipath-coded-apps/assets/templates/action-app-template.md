# Action App File Templates

Complete, copy-paste scaffold for a new UiPath Coded Action App (React + TypeScript). This is the **default inspiring layout** for the skill: a design-system `index.css` (light/dark tokens), an `app-shell` wrapper, and a `Form` with an animated gradient header, sectioned cards, and a sticky outcome footer.

> **How to use this template.** Treat it as the visual + structural baseline. Keep the design system, the header/section/sticky-footer structure, the dark-theme handling, and the animations. **Adapt the schema-specific parts** — the `FormData` interface, default values, field labels, sections, number/currency formatting, and outcome buttons — to the confirmed `action-schema.json`. **Customer instructions (Q5 layout/style) always win** — layer their requested colours, layout, copy, and structure on top of this baseline; only fall back to the baseline where they gave no direction.

> **CSS ships as files, not markdown — copy them byte-for-byte.** The four stylesheets (`index.css`, `App.css`, `Form.css`, `DocumentTab.css`) live as real files under [`action-app/`](action-app/) next to this template. **Copy them verbatim into the project** (`action-app/index-template.css` → `src/index.css`, `app-template.css` → `src/App.css`, `form-template.css` → `src/components/Form.css`, `document-tab-template.css` → `src/components/DocumentTab.css`). Do **not** retype them from memory — copying the file is what keeps the default UI identical across every scaffold.

> **Customization is token-first.** Most Q5 requests — brand colour, accent, fonts, corner radius, density — are satisfied by editing the design tokens in `:root` / `body.dark` at the top of `src/index.css` **only**, leaving the component CSS untouched. Reserve edits to `Form.css` / `DocumentTab.css` for **structural** changes the tokens can't express (new sections, a different grid, added/removed regions). This keeps the baseline stable and the diff reviewable. Prefer adding a small `src/theme-overrides.css` imported after `index.css` over rewriting `index.css` when the override set is large.

> **The default `Form` is form-only — no document/PDF tab.** Only add the optional `DocumentTab` (last two sections) when the use case requires showing a document, per the PDF viewer step in [../../references/create-action-app.md](../../references/create-action-app.md). Do not wire it in by default.

> The `Form.tsx` below is shown for a loan-review example (inputs: applicant name, loan amount, credit score; outputs: risk score, reviewer comments; outcomes: Approve / Reject). Swap those specifics for the real schema; preserve the structure and styling. (`form-template.css` uses generic class names — no per-schema edits.)

---

## `src/index.css`

Design system: CSS variables for light + dark, fonts, accent gradient palette, shadows, radii. Required — every component references these tokens.

**Copy [`action-app/index-template.css`](action-app/index-template.css) verbatim to `src/index.css`.** This is the token-first customization surface: for brand/colour/font/radius requests, edit the `:root` and `body.dark` variable values here and leave the component stylesheets alone.

---

## `src/main.tsx`

Standard Vite entry — imports `index.css` so the design system loads globally.

```typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

---

## `src/App.tsx`

Owns dark/light theme state. The task theme seeds it once via `onInitTheme`; the user can then flip it with the header toggle (`onToggleTheme`). A single effect keeps `document.body` and the `app-shell` class in sync for both paths.

```typescript
import { useState, useCallback, useEffect } from 'react';
import Form from './components/Form';
import './App.css';

function App() {
  const [darkTheme, setDarkTheme] = useState(false);

  // Seed from the task theme (Action Center) on first load.
  const handleInitTheme = useCallback((isDark: boolean) => {
    setDarkTheme(isDark);
  }, []);

  // User-driven toggle.
  const toggleTheme = useCallback(() => setDarkTheme((d) => !d), []);

  // Keep <body> in sync whether the change came from the task or the toggle.
  useEffect(() => {
    document.body.className = darkTheme ? 'dark' : 'light';
  }, [darkTheme]);

  return (
    <div className={`app-shell ${darkTheme ? 'dark' : 'light'}`}>
      <Form onInitTheme={handleInitTheme} darkTheme={darkTheme} onToggleTheme={toggleTheme} />
    </div>
  );
}

export default App;
```

---

## `src/App.css`

**Copy [`action-app/app-template.css`](action-app/app-template.css) verbatim to `src/App.css`.** Just the `app-shell` wrapper; no schema-driven changes.

---

## `vite.config.ts`

`base: './'` is **always required** — the platform handles URL routing; the app must use relative asset paths.

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: './',
});
```

---

## `action-schema.json`

Data contract between the form and the Maestro/Agent workflow. All four sections are required — use `"properties": {}` for empty sections.

```json
{
  "inputs": {
    "type": "object",
    "properties": {
      "{{INPUT_FIELD}}": {
        "type": "string",
        "required": true,
        "description": "{{DESCRIPTION}}"
      }
    }
  },
  "outputs": {
    "type": "object",
    "properties": {
      "{{OUTPUT_FIELD}}": {
        "type": "string",
        "required": false
      }
    }
  },
  "inOuts": {
    "type": "object",
    "properties": {}
  },
  "outcomes": {
    "type": "object",
    "properties": {
      "Approve": { "type": "string" },
      "Reject":  { "type": "string" }
    }
  }
}
```

For the supported field types, `format` values, and structural rules, the validator script `scripts/validate-action-schema.js` is the single source of truth — validate the schema against it before writing the project.

---

## `src/uipath.ts`

Without SDK services:

```typescript
import { CodedActionAppService } from '@uipath/coded-action-app';

export const codedActionAppService = new CodedActionAppService();
```

With SDK services (add only what the app uses):

```typescript
import { UiPath } from '@uipath/uipath-typescript/core';
// import { Entities } from '@uipath/uipath-typescript/entities';
// import { Attachments } from '@uipath/uipath-typescript/attachments'; // only if showing a document
import { CodedActionAppService } from '@uipath/coded-action-app';

const sdk = new UiPath();

export const codedActionAppService = new CodedActionAppService();
// export const entities = new Entities(sdk);
// export const attachments = new Attachments(sdk);
```

> **NEVER call `sdk.initialize()` in an action app.** Construct `new UiPath()` (no args, no `.env`) and use it directly — Action Center's sandboxed iframe injects the authenticated session at runtime, so there is nothing to initialize. `sdk.initialize()` starts a PKCE OAuth **redirect**; that is a web-app-only flow and it breaks inside the iframe.

---

## `src/components/Form.tsx`

Reference layout: animated gradient header, schema-driven `FormData` merged over defaults, sectioned cards, sticky outcome footer. **Form-only — no document/PDF tab.** Adapt the `FormData` fields, defaults, labels, sections, formatting, and outcomes to the real schema.

```typescript
import { useState, useEffect } from 'react';
import type { ChangeEvent } from 'react';
import { Theme } from '@uipath/coded-action-app';
import { codedActionAppService } from '../uipath';
import './Form.css';

// One property per field across all schema sections (inputs + outputs; inOuts is empty here)
interface FormData {
  // inputs — read-only
  applicantName: string;
  loanAmount: number;
  creditScore: number;
  // outputs — reviewer-filled
  riskScore: number;
  reviewerComments: string;
}

const defaultFormData: FormData = {
  applicantName: '',
  loanAmount: 0,
  creditScore: 0,
  riskScore: 0,
  reviewerComments: '',
};

const isDarkTheme = (theme: Theme): boolean =>
  theme === Theme.Dark || theme === Theme.DarkHighContrast;

interface FormProps {
  onInitTheme: (isDark: boolean) => void;
  darkTheme: boolean;
  onToggleTheme: () => void;
}

function Form({ onInitTheme, darkTheme, onToggleTheme }: FormProps) {
  const [formData, setFormData] = useState<FormData>(defaultFormData);
  const [isReadOnly, setIsReadOnly] = useState(false);

  useEffect(() => {
    codedActionAppService.getTask().then((task) => {
      // Merge over defaults — task.data has inputs + inOuts only, never outputs on first load.
      const merged = task.data
        ? { ...defaultFormData, ...(task.data as Partial<FormData>) }
        : defaultFormData;
      setFormData(merged);
      setIsReadOnly(task.isReadOnly);
      onInitTheme(isDarkTheme(task.theme));
    });
  }, [onInitTheme]);

  const handleTextChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    if (isReadOnly) return;
    const { name, value } = e.target;
    const updated = { ...formData, [name]: value };
    setFormData(updated);
    codedActionAppService.setTaskData(updated);
  };

  const handleNumberChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (isReadOnly) return;
    const { name, value } = e.target;
    const parsed = value === '' ? 0 : Number(value);
    const updated = { ...formData, [name]: Number.isNaN(parsed) ? 0 : parsed };
    setFormData(updated);
    codedActionAppService.setTaskData(updated);
  };

  // Required outputs filled, and not read-only.
  const isFormValid =
    !isReadOnly &&
    formData.reviewerComments.trim() !== '' &&
    Number.isFinite(formData.riskScore);

  const handleApprove = async () => {
    await codedActionAppService.completeTask('Approve', formData);
  };
  const handleReject = async () => {
    await codedActionAppService.completeTask('Reject', formData);
  };

  const formatCurrency = (n: number) =>
    new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' }).format(n || 0);

  return (
    <div className="review-app">
      <header className="review-header">
        <div className="review-header__icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <path d="M14 2v6h6" />
            <path d="M9 15l2 2 4-4" />
          </svg>
        </div>
        <div className="review-header__titles">
          <h1 className="review-header__title">Loan Application Review</h1>
          <p className="review-header__subtitle">
            Review the applicant details, then record your decision.
          </p>
        </div>
        <div className="review-header__actions">
          {isReadOnly && <span className="review-badge">Read only</span>}
          <button
            type="button"
            className="theme-toggle"
            onClick={onToggleTheme}
            aria-label={darkTheme ? 'Switch to light mode' : 'Switch to dark mode'}
            title={darkTheme ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {darkTheme ? (
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="4" />
                <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            )}
          </button>
        </div>
      </header>

      <div className="form-container form-container--enter">
          <section className="form-section">
            <h2 className="form-title">Applicant Information</h2>
            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="applicantName">Applicant Name</label>
                <input id="applicantName" readOnly value={formData.applicantName} />
              </div>
              <div className="form-group">
                <label htmlFor="loanAmount">Loan Amount</label>
                <input id="loanAmount" readOnly value={formatCurrency(formData.loanAmount)} />
              </div>
              <div className="form-group">
                <label htmlFor="creditScore">Credit Score</label>
                <input id="creditScore" readOnly value={String(formData.creditScore)} />
              </div>
            </div>
          </section>

          <section className="form-section">
            <h2 className="form-title">Reviewer Assessment</h2>
            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="riskScore">
                  Risk Score <span className="req" aria-hidden="true">*</span>
                </label>
                <input
                  id="riskScore"
                  name="riskScore"
                  type="number"
                  min={0}
                  step="any"
                  value={formData.riskScore}
                  onChange={handleNumberChange}
                  readOnly={isReadOnly}
                />
              </div>
            </div>
            <div className="form-group form-group--spaced">
              <label htmlFor="reviewerComments">
                Reviewer Comments <span className="req" aria-hidden="true">*</span>
              </label>
              <textarea
                id="reviewerComments"
                name="reviewerComments"
                rows={5}
                placeholder="Add your review notes…"
                value={formData.reviewerComments}
                onChange={handleTextChange}
                readOnly={isReadOnly}
              />
            </div>
          </section>
      </div>

      <div className="form-buttons">
        <button
          type="button"
          className="outcome-btn outcome-btn--secondary"
          onClick={handleReject}
          disabled={!isFormValid}
        >
          Reject
        </button>
        <button
          type="button"
          className="outcome-btn outcome-btn--primary"
          onClick={handleApprove}
          disabled={!isFormValid}
        >
          Approve
        </button>
      </div>
    </div>
  );
}

export default Form;
```

---

## `src/components/Form.css`

**Copy [`action-app/form-template.css`](action-app/form-template.css) verbatim to `src/components/Form.css`.** Styles the gradient header, section cards, responsive grid, readonly/dashed inputs, sticky outcome footer, and entrance/header animations — all on the `index.css` tokens. Edit it only for **structural** layout changes; colour/brand/font tweaks belong in `index.css` tokens (token-first rule above).

---

## `src/components/DocumentTab.tsx`

Generic PDF viewer. Takes a ready-to-render `fileUrl` (the parent resolves the `file` attachment id → blob/URL). Owns paging, zoom, and download. Include only when the app shows a document.

```typescript
import { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import './DocumentTab.css';

pdfjs.GlobalWorkerOptions.workerSrc =
  `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface DocumentTabProps {
  // blob: URL or direct URL to the PDF. The parent fetches the file
  // (via the Attachments service) and passes the resulting URL here.
  fileUrl: string | null;
  fileName?: string;
}

export default function DocumentTab({ fileUrl, fileName = 'document.pdf' }: DocumentTabProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [pageRendering, setPageRendering] = useState(false);

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setPageNumber(1);
  };

  const goToPrev = () => setPageNumber((p) => Math.max(1, p - 1));
  const goToNext = () => setPageNumber((p) => Math.min(numPages, p + 1));
  const zoomIn = () => setScale((s) => Math.min(2.5, parseFloat((s + 0.2).toFixed(1))));
  const zoomOut = () => setScale((s) => Math.max(0.4, parseFloat((s - 0.2).toFixed(1))));
  const resetZoom = () => setScale(1.0);

  const handleDownload = async () => {
    if (!fileUrl) return;
    let blobUrl: string;
    let tempBlob = false;
    if (fileUrl.startsWith('blob:')) {
      blobUrl = fileUrl;
    } else {
      const response = await fetch(fileUrl);
      const blob = await response.blob();
      blobUrl = URL.createObjectURL(blob);
      tempBlob = true;
    }
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    if (tempBlob) URL.revokeObjectURL(blobUrl);
  };

  if (!fileUrl) {
    return (
      <div className="pdf-shell pdf-shell--center">
        <p className="pdf-empty">Document will load when task data is available.</p>
      </div>
    );
  }

  return (
    <div className="pdf-shell">
      <div className="pdf-toolbar">
        <div className="pdf-toolbar__group">
          <button className="pdf-btn" onClick={goToPrev} disabled={pageNumber <= 1} title="Previous page">‹</button>
          <span className="pdf-page-info">
            <span className="pdf-page-info__current">{pageNumber}</span>
            <span className="pdf-page-info__sep">/</span>
            <span className="pdf-page-info__total">{numPages}</span>
          </span>
          <button className="pdf-btn" onClick={goToNext} disabled={pageNumber >= numPages} title="Next page">›</button>
        </div>
        <div className="pdf-toolbar__group">
          <button className="pdf-btn" onClick={zoomOut} disabled={scale <= 0.4} title="Zoom out">−</button>
          <button className="pdf-btn pdf-btn--zoom-label" onClick={resetZoom} title="Reset zoom">
            {Math.round(scale * 100)}%
          </button>
          <button className="pdf-btn" onClick={zoomIn} disabled={scale >= 2.5} title="Zoom in">+</button>
        </div>
        <div className="pdf-toolbar__group">
          <button className="pdf-btn pdf-btn--download" onClick={handleDownload} title="Download PDF">
            ⬇ Download
          </button>
        </div>
      </div>
      <div className="pdf-viewport">
        <Document
          file={fileUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={<div className="pdf-page-loading">Loading…</div>}
          error={<div className="pdf-page-error">Failed to load PDF.</div>}
        >
          <Page
            pageNumber={pageNumber}
            scale={scale}
            onRenderSuccess={() => setPageRendering(false)}
            onRenderError={() => setPageRendering(false)}
            loading={<div className="pdf-page-loading">Rendering page…</div>}
            className={`pdf-page${pageRendering ? ' pdf-page--rendering' : ''}`}
          />
        </Document>
      </div>
    </div>
  );
}
```

---

## `src/components/DocumentTab.css`

**Copy [`action-app/document-tab-template.css`](action-app/document-tab-template.css) verbatim to `src/components/DocumentTab.css`** (only when the app shows a document). Styles the PDF shell, toolbar, paging/zoom buttons, and viewport on the `index.css` tokens.
