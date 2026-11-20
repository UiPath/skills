# uipdm Extension Elements

`uipdm` = `http://uipath.com/schema/1.0/dmn-ext/decision-model`, defined by [uipdm.xsd](uipdm.xsd) (a copy of `vertical-solution-service/workers/policy-engine/docs/dmn/uipdm.xsd`; if that file exists and differs, use it and say so). The elements carry what DMN has no home for: where in the policy a rule was read, where an input's value comes from, and what was assumed. They live only inside `<extensionElements>`, so the DMN stays valid without the schema.

Declare `xmlns:uipdm="http://uipath.com/schema/1.0/dmn-ext/decision-model"` on `<definitions>`, only when the file carries at least one uipdm element.

## What to write, and where

| Element | Where | When |
|---|---|---|
| `<uipdm:inputVariable source sourceType [sourceMapping] [dataType]>` with `<uipdm:constraint>` children | `inputData/extensionElements`, before `<variable>` | Every input built from a document. `sourceType` is `document` or `system`. `constraint` lists the values the policy names for a categorical input (not `<allowedValues>`, which the engine enforces). `dataType` only where `typeRef` cannot say it: `categorical`, or a `string` that has constraints. Its values are `boolean`, `numeric`, `date`, `datetime`, `time`, `duration`, `string`, `categorical`; the DMN type name `number` is not one of them. |
| `<uipdm:sourceRefs><uipdm:sourceRef page box [blockId]/></uipdm:sourceRefs>` | `rule/extensionElements`, before the first `<inputEntry>` | A row whose citation resolved. One `sourceRef` per resolved citation. |
| `<uipdm:qualityWarning [conditionId] [field]>text</uipdm:qualityWarning>` | `definitions/extensionElements`, repeated | An unresolved citation, an ambiguity in the source resolved by assumption, or a cell that could not be translated. The text is what a log reads. |

Never write `review` (the human-review state, set by the person reviewing), `ruleState`, `parkedRule`, `scoreBand`, `conditionState` or `agentAssessment`. They hold the extraction pipeline's own state, and a policy gives no source for their values. Attributes and child elements of the elements above are exactly those in [uipdm.xsd](uipdm.xsd). Annotations stay as they are: critical rule 9 of the uipath-rules SKILL.md still applies, and uipdm elements do not replace the Annotation column.

## Boxes

A `box` is four plain decimals `left,top,width,height`, no spaces, in the digitizer's page units (pixels at 270 DPI, origin at the page's top-left, y growing downward). `page` is the digitizer's `pageIndex` + 1. Never write or estimate a box by hand: [extraction/citation-guide.md](extraction/citation-guide.md) turns a verbatim quote into a box with `resolve-refs.mjs`.

With no digitizer positions (the open-source PDF path), write `inputVariable` and `qualityWarning`, and write each cited page as a page-only `<uipdm:sourceRef page="<N>"/>`: no `box`, no `blockId`, one per distinct page the row cites. The schema makes `page` the only required attribute. Add one `qualityWarning` saying the citations carry a page and no source box.

## Editing a rule that carries uipdm elements

An edit to a row keeps that row's `sourceRefs` unless the edit changes what the row cites. A new row cites its source the same way, or carries a `qualityWarning` that says it has none. A row removed takes its `sourceRefs` with it. Never strip the elements to make a file smaller, and never rewrite one that the request did not touch.

## Check

`uip rules validate` accepts `uipdm:` elements without reading them. After `refresh` and `validate`, check every element against the schema:

```bash
node "<SKILL_DIR>/scripts/check-uipdm.mjs" "<DMN_FILE>"
```

It needs only `node`; it reads [uipdm.xsd](uipdm.xsd) from `references/`, or from its own folder when the script was copied elsewhere, or from a path given as a second argument. Exit 0 prints how many elements were checked. Exit 1 lists each invalid element with the reason; fix those and run it again. Exit 2 is a usage error, an unreadable file, or a schema construct the checker does not implement: show the error, skip the check, and say so in the summary. A `sourceRef` with no `page`, or with a `box` of three numbers, is rejected.

## Not verified

- How the Studio Web designer treats these elements on edit and save; it may drop elements it does not know.
- A digitizer run with a page range: whether `pageIndex` keeps the original page number or restarts at 0.
- Rotated or skewed pages and scanned images: whether `box` is in the rotated or the original page frame.
- Whether `document.md`'s `<!-- page: N -->` markers always equal `pageIndex` + 1.
- How the designer and viewer treat a page-only `sourceRef`.
- The 270 DPI, top-left-origin reading of `box` is measured, not stated by the schema; confirm it with the policy-engine owners before a consumer reads these files.
