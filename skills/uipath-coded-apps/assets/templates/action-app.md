# Action App File Templates

Ready-to-use boilerplate for a new UiPath Coded Action App (React + TypeScript). Replace `{{PLACEHOLDER}}` values with project-specific content.

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

Field types: `string` · `number` · `integer` · `boolean` · `array` (add `"items": {"type": "..."}`) · `object` (add `"properties": {...}`)

---

## `src/uipath.ts`

Without SDK services:

```typescript
import { CodedActionAppsService } from '@uipath/uipath-ts-coded-action-apps';

export const codedActionAppsService = new CodedActionAppsService();
```

With SDK services (add only what the app uses):

```typescript
import { UiPath } from '@uipath/uipath-typescript/core';
// import { Entities } from '@uipath/uipath-typescript/entities';
import { CodedActionAppsService } from '@uipath/uipath-ts-coded-action-apps';

const sdk = new UiPath();
export const codedActionAppsService = new CodedActionAppsService();
// export const entities = new Entities(sdk);
```

---

## `src/App.tsx`

```typescript
import { useState, useCallback } from 'react';
import Form from './components/Form';

function App() {
  const [darkTheme, setDarkTheme] = useState(false);

  const handleInitTheme = useCallback((isDark: boolean) => {
    setDarkTheme(isDark);
    document.body.className = isDark ? 'dark' : 'light';
  }, []);

  return (
    <div className={darkTheme ? 'dark' : 'light'}>
      <Form onInitTheme={handleInitTheme} />
    </div>
  );
}

export default App;
```

---

## `src/components/Form.tsx`

Replace `{{...}}` placeholders with fields from `action-schema.json`. Remove sections/fields not present in the schema.

```typescript
import { useState, useEffect, ChangeEvent } from 'react';
import { Theme } from '@uipath/uipath-ts-coded-action-apps';
import { codedActionAppsService } from '../uipath';
import './Form.css';

// One property per field across all schema sections (inputs, outputs, inOuts)
interface FormData {
  {{INPUT_FIELD}}: string;    // input — read-only in form
  {{OUTPUT_FIELD}}: string;   // output — editable
  // {{INOUT_FIELD}}: string; // inOut — pre-populated, editable
}

const isDarkTheme = (theme: Theme) =>
  theme === Theme.Dark || theme === Theme.DarkHighContrast;

interface FormProps {
  onInitTheme: (isDark: boolean) => void;
}

function Form({ onInitTheme }: FormProps) {
  const [formData, setFormData] = useState<FormData>({
    {{INPUT_FIELD}}: '',
    {{OUTPUT_FIELD}}: '',
  });
  const [isReadOnly, setIsReadOnly] = useState(false);

  useEffect(() => {
    codedActionAppsService.getTask().then((task) => {
      if (task.data) setFormData(task.data as FormData);
      setIsReadOnly(task.isReadOnly);
      onInitTheme(isDarkTheme(task.theme));
    });
  }, [onInitTheme]);

  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    if (isReadOnly) return;
    const { name, value } = e.target;
    const updated = { ...formData, [name]: value };
    setFormData(updated);
    codedActionAppsService.setTaskData(updated);
  };

  // false when read-only OR when required output/inOut fields are empty
  const isFormValid = !isReadOnly && Boolean(formData.{{REQUIRED_OUTPUT_FIELD}});

  // One async handler per outcome
  const handleApprove = async () =>
    codedActionAppsService.completeTask('Approve', formData);
  const handleReject = async () =>
    codedActionAppsService.completeTask('Reject', formData);

  return (
    <form className="action-form">
      {/* Input fields — always readOnly */}
      <label>{{INPUT_LABEL}}
        <input readOnly value={formData.{{INPUT_FIELD}}} />
      </label>

      {/* Output / InOut fields — editable */}
      <label>{{OUTPUT_LABEL}}
        <input
          name="{{OUTPUT_FIELD}}"
          value={formData.{{OUTPUT_FIELD}}}
          onChange={handleChange}
          readOnly={isReadOnly}
        />
      </label>

      {/* Outcome buttons */}
      <div className="form-actions">
        <button type="button" onClick={handleApprove} disabled={!isFormValid}>
          Approve
        </button>
        <button type="button" onClick={handleReject} disabled={!isFormValid}>
          Reject
        </button>
      </div>
    </form>
  );
}

export default Form;
```

---

## `src/components/Form.css`

```css
.action-form {
  max-width: 640px;
  margin: 2rem auto;
  padding: 2rem;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.action-form label {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.action-form input,
.action-form textarea {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9rem;
  background: #fff;
}

.action-form input[readonly],
.action-form textarea[readonly] {
  background: #f9fafb;
  color: #6b7280;
  cursor: default;
}

.form-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  margin-top: 0.5rem;
}

.form-actions button {
  padding: 0.5rem 1.25rem;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
}

.form-actions button:first-child {
  background: #fa4616;
  color: #fff;
}

.form-actions button:last-child {
  background: #f3f4f6;
  color: #374151;
}

.form-actions button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Dark theme */
.dark .action-form {
  background: #1f2937;
  color: #f9fafb;
}

.dark .action-form label { color: #d1d5db; }

.dark .action-form input,
.dark .action-form textarea {
  background: #374151;
  border-color: #4b5563;
  color: #f9fafb;
}

.dark .action-form input[readonly],
.dark .action-form textarea[readonly] {
  background: #111827;
  color: #9ca3af;
}

.dark .form-actions button:last-child {
  background: #374151;
  color: #f9fafb;
}
```
