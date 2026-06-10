# Create a UiPath Coded Action App

Scaffold a production-ready UiPath Coded Action App — a React form component rendered inside UiPath Action Center as part of a Maestro or Agent automation workflow.

## What Is a Coded Action App?

When an automation creates a human task (via `CreateAppTask` RPA activity/Maestro `User Task`/Agent `Escalation`/Flow `HITL node`), the assigned action app is rendered in Action Center for the reviewer. The app:
- Receives input data from the automation (inputs are read-only)
- Collects inout and output data from the reviewer (inouts are pre-populated and editable and outputs are filled in by the reviewer)
- Submits with an outcome button (e.g., Approve, Reject)

The data contract is defined in `action-schema.json`.

---

## Pre-flight: Collect Required Information

Ask these questions **one at a time, in order**. Do not start writing files until all answers are collected.

### Q1 — App name
> "What is the name of your action app? This will be the project folder name and app url (e.g., `loan-review-app`)."

Convert to lowercase kebab-case. Store as `<app-name>`.

### Q2 — Use case

Ask:
> "What do you want this action app to do? Describe the use case — what the reviewer sees, what data it works with, and where that data comes from."

Store the description. **Do not deduce services yet** — that happens in Q4, after the action schema is defined. The schema (especially how documents/files are modelled) determines which services the app needs, so define the contract first.

### Q3 — Action schema

Collect the data contract for this app. Ask field-by-field. Do not generate files until the schema is confirmed.

#### Field types reference

The **authoritative** list of supported types/formats and structural rules lives in one place — the validator script [scripts/validate-action-schema.js](../scripts/validate-action-schema.js), which mirrors the UiPath CLI's own schema validator. Run `node scripts/validate-action-schema.js --show-types` for the current type list. The table below is a quick authoring summary; the validator is the source of truth.

| Type | Notes |
|------|-------|
| `string` | Optional `format: "uuid"` or `format: "date"` (`format` is allowed on `string` only) |
| `number` | Floating-point |
| `integer` | Whole numbers only |
| `boolean` | `true` / `false` |
| `array` | Must specify `items` (element type). Nested arrays not supported |
| `object` | Must specify nested `properties` (record of further fields, each following the same rules) |
| `file` | A file reference from the automation. In task data the field's value is an **object whose root member is `ID`** (the attachment id), i.e. `formData.<field>.ID`. Fetch the file with the TypeScript SDK `AttachmentsService.getById(formData.<field>.ID)` |

Every field also supports an optional `description` string.

For each field collect: **name** (camelCase), **type**, **required** (yes/no), optional **description**, optional **format** (if type=`string`), the **items type** if type=`array`, and the nested **properties** if type=`object`.

#### Q3-doc — Document / file handling (whenever the use case involves a file, document, or storage bucket)

If the use case (Q2) involves **any** file, document, or attachment — displaying it, downloading it, or otherwise handling it — **ask explicitly how the file reaches the app — do not assume.**

> **Critical — "from a storage bucket" is NOT a decision.** A request like *"load a PDF from a storage bucket"* does **not** mean the user chose the bucket-reference path. **Both** options below use storage buckets internally — a direct **file input** uses an *internal* storage bucket that is hidden from the user (the SDK manages it via Attachments), while a **filePath input** points at an *existing* file in a bucket the user manages. Because the phrasing is ambiguous, you MUST clarify every time; never let the words "storage bucket" short-circuit the question.

Ask:

> "How does the file reach this app — both use storage buckets under the hood, so I need to know which:
> 1. **Direct file input** — the automation hands the file input to the task.
> 2. **File path (string) input** — you pass the path/name of a file that already lives in a Storage Bucket you manage, and the app reads it from there.
> 3. **Data Fabric attachment** — the file is an attachment on a Data Fabric entity record."

Construct the schema field according to the answer:

