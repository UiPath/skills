# Connector icon (`app/element/image.svg`)

`init` writes a placeholder (the name's initial on a grey tile). Replace it with the
vendor's logo before publish. `builder validate` only warns when the file is missing — it
does NOT check how the icon looks. The periodic build pipeline does: it fails a connector
whose icon is **invisible on Studio Web's dark surface** (`#1F1F1F`). Black or near-black
ink with no fallback is the usual cause — a black logomark, or shapes with no `fill`
(SVG's default is black).

How the pipeline judges it, so you can check by hand before you publish:

- **Passes right away** if the SVG has any of these:
  - a `@media (prefers-color-scheme: dark)` rule
  - `currentColor` ink, which follows the host text colour
  - an embedded `<image>` bitmap
  - its own backdrop: a solid `<rect>` covering ≥90% of the `viewBox`, or any solid
    light shape (luminance > 0.35) behind the ink. The `init` placeholder passes this way.
- **Otherwise** each `fill` / `stroke` on `path`, `circle`, `ellipse`, `rect`, `polygon`,
  `polyline`, `line` is measured for WCAG contrast against `#1F1F1F`. Fill comes from
  inline `style`, then the attribute, then a `<style>` class, then a parent `<svg>`/`<g>`.
  Ink under **1.5:1** is invisible. Gradients (`url(...)`), `none`, and ink at opacity
  ≤ 0.5 are skipped. A shape with no fill and no stroke counts as black.
- **The verdict covers the whole icon.** It fails only when NO shape is readable. A dark
  navy paired with a lighter brand blue passes. Brand colours need no change: Outlook's
  `#0078D6` is dark by luminance and still well above 1.5:1.
- **An empty file, a file with no `<svg>`, or one with no drawable shapes** fails.

Fix a failing icon by letting the ink follow the surface:

```xml
<style>
  .fg { fill: #000000; }
  @media (prefers-color-scheme: dark) { .fg { fill: #FFFFFF; } }
</style>
<path class="fg" d="..."/>
```

Or paint the shapes with `fill="currentColor"`. Do not recolour a brand logo to dodge the
check. Do not add a backdrop tile the vendor's brand doesn't use.
