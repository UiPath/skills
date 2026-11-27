# WordReplaceText

Finds and replaces text within the document.

Must be placed inside the `WordApplicationScope` body `Sequence`.

```xml
<p:WordReplaceText
    DisplayName="Replace Text"
    Found="[wasFound]"
    Replace="[&quot;NewValue&quot;]"
    ReplaceAll="True"
    Search="[&quot;OldValue&quot;]" />
```

- `Search` — string expression for the text to find
- `Replace` — string expression for the replacement text
- `ReplaceAll` — `True` to replace all occurrences; `False` for first occurrence only
- `Found` — output `Boolean` variable indicating whether the search text was found
