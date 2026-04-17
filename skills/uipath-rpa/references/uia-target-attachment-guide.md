# OR Target Attachment

How to attach Object Repository screens and elements to XAML workflow activities.

## IdRef Contract

The linker addresses activities by `sap2010:WorkflowViewState.IdRef`. Every activity that will be linked MUST carry a unique IdRef of the form `<ClassName>_<N>` — for example `NApplicationCard_1`, `NClick_1`, `NClick_2`, `NTypeInto_1`. Numbering is per class and unique across the whole file. When inserting activities into an existing file, scan for the highest existing `<ClassName>_<N>` and continue from `N+1`.

This matches Studio's own naming convention, so files remain clean when re-opened in Studio.

## Fast Path: Linking OR Entries to Activities

Write plain activities (no `.Target` child element) with unique IdRefs, then attach targets post-write using `link-screen` and `link-element`.

> **Do not run `link-screen` or `link-element` calls in parallel.** These commands mutate the same `.xaml` file and will corrupt each other when invoked as parallel Bash tool calls. Run them sequentially — either as separate Bash calls one after another, or batched in a single Bash call chained with `&&` (stop on first failure) or `;` (continue on failure). Link the screen first, then link each element.

### 1. Link a screen to an ApplicationCard

```bash
uip rpa uia object-repository link-screen \
  --workflow-relative-path "<RELATIVE_XAML_PATH>" \
  --activity-ref-id "<ACTIVITY_REF_ID>" \
  --reference-id "<SCREEN_REFERENCE_ID>" \
  --project-dir "<PROJECT_DIR>" \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--workflow-relative-path` | Yes | Path to the `.xaml` file, relative to the project directory (e.g., `Workflows/Main.xaml`). |
| `--activity-ref-id` | Yes | The `sap2010:WorkflowViewState.IdRef` on the target activity — typically `NApplicationCard_1`. |
| `--reference-id` | Yes | OR screen reference returned by `uia-configure-target` or `indicate-application`. |

### 2. Link elements to UI activities

One call per (activity, element) pair. The CLI does not batch.

```bash
uip rpa uia object-repository link-element \
  --workflow-relative-path "<RELATIVE_XAML_PATH>" \
  --activity-ref-id "<ACTIVITY_REF_ID>" \
  --reference-id "<ELEMENT_REFERENCE_ID>" \
  --project-dir "<PROJECT_DIR>" \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--workflow-relative-path` | Yes | Path to the `.xaml` file, relative to the project directory. |
| `--activity-ref-id` | Yes | The `sap2010:WorkflowViewState.IdRef` on the target activity (e.g., `NClick_3`). |
| `--reference-id` | Yes | OR element reference returned by `uia-configure-target` or `indicate-element`. |
| `--target-property` | No | Activity property to attach the target to. Supports dotted paths for nested properties (e.g., `SearchedElement.Target`). Defaults to `Target`. |

**When to use `--target-property`:** most UI activities (`NClick`, `NTypeInto`, `NGetText`) attach the target at `.Target`, so the default is correct. Some activities expose the target at a nested property (e.g., anchor-based activities use `SearchedElement.Target`). When the target sits anywhere other than `.Target`, pass `--target-property` explicitly.

**Element reuse:** when the same element is referenced by multiple activities (e.g., the same field clicked and then typed into), call `link-element` once per activity with each activity's own `--activity-ref-id`.

## Fallback: Embedding OR Entries When Linking Fails

Use this path only when a `link-screen` or `link-element` call returns a non-zero exit or an error for a specific reference ID. Embed the OR XAML snippet directly into the matching activity — scoped to only the failed reference, not the whole screen.

### 1. Get the screen XAML for the ApplicationCard

```bash
uip rpa uia object-repository get-screen-xaml \
  --reference-id "<SCREEN_REFERENCE_ID>" \
  --project-dir "<PROJECT_DIR>"
```

Returns a `<TargetApp>` element. Embed it inside the ApplicationCard:

```xml
<uix:NApplicationCard.TargetApp>
  <!-- paste the returned <TargetApp ... /> here -->
</uix:NApplicationCard.TargetApp>
```

### 2. Get element XAML for UI activities

```bash
uip rpa uia object-repository get-elements-xaml \
  --reference-ids "<REF_1>,<REF_2>,<REF_3>" \
  --project-dir "<PROJECT_DIR>"
```

Returns `<TargetAnchorable>` elements, one per reference ID, separated by `=== Element Name ===` headers. Embed each inside its activity's `.Target` property (or the nested property named on the activity, e.g., `SearchedElement.Target`):

```xml
<uix:NClick ...>
  <uix:NClick.Target>
    <!-- paste the returned <TargetAnchorable ... /> here -->
  </uix:NClick.Target>
</uix:NClick>

<uix:NTypeInto ...>
  <uix:NTypeInto.Target>
    <!-- paste the returned <TargetAnchorable ... /> here -->
  </uix:NTypeInto.Target>
</uix:NTypeInto>

<uix:NGetText ...>
  <uix:NGetText.Target>
    <!-- paste the returned <TargetAnchorable ... /> here -->
  </uix:NGetText.Target>
</uix:NGetText>
```

| Parameter | Source |
|-----------|--------|
| `<SCREEN_REFERENCE_ID>` | OR screen reference returned by `uia-configure-target` or `indicate-application` |
| `<REF_1>,<REF_2>,...` | Comma-separated OR element references returned by `uia-configure-target` or `indicate-element` |

When an element is used by multiple activities (e.g., the same field clicked and then typed into), use the same `<TargetAnchorable>` snippet in each activity's `.Target` property.