| Answer | Schema field(s) | Services implied (feed Q4) | How the file is fetched |
|--------|-----------------|----------------------------|-------------------------|
| Direct file input | one `type: "file"` field — a file reference from the automation (has an ID in task data) | Attachments | `AttachmentsService.getById()` (TypeScript SDK) |
| File path (string) input | one `type: "string"` field for the file path (plus a `string` for bucket name if not fixed) | Buckets | `bucketService.getReadUri()` — see the PDF viewer step |
| Data Fabric attachment | a `type: "file"` field, or a `string` attachment id per the entity field | Entities (Data Fabric) + Attachments | Data Fabric entity record → attachment |

Record the implied services — they are inputs to the Q4 deduction.

#### Q3a — Input fields
> "How many INPUT fields does this form have? (Read-only data passed in from the automation — e.g., applicant name, loan amount.) Enter 0 if none."

For each input field ask:
> "Input field [N]:
> - Name (camelCase):
> - Type (`string` / `number` / `integer` / `boolean` / `array` / `object` / `file`):
> - Required? (`yes` / `no`):
> - Description (optional, press Enter to skip):
> - *(if type=`string`)* Format? (`uuid` / `date` / none):
> - *(if type=`array`)* Items type (cannot be `array`):
> - *(if type=`object`)* Define nested properties now? (describe them one by one):"

#### Q3b — Output fields
> "How many OUTPUT fields does this form have? (Fields the reviewer fills in — e.g., review notes, risk rating.) Enter 0 if none."

Same sub-questions as Q3a.

#### Q3c — InOut fields
> "How many INOUT fields does this form have? (Pre-populated but editable by the reviewer.) Enter 0 if none."

Same sub-questions as Q3a.

#### Q3d — Outcomes
> "What are the outcome buttons for this task? Enter comma-separated names (e.g., `Approve, Reject, Escalate`)."

Each outcome becomes a `string`-typed property in the `outcomes` section.

#### Q3e — Hidden fields
> "Are there any fields that should NOT be shown as form inputs (e.g., internal IDs passed silently)? If yes, list names comma-separated. Press Enter to skip."

Hidden fields are included in `action-schema.json` and in the `FormData` interface but omitted from the JSX which is rendered.

#### Validate the schema (required before proposing it)

Before showing the schema to the user, **validate it** with the schema validator — the single source of truth for what is and isn't supported:

```bash
node <skill-dir>/scripts/validate-action-schema.js <path-to-action-schema.json>
# or pipe it:  echo '<schema-json>' | node <skill-dir>/scripts/validate-action-schema.js -
```

Exit `0` = valid. On exit `1`, fix every reported `path: message` (it flags unsupported types, `format` on non-`string`, missing `items` on arrays, nested arrays, missing/malformed sections) and re-run until it passes. Never propose or write an `action-schema.json` that has not passed the validator.

#### Confirm the schema
Once it validates, show the complete `action-schema.json` and explain the structure:
- All four sections (`inputs`, `outputs`, `inOuts`, `outcomes`) always present — use `"properties": {}` for empty sections.
- Each section has `"type": "object"` and a `properties` map.
- `array` fields include an `items` object with its own `type`.
- `object` fields include a `properties` map of nested fields.
- `format` and `description` appear only when provided.

Ask:
> "Does this look correct? Reply ok to continue, or tell me what to change."

### Q4 — UiPath services & authentication

Now deduce whether the app needs UiPath platform services, using **both** the use case (Q2) **and** the confirmed action schema (Q3) — especially the document-handling choice. Do **not** ask the user to pick from a list — infer.

Treat the app as needing UiPath services if it references anything covered by the SDK reference files in this folder — e.g. Data Fabric / Entities / ChoiceSets, Storage Buckets, Orchestrator (Assets, Queues, Processes, Tasks), Maestro Processes / Instances / Incidents, Cases, or Conversational Agent. Reading or writing files, querying entity records, starting processes, fetching assets/queue items, or AI chat all imply SDK services. In addition, from Q3-doc:
- a `file`-typed field implies the **Attachments** service
- a storage-bucket file path implies **Buckets**
- a Data Fabric attachment implies **Entities + Attachments**

