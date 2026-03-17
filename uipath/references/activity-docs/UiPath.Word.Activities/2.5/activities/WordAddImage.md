# WordAddImage

Inserts an image into the document.

Must be placed inside the `WordApplicationScope` body `Sequence`.

```xml
<p:WordAddImage
    DisplayName="Add Image"
    Height="100"
    ImagePath="[imagePath]"
    Width="150" />
```

- `ImagePath` — path to the image file
- `Width`, `Height` — dimensions in points (numeric expressions)
