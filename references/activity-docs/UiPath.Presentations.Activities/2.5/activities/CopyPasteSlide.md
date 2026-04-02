### CopyPasteSlide

Copies (or moves) a slide within or between presentations.

```xml
<p:CopyPasteSlide
    DisplayName="Copy Slide"
    DestinationPresentation="[PowerPoint]"
    Move="False"
    SlideToInsert="[destinationIndex]"
    SlideToCopy="[sourceIndex]"
    SourcePresentation="[PowerPoint]" />
```

- `SlideToCopy` — 1-based source slide index; `SlideToInsert` — 1-based destination index
- `Move` — `True` to cut+paste instead of copy
- `SourcePresentation` and `DestinationPresentation` can be the same handle for within-file copies
