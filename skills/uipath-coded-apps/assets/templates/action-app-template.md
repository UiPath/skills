# Action App File Templates

Complete, copy-paste scaffold for a new UiPath Coded Action App (React + TypeScript). This is the **default inspiring layout** for the skill: a design-system `index.css` (light/dark tokens), an `app-shell` wrapper, and a `Form` with an animated gradient header, sectioned cards, and a sticky outcome footer.

> **How to use this template.** Treat it as the visual + structural baseline. Keep the design system, the header/section/sticky-footer structure, the dark-theme handling, and the animations. **Adapt the schema-specific parts** — the `FormData` interface, default values, field labels, sections, number/currency formatting, and outcome buttons — to the confirmed `action-schema.json`. **Customer instructions (Q5 layout/style) always win** — layer their requested colours, layout, copy, and structure on top of this baseline; only fall back to the baseline where they gave no direction.

> **The default `Form` is form-only — no document/PDF tab.** Only add the optional `DocumentTab` (last two sections) when the use case requires showing a document, per the PDF viewer step in [../../references/create-action-app.md](../../references/create-action-app.md). Do not wire it in by default.

> The `Form.tsx` / `Form.css` below are shown for a loan-review example (inputs: applicant name, loan amount, credit score; outputs: risk score, reviewer comments; outcomes: Approve / Reject). Swap those specifics for the real schema; preserve the structure and styling.

---

## `src/index.css`

Design system: CSS variables for light + dark, fonts, accent gradient palette, shadows, radii. Required — every component below references these tokens. Write it verbatim (adjust the accent palette if the customer asked for a different brand colour).

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

:root {
  /* Surfaces */
  --bg-canvas: #eef3fb;
  --bg-card: #ffffff;
  --bg-hover: #eff5ff;
  --bg-input: #f8fafc;
  --bg-primary: #ffffff;
  --bg-secondary: #f1f6fe;

  /* Text */
  --text-primary: #0f1f3d;
  --text-secondary: #51607a;
  --text-muted: #8a97ad;

  /* Borders */
  --border-color: #dbe5f5;
  --border-strong: #b8c8e6;
  --border-focus: #2563eb;

  /* Accent (blue) */
  --accent-color: #2563eb;
  --accent-hover: #1d4ed8;
  --accent-soft: #3b82f6;
  --accent-cyan: #06b6d4;
  --accent-text: #ffffff;
  --accent-bg: rgba(37, 99, 235, 0.1);
  --accent-grad: linear-gradient(135deg, #3b82f6 0%, #2563eb 50%, #1e40af 100%);
  --accent-grad-vivid: linear-gradient(120deg, #06b6d4 0%, #3b82f6 45%, #1e40af 100%);

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(15, 31, 61, 0.06);
  --shadow-md: 0 8px 24px rgba(37, 99, 235, 0.1);
  --shadow-lg: 0 18px 48px rgba(30, 64, 175, 0.18);
  --shadow-accent: 0 8px 20px rgba(37, 99, 235, 0.35);

  /* Radius */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 18px;

  --sans: 'Inter', system-ui, 'Segoe UI', Roboto, sans-serif;
  --heading: 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif;

  font-family: var(--sans);
  color-scheme: light dark;
  color: var(--text-primary);
  background: var(--bg-canvas);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body.dark,
.dark {
  --bg-canvas: #0a1124;
  --bg-card: #111a33;
  --bg-hover: #1a2647;
  --bg-input: #16213f;
  --bg-primary: #111a33;
  --bg-secondary: #0d1530;

  --text-primary: #eaf1ff;
  --text-secondary: #a9b7d4;
  --text-muted: #6f7ea0;

  --border-color: #25335c;
  --border-strong: #3a4d80;
  --border-focus: #60a5fa;

  --accent-color: #3b82f6;
  --accent-hover: #60a5fa;
  --accent-soft: #60a5fa;
  --accent-cyan: #22d3ee;
  --accent-text: #ffffff;
  --accent-bg: rgba(59, 130, 246, 0.18);

  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.4);
  --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.5);
  --shadow-lg: 0 18px 48px rgba(0, 0, 0, 0.6);
  --shadow-accent: 0 8px 22px rgba(37, 99, 235, 0.5);
}

* {
  box-sizing: border-box;
}

html,
body,
#root {
  margin: 0;
  padding: 0;
  width: 100%;
  min-height: 100vh;
}

body {
  background: var(--bg-canvas);
  color: var(--text-primary);
  transition: background 0.3s ease, color 0.3s ease;
}

#root {
  display: flex;
  flex-direction: column;
}