If the deduction surfaces **Storage Buckets** and Q3-doc was not already asked for that file, go back and ask the file-input-vs-bucket-reference question now — never assume a bucket reference without confirming.

**If you deduce one or more services:**
1. Read [oauth-scopes.md](oauth-scopes.md) to map the deduced services to their required scopes.
2. Confirm the services with the user before proceeding:
   > "Based on your use case and schema, this app needs these UiPath services: `<services>`, which require OAuth scopes: `<scopes>`. Reply ok to use these, or tell me what to change."
3. After confirmation, proceed to Q4a.

**If you cannot deduce any UiPath service**, confirm and skip to Q5:
> "I don't see any UiPath platform services needed here, so no External Application client ID is required. The app will use only `@uipath/coded-action-app`. Reply ok, or tell me if it does need to call a UiPath service."

#### Q4a — Environment (only if SDK needed)

Ask:
> "Which UiPath environment are you targeting? `cloud` (production), `staging`, or `alpha`?"

Map the answer to the cloud host:

| Environment | Cloud Host |
|---|---|
| cloud | `https://cloud.uipath.com` |
| staging | `https://staging.uipath.com` |
| alpha | `https://alpha.uipath.com` |

Store the cloud host as `<cloud-host>`. It tells the External-App creation step (Q4b) which org/environment portal to target — **do not** skip it and default to `https://cloud.uipath.com`, or staging/alpha users will create the External App in the wrong environment. It is also passed as the redirect URI in Q4b: the create form requires one, but an action app never performs a browser OAuth redirect, so the value is inert at runtime — it only needs to satisfy the mandatory field, not match anything.

#### Q4b — Client ID (only if SDK needed)

Ask:
> "Do you have an existing OAuth External Application client ID?
> It needs these scopes: `<deduced-scopes>`
>
> - If yes, paste it
> - If no, say **"create one"** and I'll set it up via browser automation"

