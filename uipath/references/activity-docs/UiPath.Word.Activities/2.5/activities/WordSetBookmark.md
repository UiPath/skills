# WordSetBookmark

Sets the text content of a named bookmark in the document.

Must be placed inside the `WordApplicationScope` body `Sequence`.

```xml
<p:WordSetBookmark
    BookmarkName="[&quot;InvoiceNumber&quot;]"
    DisplayName="Set Bookmark"
    Text="[invoiceNumberValue]" />
```

- `BookmarkName` — name of the bookmark defined in the Word document
- `Text` — string expression for the bookmark's new content