h1,
h2 {
  font-family: var(--heading);
}
```

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

```css
.app-shell {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-canvas);
  color: var(--text-primary);
  transition: background 0.3s ease, color 0.3s ease;
}
```

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

```css
/* ===== Full-width review workspace ===== */
.review-app {
  width: 100%;
  max-width: 1320px;
  margin: 0 auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 1.75rem 2rem 0;
  gap: 1.5rem;
  text-align: left;
  box-sizing: border-box;
}

/* ===== Header banner (gradient) ===== */
.review-header {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 1.1rem;
  padding: 1.6rem 1.9rem;
  border-radius: var(--radius-lg);
  background: var(--accent-grad-vivid);
  background-size: 220% 220%;
  color: #fff;
  box-shadow: var(--shadow-accent);
  animation: fade-slide-down 0.5s ease both,
    gradient-shift 9s ease-in-out infinite;
}

/* decorative glow */
.review-header::after {
  content: '';
  position: absolute;
  top: -60%;
  right: -5%;
  width: 280px;
  height: 280px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.25), transparent 70%);
  pointer-events: none;
  animation: glow-float 7s ease-in-out infinite;
}

/* shine sweep */
.review-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: -60%;
  width: 45%;
  height: 100%;
  background: linear-gradient(
    100deg,
    transparent,
    rgba(255, 255, 255, 0.18),
    transparent
  );
  transform: skewX(-18deg);
  pointer-events: none;
  animation: shine-sweep 6s ease-in-out 1.2s infinite;
}

.review-header__icon {
  flex-shrink: 0;
  width: 52px;
  height: 52px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #fff;
  backdrop-filter: blur(4px);
  animation: pop-in 0.5s 0.1s ease both;
}

.review-header__titles {
  position: relative;
  z-index: 1;
}

.review-header__title {
  font-family: var(--heading);
  font-size: 1.7rem;
  font-weight: 800;
  margin: 0;
  color: #fff;
  letter-spacing: -0.02em;
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.12);
}

.review-header__subtitle {
  margin: 0.3rem 0 0;
  font-size: 0.92rem;
  color: rgba(255, 255, 255, 0.88);
}

.review-header__actions {
  position: relative;
  z-index: 1;
  margin-left: auto;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.review-badge {
  flex-shrink: 0;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #fff;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.35);
  padding: 0.32rem 0.7rem;
  border-radius: 999px;
}

/* dark-mode toggle (top-right of the header) */
.theme-toggle {
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: #fff;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.32);
  cursor: pointer;
  backdrop-filter: blur(4px);
  transition: background 0.2s ease, transform 0.15s ease;
}

.theme-toggle:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.theme-toggle:active {
  transform: translateY(0);
}

.theme-toggle:focus-visible {
  outline: 2px solid #fff;
  outline-offset: 2px;
}

/* ===== Form card ===== */
.form-container {
  flex: 1;
  min-height: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: 2rem 2.1rem;
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}

.form-container--enter {
  animation: panel-enter 0.42s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.form-section {
  position: relative;
  padding: 1.4rem 1.5rem;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: linear-gradient(180deg, var(--bg-secondary), var(--bg-card) 60%);
  transition: box-shadow 0.25s ease, transform 0.25s ease;
}

.form-section:hover {
  box-shadow: var(--shadow-md);
}

.form-title {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-family: var(--heading);
  font-size: 1.12rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 1.2rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border-color);
}

/* accent bar before each section title */
.form-title::before {
  content: '';
  width: 5px;
  height: 1.15rem;
  border-radius: 999px;
  background: var(--accent-grad);
  flex-shrink: 0;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.2rem;
  margin-bottom: 0.5rem;
}

/* extra breathing room before a stacked field (e.g. Reviewer Comments) */
.form-group--spaced {
  margin-top: 1.5rem;
}

/* required-field marker */
.req {
  color: #ef4444;
  font-weight: 700;
  margin-left: 0.15rem;
}

.dark .req {
  color: #f87171;
}

.form-group {
  display: flex;
  flex-direction: column;
  margin-bottom: 1.1rem;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  margin-bottom: 0.4rem;
}

.form-group input,
.form-group textarea {
  width: 100%;
  background: var(--bg-input);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 0.65rem 0.85rem;
  color: var(--text-primary);
  font-size: 0.92rem;
  font-family: inherit;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
  box-sizing: border-box;
  resize: vertical;
}

.form-group input::placeholder,
.form-group textarea::placeholder {
  color: var(--text-muted);
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  background: var(--bg-card);
  border-color: var(--border-focus);
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.16);
}

.form-group input[readonly],
.form-group textarea[readonly] {
  background: var(--bg-hover);
  color: var(--text-secondary);
  border-color: var(--border-color);
  border-style: dashed;
  cursor: default;
}

