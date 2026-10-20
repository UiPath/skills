# Library Authoring Guide

How to produce a reusable library: a NuGet package whose public workflows surface as activities in every consuming project's panel. For finding and consuming libraries that already exist, see [tenant-library-search-guide.md](tenant-library-search-guide.md).

## When to Build a Library

Good fit:

- **Complex reusable actions** shared by multiple processes — login flows, paginate-and-extract, shared validators, notification senders
- **Standard practices** the organization wants enforced once — logging wrappers, error handlers
- **Interactions with a shared corporate system** (ERP, CRM) that many automations touch

Not a fit:

- **Process-specific logic** — used once, belongs in the project
- **Unstable code** — frequent changes create versioning overhead for every consumer
- **Tightly coupled workflows** — only make sense inside one process
- **Single activities** — wrapping one `Click` as a library activity adds no value. Extract macro-actions (`DownloadInvoices`), not micro-primitives

Boundaries:

| Need | Go to |
|------|-------|
| Start new projects from a standard baseline | Project templates — [environment-setup.md § Template Selection](environment-setup.md) |
| Share UI selectors across projects | UI Libraries — [uia-starter-guide.md § Object Repository as a Published UI Library](uia-starter-guide.md) |
| Reuse logic inside one project | Separate workflow file — [environment-setup.md § Designing for Reuse](environment-setup.md#designing-for-reuse) |

## Creating and Structuring

```bash
uip rpa init \
  --name "<LIBRARY_NAME>" \
  --location "<PARENT_DIR>" \
  --template-id "LibraryProcessTemplate" \
  --expression-language <VisualBasic|CSharp> \
  --target-framework <Windows|Portable> \
  --description "<DESCRIPTION>" \
  --output json
```

- `<LIBRARY_NAME>`: descriptive and scoped, dotted segments accepted — `Company.Email.Utilities`, not `Helpers`. The name becomes the package ID.
- **Default `--target-framework Portable` (Cross-platform) for libraries.** Cross-platform libraries (packed to `lib/net8.0`) install into both Cross-platform and Windows consumer projects; Windows libraries (`lib/net8.0-windows7.0`) install only into Windows projects. Choose Windows only when the library needs Windows-only activities or dependencies — every Windows-only pick shrinks the consumer base.
- `<DESCRIPTION>` (`project.json` → `description`) becomes the package description shown in the feed — write it for consumers.
- The template scaffolds `NewActivity.xaml`; replace it — delete the file and point `project.json` → `main` at a real workflow, then add one workflow file per activity.
- Library `project.json` differs from a process: `designOptions.outputType` is `"Library"`, and there is no `entryPoints` (SKILL.md Rule 15) — do not add one.

### Public vs private workflows

Every workflow file is **public** by default — packed as an activity. To keep a helper internal, add its filename to `project.json`:

```json
"designOptions": {
  "libraryOptions": {
    "privateWorkflows": [
      "ValidateEmailFormat.xaml"
    ]
  }
}
```

Private workflows compile into the package and stay invocable from the library's own workflows, but no activity is generated for consumers.

### Activity identity

- Activity name and class = workflow file name (`SendInvoiceNotification.xaml` → activity `SendInvoiceNotification`)
- Activity namespace = library name with dots and hyphens sanitized to underscores (`Company.Email.Utilities` → namespace `Company_Email_Utilities`); the package ID and assembly keep the dotted name. Read the real namespace from `uip rpa packages inspect` on the packed `.nupkg` — never derive it
- Property tooltip = the argument's description annotation in XAML: `sap2010:Annotation.AnnotationText` on the `x:Property`

### Activity Layout — the sidecar file

Each public workflow can ship as a rich activity: custom display name, tooltip, color, SVG icon, and per-property display names, placeholders, input widgets, required flags, and category grouping. All of it is authored in a sidecar JSON next to the workflow — `<WORKFLOW_NAME>.xaml.json`:

```json
{
  "DisplayName": "Send Invoice Notification",
  "Tooltip": "Sends an invoice notification email and returns a delivery summary",
  "Color": "#1F8FFF",
  "OriginalIconFileName": "SendInvoiceNotification.xaml.svg",
  "Arguments": [
    {
      "Name": "RecipientEmail",
      "DisplayName": "Recipient email",
      "Category": "Input",
      "Tooltip": "Email address that receives the notification",
      "Placeholder": "someone@company.com",
      "Widget": "TextComposer",
      "IsRequired": true,
      "IsPrincipal": true,
      "ArgumentType": 0
    },
    {
      "Name": "UrgentDelivery",
      "DisplayName": "Urgent delivery",
      "Category": "Options",
      "Tooltip": "Send with high priority",
      "Widget": "Toggle",
      "IsRequired": false,
      "IsPrincipal": false,
      "ArgumentType": 0
    }
  ]
}
```

Rules:

1. **`Arguments[].Name` must match the XAML argument name exactly** — the sidecar decorates arguments, it does not declare them.
2. **The sidecar wins over XAML annotations.** Without a sidecar, the argument annotation is the tooltip and the file name is the display name; the sidecar overrides both and adds everything else.
3. **Icon**: place an SVG next to the workflow as `<WORKFLOW_NAME>.xaml.svg` and reference it in `OriginalIconFileName`. `pack` embeds it as a package resource.
4. **`Widget` is the property's input type** (Studio: "Input type"). Valid values depend on the argument's type — omit `Widget` for the type's default editor:

| Argument type | `Widget` values |
|---------------|-----------------|
| `String` | `TextComposer` (default), `RichTextComposer`, `Dropdown`, `AutocompleteForExpression`, `RadioGroup` |
| `Boolean` / `bool?` | `Toggle` (default), `ConditionBuilder`, `NullableBoolean` |
| Numeric | `Number` (default), `Dropdown` |
| `DateTime` | `Datetime` |
| `TimeSpan` | `Timespan` |
| `String[]` | `StringArray` |
| `Dictionary` | `Dictionary` |

   `DataSourceItems` (string array of choices) applies only to `Dropdown`, `RadioGroup`, and `AutocompleteForExpression`.
5. **`Category`** groups properties in the activity's body, in sidecar argument order; `IsPrincipal: true` surfaces the property on the activity card, `IsRequired: true` marks it mandatory.
6. **`HelpLink`** is a valid sidecar field but stays design-time only — it does not ship in the compiled activity metadata.
7. **`ArgumentType` is `0`** for plain arguments.

`pack` compiles the sidecar into the activity metadata embedded in the library assembly — consumers see the layout in their Activities panel with no extra steps.

## The Public-Workflow Contract — MANDATORY

Each public workflow is an API surface. Apply every rule:

1. **Name workflows verb-noun PascalCase, no spaces** — `SendNotificationEmail.xaml`, `DownloadInvoices.xaml`. The file name becomes the activity name in the consumer's panel.
2. **Public arguments: PascalCase, NO `in_`/`out_`/`io_` prefixes** — `InvoiceId`, `RecipientEmail`, `NotificationResult`. Argument names become activity property names; prefixes become noise on the property grid. This inverts the process-workflow convention: workflows invoked via Invoke Workflow File keep directional prefixes ([environment-setup.md § Designing for Reuse](environment-setup.md#designing-for-reuse)); library public workflows drop them.
3. **Describe every public argument** via its `sap2010:Annotation.AnnotationText` — descriptions ship as property tooltips. For display names, placeholders, widgets, and grouping, add the layout sidecar ([§ Activity Layout](#activity-layout--the-sidecar-file)).
4. **Expect — and keep — the analyzer naming warnings.** `build`/`pack` emit `Argument <Name> does not respect the set pattern ^in_...` for prefix-free library arguments. The warning is non-blocking. Do NOT rename arguments to silence it.
5. **Return application handles.** A workflow that opens or attaches to an app outputs the window/browser object; downstream public workflows accept it as an input argument instead of reopening.
6. **Post-authoring audit:** before packing, re-check every public workflow against rules 1-3 — name form, argument naming, argument descriptions.

## Error Contract

- **Throw meaningful exceptions** — `BusinessRuleException` for input validation failures, with the offending value in the message. Let system exceptions propagate to the consumer.
- **Never swallow errors**: no empty `Catch` blocks, no `out` boolean success flags in place of exceptions. A swallowed error returns control to a consumer whose target app is in an unknown state.
- **Never set `ContinueOnError` inside a library** — the consumer decides failure policy.
- **No hardcoded paths** — accept paths as arguments, or build from `UiPath.Constants.Project.Location` for files packed with the library.
- **No embedded config or secrets** — read Orchestrator assets at the consumer level and pass them in as arguments. A credential passes as its asset's name, and the library reads it inside the scope that uses it: a `SecureString` argument fails `build` ([cli-reference.md § Analyzer errors](cli-reference.md#analyzer-errors)).

## Versioning

`projectVersion` in `project.json` is the package version (override at pack time with `--package-version`). Follow SemVer:

| Bump | When | Consumer impact |
|------|------|-----------------|
| Patch `x.x.1` | Bug fix, no interface change | Safe drop-in |
| Minor `x.1.x` | New workflow or new optional argument, backward compatible | Safe upgrade |
| Major `1.x.x` | Renamed/removed workflow or argument, changed behavior | Code changes required |

1. Renaming a public workflow or argument is a **breaking change** — major bump. To change an argument compatibly, add a new one and keep the old.
2. **Never delete published versions from the feed** — consumers pin them. `libraries delete` is for mistaken uploads only.
3. Consumers pin exact versions in production.

## Pack & Publish

```bash
uip rpa pack "<PROJECT_DIR>" "<OUTPUT_DIR>" --output json
uip rpa publish "<OUTPUT_DIR>/<LIBRARY_NAME>.<VERSION>.nupkg" --output json
```

- `publish` reads the package's type and sends a library to the tenant **Libraries feed** (`Data.Feed`: `Orchestrator Tenant Libraries Feed`), not the processes feed a process goes to. Other destinations, refusals and the duplicate-version error: [cli-reference.md § Pack & Publish to Orchestrator](cli-reference.md#pack--publish-to-orchestrator).
- `<OUTPUT_DIR>` must be OUTSIDE the project directory tree — `pack` refuses an output path inside the project. Use a sibling directory (e.g. `dist/`).
- Verify the publish:

```bash
uip or libraries list --search "<LIBRARY_NAME>" --output json
```

Returns the library with `Key` = `<PackageId>:<Version>` and `ProjectType: "ProcessLibrary"`.

## Consumption Loop

1. **Discover** existing libraries before building new ones — [tenant-library-search-guide.md](tenant-library-search-guide.md) (SKILL.md Rule 9).
2. **Install** into the consumer as a dependency — SKILL.md § Resolving Packages & Activity Docs. The install records the dependency in the consumer's `project.json`; the library's activities become available.
3. **Build-time resolution:** signed in, `build` and `pack` restore the library from the tenant's libraries feeds, as the install does; no extra NuGet source is needed.
4. **Author against the library in consumer XAML.** Once the library is installed, `activities find` returns its public workflows and `activities get-default-xaml` returns each one's element with its arguments as properties, without their types or directions — read those from the package itself:

```bash
uip or libraries download "<PackageId>:<Version>" --destination "<LOCAL_DIR>/<LIBRARY_NAME>.<VERSION>.nupkg" --output json
uip rpa packages inspect --nupkg-path "<LOCAL_DIR>/<LIBRARY_NAME>.<VERSION>.nupkg" --output json
```

Declare the namespace and use each public workflow as an element — property names = the library's argument names:

```xml
<Activity ... xmlns:lib="clr-namespace:<SANITIZED_NAMESPACE>;assembly=<LIBRARY_NAME>">
  <lib:SendInvoiceNotification RecipientEmail="..." InvoiceId="..." />
```

`<SANITIZED_NAMESPACE>` is the underscore form from [§ Activity identity](#activity-identity). Bind non-literal properties per the project's expression language rules ([xaml/xaml-basics-and-rules.md](xaml/xaml-basics-and-rules.md)).

5. **Stale design session after the dependency becomes resolvable:** `build` compiles the consumer but `validate` keeps failing with `Cannot create unknown type` for the library activity. Run `uip rpa project close --project-dir "<CONSUMER_PROJECT_DIR>"` and re-run `validate`; the next command reloads the project.
6. **Same version repacked:** the package cache keeps the first package under an id and version and ignores a repack, so bump the library version whenever a consumer must see a change.

## Library Patterns

| Pattern | Shape | Example |
|---------|-------|---------|
| Wrapper | Bundle related operations into one higher-level activity | `OpenExcelAndReadSheet` instead of Open Workbook + Read Range |
| Connector | One library per corporate system — single source of auth, selectors, business rules | `CompanyERP.Library` owns all ERP interactions |
| Framework | Scaffolding consumers extend (REFramework-style) | State machine with extension points |
| Data access | Centralize database/API access behind typed activities | `GetCustomerById` returns a row from any backend |

## Pitfalls

- **Never name a library project `lib`** — collides with the NuGet package folder layout; consumers fail to compile.
- **A workflow file and one of its arguments must not share the same name** — publishing crashes on the name collision.
- **Never set `ImplementationVersion`** on the XAML `ActivityBuilder` — a framework bug silently drops the library's argument mappings.
