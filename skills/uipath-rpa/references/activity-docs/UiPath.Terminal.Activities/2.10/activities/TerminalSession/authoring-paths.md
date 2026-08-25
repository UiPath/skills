# Authoring `ConnectionString` Outside Studio Desktop

Studio Desktop ships two design-time tools that consume and produce the literal `ConnectionString` value: the **Connection Settings** dialog (visual field editor) and the **Terminal Recorder** (records interactions with a live session and emits child activities). Both require the `ConnectionString` to be a literal string they can read at design time — an expression-bound value resolves only at runtime, after the designer has already needed it.

Outside Studio Desktop (Studio Web, CLI authoring, code review, non-interactive contexts), neither tool is available, so the field-completeness, single-quote, and integer-enum rules of the serialized form have to be satisfied by other means. This doc covers the two non-literal paths (Options B and C). The literal path (Option A) lives in the main [`TerminalSession.md`](../TerminalSession.md) since it interoperates with the Studio designer.

## Option B — XAML: build a `ConnectionData` and serialize with `ConnectionStringHelper.Serialize`

Recommended for non-Studio XAML authoring (Studio Web, CLI authoring, PR review). Build a strongly-typed `ConnectionData` in an `Assign`, run it through the helper, bind the result to `ConnectionString`:

```xml
<Assign DisplayName="Build connection string">
  <Assign.To>
    <OutArgument x:TypeArguments="x:String">[connectionString]</OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="x:String">[ConnectionStringHelper.Serialize(New ConnectionData() With {
      .Host = "telehack.com",
      .Port = 23,
      .ProviderType = TerminalProviderType.UiPathNew,
      .ConnectionType = ConnectionType.Address,
      .ConnectionProtocol = CommunicationType.TELNET,
      .TerminalType = TerminalType.TerminalVT,
      .TerminalModel = CInt(TTVtTermId.VT100)
    })]</InArgument>
  </Assign.Value>
</Assign>
```

Then bind `TerminalSession.ConnectionString="[connectionString]"`.

Why this works:

- **Real enum names**, compile-time validated. Typos surface at JIT with line numbers, not as `Invalid connection string` from the JSON validator.
- **Enum-to-integer conversion is automatic.** `DataContractJsonSerializer` writes each enum member as its underlying integer; you never write `9` for `UiPathNew` and never look up the order.
- **Field-completeness rule is satisfied automatically.** `DataContract` serializes every member of `ConnectionData`, including the null/default ones the validator demands. You set only the fields you care about; the helper fills in the rest.
- **No `{}` markup-escape prefix.** The attribute value is a VB expression (`[connectionString]`), not a literal JSON string, so XAML never sees a leading `{`.

Requirements in the XAML file: import `UiPath.Terminal.Helpers` and `UiPath.Terminal.Enums` in `TextExpression.NamespacesForImplementation`; reference `UiPath.Terminal` in `TextExpression.ReferencesForImplementation`. C# expression projects use the same shape with `(int)` instead of `CInt(...)` and object-initializer syntax instead of `With { ... }`.

**Trade-off vs Option A:** when `ConnectionString` is expression-bound, Studio Desktop's **Connection Settings** dialog and **Terminal Recorder** cannot open on the activity — both need a literal value they can read and round-trip at design time. If you want those tools, author the connection in Studio Desktop with a literal, then either keep it as a literal (Option A) or copy the resulting string into your non-Studio workflow.

## Option C — Coded workflows: use `GetConnection(ConnectionData)`

Skip the `TerminalSession` activity entirely; pass a strongly-typed `ConnectionData` to `terminal.GetConnection` and operate on the returned `TerminalConnection`. See [coded-api.md § Coded Quickstart](../../coded/coded-api.md#coded-quickstart) and the [Common Patterns](../../coded/coded-api.md#common-patterns) section.

Same Studio-tooling trade-off as Option B: no Recorder, no Connection Settings dialog.

## Choosing between A, B, C

| Authoring context | Recommended option |
|-------------------|---------------------|
| Studio Desktop, you want the Connection Settings dialog or Terminal Recorder available | **A** (literal string in attribute) |
| Studio Desktop, the string comes from an Asset / config / argument at runtime | **A** (literal expression binding) |
| Studio Web | **B** |
| CLI authoring (`uip rpa`), PR review, code generation | **B** |
| Coded C# workflow (`[Workflow]` class) | **C** |
| Hand-authoring on a build-only machine with no Studio | **B** (literal is fine too, but you lose typed-enum compile checks) |
