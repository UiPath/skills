# Semantic XAML Editing Guide

Use this guide when modifying an existing `.xaml` workflow by adding or moving
activities, arguments, variables, namespace imports, or assembly references.
Treat each change as a structured operation on the workflow tree, then apply the
smallest possible textual diff to preserve prefixes, designer metadata, and
surrounding layout.

## Decision Rules

| Task | Preferred path |
| --- | --- |
| Add a UI Automation target | Use `uia-configure-target`; do not hand-edit selectors |
| Add a package activity | Use `find-activities` and `get-default-activity-xaml`, then adapt the returned snippet |
| Add an Integration Service connector activity | Follow `../is-connector-xaml-guide.md`; schema and connection binding are required |
| Add workflow arguments, variables, imports, or references | Use the recipes below |
| Rewrite large control-flow regions | Prefer a new workflow file or ask the user to confirm the restructuring |
| Edit a Flowchart, State Machine, or ProcessDiagram layout | Read `canvas-layout-guide.md` first and preserve existing ViewState |

## Pre-Edit Checklist

1. Read `project.json` and record `expressionLanguage`, `targetFramework`, and
   installed package versions.
2. Run a baseline validation before editing:
   `uip rpa get-errors --file-path "<relative/path.xaml>" --output json`.
3. Read the full target `.xaml` file once, then identify a narrow, unique anchor:
   `DisplayName` plus activity type is safer than `DisplayName` alone.
4. Collect existing root `xmlns:*` prefixes, `x:Name` values, and
   `sap2010:WorkflowViewState.IdRef` values.
5. Decide the exact operation first: `insert-activity`, `add-argument`,
   `add-variable`, `add-namespace-import`, `add-assembly-reference`, or
   `validate-and-save`.

If the baseline has errors, separate pre-existing errors from errors introduced
by your edit. Do not claim the edit caused or fixed unrelated baseline errors.

## Operation Recipes

### Insert Activity

1. Discover the activity class and package:
   `uip rpa find-activities --query "<task>" --output json`.
2. Get starter XAML from the installed package:
   `uip rpa get-default-activity-xaml --activity-class-name "<class>" --output json`.
3. Read the activity docs from `{PROJECT_DIR}/.local/docs/packages/{PackageId}/`
   or the bundled fallback under `../activity-docs/{PackageId}/`.
4. Trim the starter snippet to the activity element and required child elements.
   Keep package-specific property objects when docs say they are required.
5. Insert the snippet into the correct parent collection:
   - `Sequence`: direct child of the sequence, after the anchor activity.
   - `If.Then` / `If.Else`: inside the branch `Sequence`, not beside the `If`.
   - Scope activity bodies: inside the body `Sequence`, not beside the scope.
   - `Flowchart` / `ProcessDiagram`: follow the node-wrapper and `x:Reference`
     registration rules in `xaml-basics-and-rules.md`.
6. Give the new activity a unique `DisplayName` and a unique
   `sap2010:WorkflowViewState.IdRef` when the surrounding file uses IdRefs.
7. Add only the missing root namespace declarations and imports/references.
8. Validate immediately with `get-errors`.

### Add Argument

Add arguments only inside the root `<x:Members>` block:

```xml
<x:Property Name="in_CustomerId" Type="InArgument(x:String)" />
<x:Property Name="out_Result" Type="OutArgument(x:String)" />
<x:Property Name="io_Attempts" Type="InOutArgument(x:Int32)" />
```

Rules:

- Use `in_`, `out_`, and `io_` prefixes.
- Preserve existing argument order and naming style when the file already has
  arguments.
- Use the type aliases already present in the file when possible.
- Add the required root namespace only when the type is not already resolvable.

### Add Variable

Add variables to the nearest owning activity that needs the state:

```xml
<Sequence.Variables>
  <Variable x:TypeArguments="x:String" Name="statusText" />
</Sequence.Variables>
```

Rules:

- Put `<Sequence.Variables>` before executable child activities.
- For `Flowchart`, use `<Flowchart.Variables>`.
- For `StateMachine`, use the variable collection supported by the surrounding
  workflow structure.
- Do not place a variable in a branch if a later sibling activity must read it.
- Prefer narrower scope when the value is used only inside one branch or loop.

### Add Namespace Import

Namespace imports belong inside the single
`TextExpression.NamespacesForImplementation` collection:

```xml
<TextExpression.NamespacesForImplementation>
  <sco:Collection x:TypeArguments="x:String">
    <x:String>System</x:String>
    <x:String>UiPath.Platform.ResourceHandling</x:String>
  </sco:Collection>
</TextExpression.NamespacesForImplementation>
```

Rules:

- Do not create a second `TextExpression.NamespacesForImplementation` block.
- Do not create a second `<sco:Collection>` child.
- Insert into the existing collection and keep the existing `sco` prefix.
- Avoid duplicate `<x:String>` entries.

### Add Assembly Reference

Assembly references belong inside the single
`TextExpression.ReferencesForImplementation` collection:

```xml
<TextExpression.ReferencesForImplementation>
  <sco:Collection x:TypeArguments="AssemblyReference">
    <AssemblyReference>System.Data</AssemblyReference>
    <AssemblyReference>UiPath.System.Activities</AssemblyReference>
  </sco:Collection>
</TextExpression.ReferencesForImplementation>
```

Rules:

- Do not duplicate an existing assembly reference.
- Match the package assembly name from the activity docs or default XAML.
- Keep the existing collection prefix and type argument form.

## Prefix and ViewState Safety

UiPath XAML uses namespace prefixes as part of the designer contract. XML tools
that reserialize the whole document may rename prefixes, reorder attributes, or
collapse nodes in ways Studio can load differently.

Keep these invariants:

- Preserve root `xmlns:*` prefixes exactly unless adding a new prefix.
- Preserve `mc:Ignorable` prefix names. If you add a designer prefix that must be
  ignorable, add that literal prefix to `mc:Ignorable`.
- Preserve every existing `sap2010:WorkflowViewState.IdRef`.
- Generate unique IdRefs for new nodes only; never renumber existing ones.
- Preserve existing `x:Name` values and `x:Reference` targets.
- Avoid reformatting the whole file.

## Validation Loop

After every operation:

1. Run `uip rpa get-errors --file-path "<relative/path.xaml>" --output json`.
2. If errors appear, fix one category at a time: package, structure, type,
   activity properties, then logic.
3. Stop after five failed fix attempts and report the current error output.
4. Run `uip rpa build --project-dir "<PROJECT_DIR>" --output json` before
   reporting the workflow as verified, unless a successful `run-file` smoke test
   already compiled the project.

## Stop Conditions

Stop and ask for help instead of continuing to patch when:

- the anchor activity is not unique;
- a UI selector or Object Repository target is missing;
- the edit requires changing project `expressionLanguage` or `targetFramework`;
- a dynamic connector activity lacks schema or connection metadata;
- a Flowchart/State Machine/ProcessDiagram edit needs a layout you cannot infer;
- `get-errors`, `build`, or Studio IPC is unavailable in the environment.
