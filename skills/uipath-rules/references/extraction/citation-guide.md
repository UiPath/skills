# Citation Guide

A row's position in the policy comes from a verbatim quote that code resolves to a box. The model never produces coordinates (extraction rule 6).

## Record a citation (Extraction)

Append one entry per place a row was read to `<TEMP_DIR>/cites.json`:

```json
[{ "id": "r1", "page": 1, "quote": "Employees with less than six months of service" }]
```

- `id` is the row's annotation name plus a number if the row has several cites, e.g. `under-six-months-1`.
- `page` is the number in the `<!-- page: N -->` marker in `document.md` (it equals `dom.json` `pageIndex` + 1), never the printed number in a header or footer. Header and footer lines (for example `Page 3 of 69`) sit inline in the body text; skip them when copying a quote.
- `quote` is copied character for character from `document.md`, about 4-12 words, taken from the clause itself. A threshold alone (`$250,000`) appears many times; include its neighbouring words.
- A row built from several clauses gets one entry per clause.
- A quote may cross a line break. If a multi-line quote does not resolve, retry with a fragment from a single line of the clause.

## Supporting-document citations

Only the base document has a `dom.json` and `cites.json` entries. A row built from an amendment, higher-authority source, guidance, or reference data names the source in its annotation as `<DOCUMENT_NAME> p.<N> "<verbatim quote>"`, copied from that document's text. Add no `cites.json` entry and no `uipdm:sourceRef`: `resolve-refs.mjs` reads one `dom.json`, and a page number from another document would resolve to the wrong box. List these citations in the Finish summary as carrying no box. A row that combines a base clause and a supporting clause cites the base clause normally and the supporting one in the annotation.

## Rules with no quote (user-stated)

A rule that comes from a user's answer or a call, not from the document, has no clause to quote. Do not invent a quote and do not add a `cites.json` entry. Write a `uipdm:qualityWarning` on the row (`conditionId` or `field` set when known) with text starting `User-stated, not in document:` followed by the rule and who stated it. Ask the user to get it confirmed in writing, and list it in the Finish summary.

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

Elements, their placement, the page-only form for a run with no digitizer positions, and the schema check are in the [uipdm guide](../uipdm-guide.md). Extraction adds: write `uipdm:sourceRefs` only in Finish (Extraction records `cites.json` and nothing else); with no `dom.json`, write one page-only `sourceRef` per distinct page a row cites; do not put the quote in the file; and list the citations that carry no box in the Finish summary.