.form-group input[readonly]:focus,
.form-group textarea[readonly]:focus {
  box-shadow: none;
  border-color: var(--border-color);
}

/* ===== Outcome buttons (sticky footer) ===== */
.form-buttons {
  position: sticky;
  bottom: 0;
  display: flex;
  justify-content: flex-end;
  gap: 0.85rem;
  padding: 1.1rem 0;
  margin-top: auto;
  border-top: 1px solid var(--border-color);
  background: linear-gradient(180deg, transparent, var(--bg-canvas) 35%);
}

.outcome-btn {
  padding: 0.65rem 1.9rem;
  border-radius: var(--radius-sm);
  font-family: var(--sans);
  font-weight: 700;
  font-size: 0.9rem;
  letter-spacing: 0.01em;
  cursor: pointer;
  transition: transform 0.15s ease, background 0.2s ease, box-shadow 0.2s ease,
    opacity 0.2s ease, color 0.2s ease;
}

.outcome-btn:not(:disabled):hover {
  transform: translateY(-2px);
}

.outcome-btn:not(:disabled):active {
  transform: translateY(0);
}

.outcome-btn--primary {
  background: var(--accent-grad);
  color: var(--accent-text);
  border: none;
  box-shadow: var(--shadow-accent);
}

.outcome-btn--primary:not(:disabled):hover {
  box-shadow: 0 12px 28px rgba(37, 99, 235, 0.45);
}

.outcome-btn--secondary {
  background: var(--bg-card);
  border: 1.5px solid var(--border-strong);
  color: var(--text-primary);
}

.outcome-btn--secondary:not(:disabled):hover {
  background: var(--bg-hover);
  border-color: var(--accent-soft);
  color: var(--accent-color);
}

.outcome-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* ===== Animations ===== */
@keyframes fade-slide-down {
  from {
    opacity: 0;
    transform: translateY(-12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pop-in {
  from {
    opacity: 0;
    transform: scale(0.7);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes panel-enter {
  from {
    opacity: 0;
    transform: translateY(12px) scale(0.99);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes gradient-shift {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

@keyframes glow-float {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
    opacity: 0.8;
  }
  50% {
    transform: translate(-18px, 14px) scale(1.15);
    opacity: 1;
  }
}

@keyframes shine-sweep {
  0% {
    left: -60%;
  }
  60%,
  100% {
    left: 130%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .review-header,
  .review-header::after,
  .review-header::before,
  .form-container--enter {
    animation: none !important;
  }
}

@media (max-width: 720px) {
  .review-app {
    padding: 1rem 1rem 0;
  }
  .form-container {
    padding: 1.25rem;
  }
  .review-header {
    padding: 1.25rem 1.3rem;
  }
  .review-header__title {
    font-size: 1.4rem;
  }
}
```

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

```css
.pdf-shell {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 60vh;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-md);
}

.pdf-shell--center {
  align-items: center;
  justify-content: center;
}

.pdf-toolbar {
  position: sticky;
  top: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  padding: 0.5rem 0.75rem;
}

.pdf-toolbar__group {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.pdf-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  height: 2rem;
  padding: 0 0.6rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  color: var(--text-primary);
  font-size: 1rem;
  line-height: 1;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease, transform 0.1s ease;
}

.pdf-btn:not(:disabled):hover {
  background: var(--bg-hover);
  border-color: var(--border-strong);
}

.pdf-btn:not(:disabled):active {
  transform: scale(0.96);
}

.pdf-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.pdf-btn--zoom-label {
  min-width: 3.5rem;
  font-size: 0.8rem;
  font-variant-numeric: tabular-nums;
}

.pdf-btn--download {
  gap: 0.35rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--accent-color);
  border-color: var(--accent-color);
}

.pdf-btn--download:not(:disabled):hover {
  background: var(--accent-bg);
}

.pdf-page-info {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.85rem;
  color: var(--text-secondary);
  padding: 0 0.4rem;
  font-variant-numeric: tabular-nums;
}

.pdf-page-info__current {
  color: var(--text-primary);
  font-weight: 600;
}

.pdf-viewport {
  flex: 1;
  overflow-y: auto;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 1.5rem;
}

.pdf-page {
  box-shadow: var(--shadow-lg);
  border-radius: var(--radius-sm);
  overflow: hidden;
  transition: opacity 0.2s ease;
}

.pdf-page--rendering {
  opacity: 0.6;
}

.pdf-page-loading,
.pdf-page-error {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.pdf-page-error {
  color: #b91c1c;
}

.pdf-empty {
  color: var(--text-muted);
  font-size: 0.9rem;
}
```
