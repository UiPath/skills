# Create a UiPath Coded Action App

Scaffold a production-ready UiPath Coded Action App — a React form component rendered inside UiPath Action Center as part of a Maestro or Agent automation workflow.

## What Is a Coded Action App?

When an automation creates a human task (via `CreateFormTask` or similar), the assigned action app is rendered in Action Center for the reviewer. The app:
- Receives input data from the automation (read-only)
- Collects output data from the reviewer (editable)
- Submits with an outcome button (e.g., Approve, Reject)

The data contract is defined in `action-schema.json`.

---

## Pre-flight: Collect Required Information

Ask these questions **one at a time, in order**. Do not start writing files until all answers are collected.

### Q1 — App name
> "What is the name of your action app? This will be the project folder name (e.g., `loan-review-app`)."

Convert to lowercase kebab-case. Store as `<app-name>`.

### Q2 — Routing name
> "What routing name should this app use in Action Center? This becomes the URL path (e.g., `loan-review`). Lowercase letters, digits, and hyphens only. 4–32 characters."

Auto-convert spaces/underscores to hyphens and uppercase to lowercase. Validate the pattern and length. Confirm the final value. Store as `<routing-name>`.

### Q3 — SDK services (optional)

From the user's **request**, determine whether the app needs to call UiPath platform services (Data Fabric, Orchestrator, Buckets, etc.). Do **not** ask the user to pick from a list.

If services are needed: read [oauth-scopes.md](oauth-scopes.md) to determine the required scopes, then proceed to Q3a.

If no platform services are apparent from the request: skip to Q4. No SDK setup needed beyond `@uipath/uipath-ts-coded-action-apps`.

After deducing scopes, present them to the user:
> "Based on your request, the required OAuth scopes are: `<scopes>`. Reply ok to use these, or tell me what to change."

### Q3a — Environment (only if SDK needed)

Ask:
> "Which UiPath environment are you targeting? `cloud` (production), `staging`, or `alpha`?"

Map the answer to the cloud host:

| Environment | Cloud Host |
|---|---|
| cloud | `https://cloud.uipath.com` |
| staging | `https://staging.uipath.com` |
| alpha | `https://alpha.uipath.com` |

Store the cloud host as `<cloud-host>`. This value is used to build the redirect URI in Q3b — **do not** skip this step and default to `https://cloud.uipath.com`, or staging/alpha users will register a redirect URI that never matches at runtime.

### Q3b — Client ID (only if SDK needed)

Ask:
> "Do you have an existing OAuth External Application client ID?
> It needs these scopes: `<deduced-scopes>` and this redirect URI: `<cloud-host>/<orgName>/<tenantName>/actions_`
>
> - If yes, paste it
> - If no, say **"create one"** and I'll set it up via browser automation"

