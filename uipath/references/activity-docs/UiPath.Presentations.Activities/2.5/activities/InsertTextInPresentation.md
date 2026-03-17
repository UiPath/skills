### InsertTextInPresentation

Inserts or replaces text in a named shape/placeholder on a slide.

```xml
<p:InsertTextInPresentation
    ClearExistingText="False"
    DisplayName="Insert Text"
    Presentation="[PowerPoint]"
    ShapeName="[&quot;Content Holder&quot;]"
    SlideIndex="[slideIndex]"
    Text="[textToInsert]" />
```

- `SlideIndex` — 1-based slide number
- `ShapeName` — name of the shape/placeholder as defined in the slide
- `ClearExistingText` — `True` to clear the shape before inserting
