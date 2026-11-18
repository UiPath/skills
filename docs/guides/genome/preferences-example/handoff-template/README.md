# Hand-off report template

`handoff-report-template.html` is a standalone sample of the hand-off page the [example preferences](../migration-preferences.md) ask for: one file, a calm dark-blue theme, a tab per report with a count badge, a filter box (match count, Clear button), sticky table headers and Mermaid diagrams. Open it in a browser to see it with placeholder data. Without JavaScript the page shows only a short "needs JavaScript" line; diagrams use Mermaid 10.9.1 from a public CDN, and without a network the diagram text is shown instead.

A generator fills in three places and touches nothing else:

1. `<title>` (browser tab title).
2. `<h1 id="page-title">` (put the accent-coloured part in a `<span>`) and `<p class="sub-title" id="page-subtitle">`.
3. The block `<script type="application/json" id="report-data"> ... </script>`. The page builds the tabs, counts, tables and diagrams from it. Escape `<`, `>` and `&` inside the JSON as `<`, `>`, `&`, so a value can never close the script tag.

## The data block

```json
{ "notice": "optional text above the tabs", "footer": "optional text under the last report",
  "reports": [ { "id": "optional-slug", "title": "Tab name", "intro": "optional sentence",
      "columns": ["Plain name", {"name": "Wide column", "wide": true}],
      "rows": [ ["cell", {"text": "cell shown in amber", "tone": "warn"}] ],
      "empty": "optional text when the report has no rows" },
    { "title": "Overview", "markdown": "# Title\n\n## Heading\n\nA paragraph with **bold** and `code`.\n\n- a bullet" } ] }
```

Report keys, all optional except `title`:

- `columns` and `rows`: a table with a filter. A column is a string or `{name, wide}` (`wide` gives a text column more room). A cell is a string, a number, or `{text, tone}` (`tone: "warn"` shows the text in amber). Every row has one cell per column. The first column is shown in the accent colour.
- `groups`: instead of `rows`, a list of `{name, rows, empty}`. Each group is a pill-shaped sub-tab with its own count and the shared `columns`; the filter applies to the group on show. A group with no rows shows its `empty` text.
- `diagrams`: a list of `{title, mermaid}` shown side by side (Mermaid flowchart text, `\n` for line breaks). A report can have diagrams and a table, or diagrams and groups (Process components does).
- `markdown`: instead of `columns`, `rows` and `groups`, a page of Markdown text (the Overview is one). The page renders it with a small built-in renderer: headings (`#` to `####`), paragraphs, bullet and numbered lists, `**bold**`, `*italic*`, `` `code` `` and `[links](https://...)`. Everything else, including any HTML, is escaped and shown as plain text; a link is only made for `http`, `https`, `mailto` and `#` addresses. A Markdown report has no filter and its tab shows no count. The text is limited to about 760 pixels wide for easy reading and uses the page's own colours. A generator writes the same text to a `.md` file beside the report, and gives the Excel file no sheet for it.
- `notes`: `[{title, items: [text]}]` and `legend`: `[text]`, shown under the diagrams. `table_title`: a heading above the table that follows the diagrams.

The badge of a tab is the number of rows (all groups added up); a report that only has diagrams shows the number of diagrams; a Markdown report shows no badge. `id` becomes the page anchor (`#workflow-map`); it defaults to a slug of `title`. Text is always escaped, so a cell cannot carry HTML. Line breaks in a cell are kept. Tabs switch with the left and right arrow keys, and each tab button points (`aria-controls`) to its section.

## The nine reports, in order

1. **Overview**: a Markdown page of about 600 to 1000 words: what the solution does, how it runs from start to finish, what changed from the source and why, what operations need to know, where to look next. Headings, short paragraphs and a few bullet lists; no migration internals.
2. **Workflow map**.
3. **Variables**.
4. **Design decisions**: the decisions taken about how the solution is built, each with its reason and where it applies; columns Topic, Decision, Why, Applies to. No configuration answers, preferences or review findings: their values are under Deployment open items.
5. **Defect register**.
6. **TODO list**. Live checks: one row per UI library ("verify this library's screens on the live application"), not one per target.
7. **Deployment open items**: groups Set-up, Packages, Queues, Entities, Triggers, Assets, Credential assets, Settings, Deployment notes, and a Type column. An Entities row has the field list and, after one plain line, the entity's definition JSON. In Assets, Credential assets and Settings, Used by names each process with the workflows that use the value, at most three, then `+N more`, or `(not used in any workflow)`.
8. **Structural deviations**: groups Added, Removed, Changed.
9. **Process components**: an original and a migrated diagram of processes and queues only, no libraries or components they call, the nodes carrying the process names (the source's name in the original, the UiPath project name in the migrated); then the groups Components and links, and Queues and data stores. The second holds the queue rows and one row per Data Fabric entity: why it exists, what it holds, which projects use it.

The sample shows the Overview with placeholder prose and each of the others with its columns and two or three placeholder rows. "Removed (not migrated)" in Structural deviations is the empty-state example; typing a word that matches nothing in a filter shows the other empty state.

The Excel file holds the eight data reports, one sheet each. The Overview is also written as a `.md` file beside the report, and so are the open items, in a second `.md` file generated from the same rows as their two tabs: Deployment open items, with the entities' definition JSON in code blocks, and the TODO list grouped by project.