**If the user says "create one":** Follow [oauth-client-setup.md Step 2 (Setup B)](oauth-client-setup.md#step-2-ensure-playwright-is-available) to install Playwright into `~/.uipath-skills/playwright/`. Do **not** install into the user's app (`npm install -D playwright` adds ~300MB to devDependencies for a tool that runs once or twice).

Then read [oauth-client-setup.md](oauth-client-setup.md) and follow it to create the External Application with the scopes above and redirect URI `<cloud-host>/<orgName>/<tenantName>/actions_` — pass `<cloud-host>` as `--cloud-host` to the script.

Store the resulting client ID as `<client-id>`.

### Q4 — Action schema

Collect the data contract for this app. Ask field-by-field.

#### Q4a — Input fields
> "How many INPUT fields does this form have? (Read-only data passed in from the automation — e.g., applicant name, loan amount.) Enter 0 if none."

For each input field, collect: **name** (camelCase), **type** (`string` / `number` / `integer` / `boolean` / `array` / `object`), **required** (yes/no), optional **description**, and if type is `array` the items type.

#### Q4b — Output fields
> "How many OUTPUT fields does this form have? (Fields the reviewer fills in — e.g., review notes, risk rating.) Enter 0 if none."

Same sub-questions as Q4a.

#### Q4c — InOut fields
> "How many INOUT fields does this form have? (Pre-populated but editable by the reviewer.) Enter 0 if none."

Same sub-questions.

#### Q4d — Outcomes
> "What are the outcome buttons for this task? Enter comma-separated names (e.g., `Approve, Reject, Escalate`)."

#### Q4e — Hidden fields (optional)
> "Are there any fields that should NOT be shown as form inputs (e.g., internal IDs passed silently)? If yes, list names comma-separated. Press Enter to skip."

Hidden fields are included in `action-schema.json` and in the `FormData` interface but omitted from the JSX.

#### Confirm the schema
Show the complete `action-schema.json` to the user and ask:
> "Does this look correct? Reply ok to generate the project, or tell me what to change."

### Q5 — Form layout (optional)
> "Describe the form's layout and style — purpose, visual arrangement, colour preferences. Press Enter for a clean default layout."

---

## Project Scaffolding

After collecting all answers, scaffold the project. Use the file templates in [assets/templates/action-app-template.md](../assets/templates/action-app-template.md) as starting points for all generated files.

```bash
npm create vite@latest <app-name> -- --template react-ts
cd <app-name>
npm install @uipath/uipath-ts-coded-action-apps --@uipath:registry=https://registry.npmjs.org
npm install
```

If SDK services are needed:
```bash
npm install @uipath/uipath-typescript --@uipath:registry=https://registry.npmjs.org
```

> **Why the registry flag?** Users may have `@uipath` scoped to GitHub Packages in their `.npmrc`, which requires authentication and causes a 401. The flag forces these packages to install from the public npm registry.

---

## Generated Files

### `action-schema.json`

Write to the project root. All four sections are always present — use `"properties": {}` for empty sections.

```json
{
  "inputs": {
    "type": "object",
    "properties": {
      "applicantName": { "type": "string", "required": true, "description": "Full name" },
      "loanAmount":    { "type": "number", "required": false },
      "documentIds":   { "type": "array",  "required": false, "items": { "type": "string" } }
    }
  },
  "outputs": {
    "type": "object",
    "properties": {
      "reviewerNotes": { "type": "string",  "required": false },
      "riskScore":     { "type": "integer", "required": true }
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

**TypeScript ↔ JSON schema type mapping:**

| Schema type | TypeScript type | Initial value |
|-------------|-----------------|---------------|
| `string` | `string` | `''` |
| `number` | `number` | `0` |
| `integer` | `number` | `0` |
| `boolean` | `boolean` | `false` |
| `array` | `ItemType[]` | `[]` |
| `object` | `Record<string, unknown>` | `{}` |

---

### `src/uipath.ts`

Without SDK services:
```typescript
import { CodedActionAppsService } from '@uipath/uipath-ts-coded-action-apps';

export const codedActionAppsService = new CodedActionAppsService();
```

With SDK services:
```typescript
import { UiPath } from '@uipath/uipath-typescript/core';
import { Entities } from '@uipath/uipath-typescript/entities';  // example
import { CodedActionAppsService } from '@uipath/uipath-ts-coded-action-apps';

const sdk = new UiPath();
export const codedActionAppsService = new CodedActionAppsService();
export const entities = new Entities(sdk);  // example
```

---

### `src/App.tsx`

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

### `src/components/Form.tsx`

Generate based on the collected schema. Key patterns:

```typescript
import { useState, useEffect, ChangeEvent } from 'react';
import { Theme } from '@uipath/uipath-ts-coded-action-apps';
import { codedActionAppsService } from '../uipath';
import './Form.css';

// Generate from schema — one property per field across all sections
interface FormData {
  applicantName: string;   // input
  loanAmount: number;      // input
  reviewerNotes: string;   // output
  riskScore: number;       // output
}

const isDarkTheme = (theme: Theme) =>
  theme === Theme.Dark || theme === Theme.DarkHighContrast;

interface FormProps {
  onInitTheme: (isDark: boolean) => void;
}

function Form({ onInitTheme }: FormProps) {
  const [formData, setFormData] = useState<FormData>({
    applicantName: '', loanAmount: 0,
    reviewerNotes: '', riskScore: 0,
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

  // isFormValid: false when read-only OR when required output/inout fields are empty
  const isFormValid = !isReadOnly && Boolean(formData.riskScore);

  // One async handler per outcome
  const handleApprove = async () =>
    codedActionAppsService.completeTask('Approve', formData);
  const handleReject = async () =>
    codedActionAppsService.completeTask('Reject', formData);

  return (
    <form className="action-form">
      {/* Input fields — always readOnly */}
      <label>Applicant Name
        <input readOnly value={formData.applicantName} />
      </label>

      {/* Output fields — editable unless isReadOnly */}
      <label>Review Notes
        <textarea
          name="reviewerNotes"
          value={formData.reviewerNotes}
          onChange={handleChange}
          readOnly={isReadOnly}
        />
      </label>

      {/* Outcome buttons — disabled when form is invalid */}
      <div className="actions">
        <button type="button" onClick={handleApprove} disabled={!isFormValid}>Approve</button>
        <button type="button" onClick={handleReject} disabled={!isFormValid}>Reject</button>
      </div>
    </form>
  );
}

export default Form;
```

**Rendering rules:**
- `inputs` fields → `readOnly` always
- `outputs` fields → editable, `readOnly={isReadOnly}`
- `inOuts` fields → editable, `readOnly={isReadOnly}`
- Hidden fields (from Q4e) → omit from JSX entirely, but keep in `FormData` interface and initial state

---

### `vite.config.ts`

`base: './'` is **always required** — the platform handles URL routing at runtime:

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: './',
});
```

---

## Deploy Action App

```bash
npm run build
uip codedapp pack dist -n <app-name> -v 1.0.0
uip codedapp publish -t Action        # -t Action is required
uip codedapp deploy
```

See [pack-publish-deploy.md](pack-publish-deploy.md) for full deployment options.
