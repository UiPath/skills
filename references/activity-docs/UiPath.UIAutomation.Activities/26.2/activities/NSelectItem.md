### NSelectItem — select an option from a dropdown

```xml
<!-- Selects an item from a combo box / select element.
     Item: the visible text of the option to select.
     IMPORTANT for some desktop apps: NClick the dropdown first to open it,
     then use NSelectItem to pick the item. -->

<!-- Step 1: Open the dropdown (required for some WinForms combo boxes) -->
<uix:NClick
    ActivateBefore="True"
    ClickType="Single"
    DisplayName="Click 'Transaction Type' dropdown to open it"
    HealingAgentBehavior="SameAsCard"
    InteractionMode="SameAsCard"
    KeyModifiers="None"
    MouseButton="Left"
    ScopeIdentifier="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    Version="V5">
  <uix:NClick.Target>
    <uix:TargetAnchorable
        DesignTimeRectangle="0, 0, 0, 0"
        Guid="b8c9d0e1-f2a3-4567-bcde-678901234567"
        Reference="<transaction-type-dropdown-element-reference>" />
  </uix:NClick.Target>
</uix:NClick>

<!-- Step 2: Select the item -->
<uix:NSelectItem
    DisplayName="Select Item 'Transaction Type'"
    HealingAgentBehavior="SameAsCard"
    Item="[InOperation]"
    ScopeIdentifier="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    Version="V5">
  <uix:NSelectItem.Target>
    <uix:TargetAnchorable
        DesignTimeRectangle="0, 0, 0, 0"
        Guid="c9d0e1f2-a3b4-5678-cdef-789012345678"
        Reference="<transaction-type-dropdown-element-reference>" />
  </uix:NSelectItem.Target>
</uix:NSelectItem>
```

**Web HTML `<select>` elements** typically do NOT need the prior `NClick` — `NSelectItem` alone works.
**WinForms ComboBox** elements often require `NClick` first to open the dropdown list.
