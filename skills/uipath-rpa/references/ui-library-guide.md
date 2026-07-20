# Object Repository as a Published UI Library

Selector breakage is the #1 maintenance cost in UI automation. A **UI Library** is a published library project whose Object Repository ships inside the `.nupkg` — descriptors defined once, consumed by every automation against the same application. Fix a descriptor once, bump the version, and all consumers inherit the fix.

## Hierarchy and naming

```
Application (InvoicePortal)
  └── Screen (LoginPage)
      └── Element (UsernameField)
```

- Reference form: `App.Screen.Element` — `InvoicePortal.LoginPage.UsernameField`
- Business-meaningful PascalCase element names: `SubmitOrderButton`, not `Button32`
- One descriptor per distinct UI element; screens mirror the application's logical screens

## Extract-and-publish pattern

Precondition: the source project has captured descriptors (`.objects/` content). If it has none, capture targets first (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md` § Configuring Targets) — there is nothing to promote, and hand-writing descriptors is forbidden.

1. Develop the first process against its **local** Object Repository, configuring targets as usual (§ Configuring Targets in the package guide above).
2. Promote the reusable descriptors into a dedicated UI Library project — a library project ([library-authoring-guide.md](library-authoring-guide.md)) holding the shared Object Repository; pack and upload per [library-authoring-guide.md § Pack & Publish](library-authoring-guide.md). Concrete Object Repository manipulation steps: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/object-repository.md`.
3. **One UI Library per corporate application** (SAP, Salesforce, Workday) — an update to one app's selectors must not force re-deployment of another's.
4. New automations against that application consume the UI Library from the start. Process-specific one-off descriptors stay in the local Object Repository.

## Consumption

Install the UI Library as a package dependency; its descriptors appear under **UI Libraries** in the Object Repository and are targetable like local descriptors. Coded workflows resolve them via the package guide's § Finding Descriptors Step 2 (UILibrary NuGet packages). Selector updates propagate by bumping the dependency version — no per-workflow changes.

## Update rules — MANDATORY

1. **Update descriptors in place — NEVER delete-and-re-add an element.** The element-to-activity link is identity-based; deleting the element severs it and every consumer activity bound to it breaks, even if a same-named element is re-created.
2. **Version by SemVer** ([library-authoring-guide.md § Versioning](library-authoring-guide.md)): selector fix without renaming = patch; element/screen rename or restructure = breaking = major.
3. **Promote accepted healing fixes.** When a selector recovery ([uia-running-guide.md § Runtime Selector Failure Recovery](uia-running-guide.md#runtime-selector-failure-recovery)) is accepted in a workflow that consumes a shared UI Library, apply the fix in the UI Library and bump the version — do not re-fix the same selector consumer by consumer.
