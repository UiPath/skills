### InsertSlide

Inserts a new slide into the presentation.

```xml
<p:InsertSlide
    DisplayName="Insert Slide"
    InsertType="End"
    InsertedAtPosition="[newSlideIndex]"
    LayoutName="[&quot;(default)&quot;]"
    Presentation="[PowerPoint]"
    SlideMasterName="[&quot;(default)&quot;]" />
```

- `InsertType` — `"End"`, `"Beginning"`, etc.
- `InsertedAtPosition` — output `Int32` with the newly inserted slide's index
- `LayoutName`, `SlideMasterName` — layout/master to use (use `"(default)"`)