**If the user says "create one":** Follow [oauth-client-setup.md Step 2 (Setup B)](oauth-client-setup.md#step-2-ensure-playwright-is-available) to install Playwright into `~/.uipath-skills/playwright/`. Do **not** install into the user's app (`npm install -D playwright` adds ~300MB to devDependencies for a tool that runs once or twice).

Then read [oauth-client-setup.md](oauth-client-setup.md) and follow it to create the External Application with the scopes above — pass `<cloud-host>` as `--cloud-host` **and** as `--redirects <cloud-host>`. The portal's create form requires at least one redirect URI, so pass `<cloud-host>` to satisfy it; the value is harmless and unused — an action app runs inside Action Center's iframe with a host-injected session and never performs a browser OAuth redirect (Critical Rule 17). The External App is needed only for its client ID and scopes (written to `uipath.json`).

Store the resulting client ID as `<client-id>`.

### Q5 — Form layout
> "Describe any layout or style preferences — visual arrangement, colour/brand, copy. Press Enter to use the polished default layout (gradient header, sectioned cards, sticky action footer, light/dark theme)."

Whatever the user provides here is layered **on top of** the default template layout and overrides it. If they press Enter, use the template as-is (adapted to the schema).

---

## Project Scaffolding

After collecting all answers, scaffold the project. **[assets/templates/action-app-template.md](../assets/templates/action-app-template.md) is the default inspiring layout** — build from it. It provides the complete baseline: the `src/index.css` design system (light/dark tokens, fonts, blue gradient accent), `src/App.tsx` + `src/App.css` (`app-shell`), `src/main.tsx`, `vite.config.ts`, `src/uipath.ts`, and a `Form.tsx` / `Form.css` with an animated gradient header, sectioned cards, and a sticky outcome footer.

> **Default layout rules:**
> 1. **Default `Form` is form-only — no document/PDF tab.** Only add the optional `DocumentTab` (PDF viewer step) when the use case requires showing a document.
> 2. **Adapt the schema-specific parts** — `FormData`, defaults, labels, sections, formatting, outcome buttons — to the confirmed `action-schema.json`.
> 3. **Customer instructions (Q5) always win.** Layer the user's requested colours, layout, copy, and structure on top of this baseline; fall back to the baseline only where they gave no direction.

The sections below describe the schema-driven adaptations; copy verbatim from the template for the parts they don't override (`index.css`, `App.css`, `main.tsx`, the design-system tokens, animations).

```bash
npm create vite@latest <app-name> -- --template react-ts
cd <app-name>
npm install @uipath/coded-action-app --@uipath:registry=https://registry.npmjs.org
npm install
```

If SDK services are needed:
```bash
npm install @uipath/uipath-typescript --@uipath:registry=https://registry.npmjs.org
```
---

## Generated Files

### `action-schema.json`

Write the confirmed schema (the one that passed [scripts/validate-action-schema.js](../scripts/validate-action-schema.js) in Q3) to the project root. Re-run the validator on the written file as a final check. Example:

```json
{
  "inputs": {
    "type": "object",
    "properties": {
      "applicantName": { "type": "string",  "required": true,  "description": "Full name" },
      "loanAmount":    { "type": "number",  "required": false },
      "applicationId": { "type": "string",  "required": true,  "format": "uuid" },
      "submittedAt":   { "type": "string",  "required": false, "format": "date" },
      "documentIds":   { "type": "array",   "required": false, "items": { "type": "string" } },
      "contract":      { "type": "file",    "required": false, "description": "Loan contract document" },
      "metadata":      {
        "type": "object", "required": false,
        "properties": {
          "source": { "type": "string", "required": false }
        }
      }
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
---

### `src/uipath.ts`

Copy the without-/with-SDK setup verbatim from the template's [`src/uipath.ts` section](../assets/templates/action-app-template.md). For the "with SDK services" variant, uncomment only the service exports the app uses (e.g. `Entities`, `Attachments`).

> **NEVER call `sdk.initialize()` in an action app** (Critical Rule 17). Construct `new UiPath()` (no args, no `.env`) and use it directly — Action Center's iframe injects the session at runtime. `sdk.initialize()` starts a PKCE OAuth redirect that only works in a standalone web app and breaks inside the iframe.

---

### `uipath.json` (only if SDK services are needed)

Write to the project root **only when SDK services are needed** (Q4 deduced one or more services). Project-root config consumed by the `uip codedapp` CLI for deployment. Substitute `<scopes>` (confirmed in Q4) and `<client-id>` (from Q4b). Keep it in sync if scopes or client ID change later.

```json
{
  "scope": "<scopes>",
  "clientId": "<client-id>"
}
```

Without SDK services there is no OAuth client, so **do not** write `uipath.json` — the app uses only `@uipath/coded-action-app` and needs no scopes or client ID.

---

### `src/index.css`, `src/App.css`, `src/main.tsx`

Copy verbatim from the template — these carry the design system (light/dark tokens, fonts, accent palette), the `app-shell` wrapper, and the Vite entry that imports `index.css`. Adjust only the accent palette if the customer asked for a different brand colour.

### `src/App.tsx`

Copy verbatim from the template's [`src/App.tsx` section](../assets/templates/action-app-template.md) — no schema-driven changes. It owns dark/light theme state and the `app-shell` wrapper: the task theme seeds it once via `onInitTheme`, the user flips it with the header toggle via `onToggleTheme`, and a single effect keeps `<body>` in sync for both paths.

---

### `src/components/Form.tsx`

Start from the template's `Form.tsx` (gradient header, sectioned cards, sticky footer, form-only by default) and adapt it to the schema using these rules:

**TypeScript `FormData` interface** — one property per field across all inputs, outputs, and inouts. Map schema types to TypeScript as follows:

| Schema type | TypeScript type | Initial value |
|-------------|-----------------|---------------|
| `string` | `string` | `''` |
| `number` | `number` | `0` |
| `integer` | `number` | `0` |
| `boolean` | `boolean` | `false` |
| `array` | `<itemsType>[]` (e.g. `string[]`) | `[]` |
| `object` | a named nested interface, or `Record<string, unknown>` | `{}` |
| `file` | `{ ID: string }` (the root `ID` member is the attachment id) | `{ ID: '' }` |

> For a `file` field, read the attachment id from the root `ID` member — `formData.<field>.ID` — and pass it to `AttachmentsService.getById()` to fetch the bytes. Do not treat the field value as a plain string or URL.

Collect these initial values into a `const defaultFormData: FormData = { ... }` (as in the template) — the task-initialisation merge below reuses it.

**Imports:**
- Without SDK services: `import { codedActionAppService } from '../uipath';`
- With SDK services: `import { codedActionAppService, <serviceInstance> } from '../uipath';` (add the named service exports the component uses, e.g. `entities`, `bucketService`)
- Always: `import { Theme } from '@uipath/coded-action-app';` (`MessageSeverity` is also exported from this package)

**Service accessor:** call `codedActionAppService.getTask()`, `.completeTask()`, `.setTaskData()`, `.showMessage()` directly. Call any SDK services via their named imports (e.g. `bucketService.getAll(...)`).

**Theme helper** (always include):
```typescript
const isDarkTheme = (theme: Theme): boolean =>
  theme === Theme.Dark || theme === Theme.DarkHighContrast;
```

**Theme toggle (always include).** `Form` takes `darkTheme: boolean` and `onToggleTheme: () => void` props from `App`. Render a `.theme-toggle` button in the header's top-right (inside `.review-header__actions`, alongside the read-only badge) that calls `onToggleTheme` and swaps a sun/moon icon based on `darkTheme`. The task theme seeds the initial mode via `onInitTheme(isDarkTheme(task.theme))`; the toggle lets the reviewer override it. Copy the button + CSS from the template.

**Task initialisation** (always include):

> **`getTask().data` only contains `inputs` and `inOuts` the first time — NOT `outputs`.** Outputs are blank until the reviewer fills them in, so they are absent from the initial payload. Do **not** assume every schema field is present. **Merge `task.data` over the fully-initialized `FormData` defaults** (`{ ...defaultFormData, ...task.data }`) so output fields keep their initial values instead of becoming `undefined` — binding an input to an `undefined` value triggers React's controlled/uncontrolled warning and can crash on `.length`/`.ID` access.

```typescript
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
```

Merge over the explicit `defaultFormData` object (not over `prev`) so output fields keep their initial values and the merge never depends on stale batched state. This matches the template's `Form.tsx`.

> **`folderId` — capture only when an SDK service needs it.** Folder-scoped Orchestrator services (Buckets, Assets, Queues, Processes, Jobs) and Data Fabric/Entities (optionally) require the task's `folderId` passed in the call. **Only if** the app calls one of those, add `const [folderId, setFolderId] = useState<number | null>(null);` and `setFolderId(task.folderId);` inside the `.then()`. Attachments are not folder-scoped — omit `folderId` entirely when the app uses only those or no SDK services (the form-only template omits it).

**Change handlers** — see the template's `Form.tsx` for the implementation. Two non-obvious rules:
1. **Every edit must call `codedActionAppService.setTaskData(updated)`** after `setFormData` so Action Center persists in-progress data — not a generic React pattern.
2. **Parse `number`/`integer` fields to a number** (`Number(value)`, guarding `''`/`NaN`); never bind them to a string-only handler, or the value stays a string and breaks `Number.isFinite`/numeric validation and any arithmetic.

**Outcome handlers** — one `async` function per outcome:
```typescript
const handle<OutcomeName> = async () => {
  await codedActionAppService.completeTask('<OutcomeName>', formData);
};
```

**JSX rendering rules:**
| Field type | Renders as |
|------------|------------|
| `inputs` field | `<input readOnly value={formData.<name>} />` — never editable |
| `inOuts` / `outputs` field (`string`) | `<input value={formData.<name>} onChange={handleTextChange} readOnly={isReadOnly} />` |
| `inOuts` / `outputs` field (`number` / `integer`) | `<input type="number" value={formData.<name>} onChange={handleNumberChange} readOnly={isReadOnly} />` |
| Outcome button | `<button onClick={handle<Name>} disabled={!isFormValid}>` |

**Hidden fields** — any field whose name appears in the hidden-fields list (Q3e) must be **omitted entirely from the JSX**. Do not render a label or input element for it. The field must still be present in the `FormData` interface, the initial state object, and submitted via `setTaskData`/`completeTask` — it is only invisible in the UI.

`isFormValid` must be `false` when `isReadOnly` is `true` or when any required output/inout field (that is **not** hidden) is empty.

---

### `src/components/Form.css`

Copy the template's `Form.css` as the default — it styles the gradient header (`.review-header`), section cards (`.form-section`, `.form-title`), the responsive `.form-grid`, inputs (incl. read-only/dashed treatment), the sticky `.form-buttons` footer with primary/secondary `.outcome-btn`, and the entrance/header animations, all on the `index.css` design-system tokens.

Adapt only what the schema or customer needs: drop classes for sections you removed, add classes for new ones, and apply the Q5 layout intent (e.g. two-column grid, summary card at top, different brand colour). Customer styling instructions override the baseline.

---

### PDF viewer (when displaying PDF documents)

**When to use this step:** Any time the app needs to display a PDF — whether from a Storage Bucket, a blob, a direct URL, or a file reference. This applies both when building from scratch and when reviewing existing code.

The document source was already settled in **Q3-doc** (direct file input → Attachments, file path (string) input → Buckets, Data Fabric attachment → Entities + Attachments). If it was not — e.g. the user only said "load a PDF from a storage bucket" — go back and ask Q3-doc first; that phrasing does not pick a path. Fetching the bytes for any of those is straightforward — get the file from the service, build a blob URL (`URL.createObjectURL(blob)`), and pass it to the viewer below as `fileUrl`. The part agents get wrong is the **rendering** inside Action Center's sandboxed iframe — that is what the example below exists to get right.

#### Anti-pattern warning — ALWAYS enforce

> **If the user's code or plan uses `<embed>`, `<object>`, `<iframe src="...">`, or any browser-native PDF embedding tag to display PDFs, stop and warn them:**
>
> "`<embed>`, `<object>`, and `<iframe>` PDF rendering will not work inside UiPath Action Center. Action Center loads coded apps inside a sandboxed iframe with strict CSP/sandbox attributes that block browser-native PDF plugins entirely. You must use an open-source JavaScript PDF renderer instead. Please review the implementation below."
>
> Then present the pattern from this section and ask the user to confirm before generating.

#### Required package

Add `react-pdf` to `dependencies` in `package.json` and install it:

```bash
npm install react-pdf
```

`react-pdf` bundles `pdfjs-dist` as a peer dependency; the worker URL is set at module level via the unpkg CDN (no extra webpack/vite config needed).

#### Component & styles — copy from the template

Copy `src/components/DocumentTab.tsx` and `src/components/DocumentTab.css` **verbatim** from the template's [DocumentTab sections](../assets/templates/action-app-template.md). The component is a generic PDF viewer: it takes a ready-to-render `fileUrl` (a `blob:` URL or direct URL) and owns paging, zoom, download, and the pdf.js worker setup. **The parent fetches the bytes** from whatever source Q3-doc settled on (Attachments / Buckets / Data Fabric), builds the URL with `URL.createObjectURL(blob)`, and passes it in as `fileUrl`. No schema-driven changes are needed inside the component.

---

### `vite.config.ts`

`base: './'` is **always required** — the platform handles URL routing at runtime. Copy verbatim from the template's `vite.config.ts` section; no changes needed.

---

## Deploy Action App

If the app uses SDK services, confirm `uipath.json` exists at the project root with `scope` and `clientId` populated before packing — the `uip codedapp` CLI reads it during pack.

```bash
npm run build
uip codedapp pack dist -n <app-name> -v 1.0.0
uip codedapp publish -t Action        # -t Action is required
uip codedapp deploy
```

See [pack-publish-deploy.md](pack-publish-deploy.md) for full deployment options.
