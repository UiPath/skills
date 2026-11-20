# Citation Guide

Read when a `dom.json` with page positions exists. A row's position in the policy comes from a verbatim quote that code resolves to a box. The model never produces coordinates (extraction rule 5). Citations of supporting documents are in [multi-document-guide.md](multi-document-guide.md); a rule with no quote is in [guided-guide.md](guided-guide.md) (Extraction).

## Record a citation (Extraction)

Record each citation in `<TEMP_DIR>/cites.json` as the guided guide says (Extraction, Do). With a `dom.json`, two points matter for resolving:

- `page` is the `<!-- page: N -->` marker, which equals `dom.json` `pageIndex` + 1.
- A quote may cross a line break. If a multi-line quote does not resolve, retry with a fragment from a single line of the clause.

## Resolve (Finish)

```bash
node "<SKILL_DIR>/scripts/extraction/resolve-refs.mjs" --dom <DOM_JSON> --cites <TEMP_DIR>/cites.json
```

Stdout is one JSON object: `status`, `resolved`, `unresolved`, `ambiguous` (counts), and `results[]`. Each result has `id` and `status`:

| `status` | Meaning | Action |
|---|---|---|
| `resolved` | One match. `page` and `box` (`left,top,width,height`) are set. | Write a `uipdm:sourceRef`. |
| `ambiguous` | The quote matches several places; `candidates[]` lists each page and box. | Re-run with a longer quote, or choose the candidate whose neighbouring text fits the clause. |
| `unresolved` | The words are not on the cited page (or on any page when the page was absent). Typical causes: paraphrase, line-break hyphenation, wrong page. | Copy the quote again from `document.md`; if it still fails, write a `uipdm:qualityWarning` and leave `sourceRefs` out for that row. |

Exit 2 is a usage error: fix the arguments. Run it once more after fixing quotes; never hand-edit a box.

## uipdm elements

Elements, their placement, the page-only form for a run with no digitizer positions, and the schema check are in the [uipdm guide](../uipdm-guide.md). Extraction adds: write `uipdm:sourceRefs` only in Finish (Extraction records `cites.json` and nothing else); do not put the quote in the file; and list the citations that carry no box in the Finish summary.
