# uipath-ixp replace-taxonomy fixture

Stages `new-taxonomy.json` at the sandbox root — a taxonomy file the user
"hands over", in the `{ entity_defs, label_groups }` import format. Used by
`../../smoke/replace_taxonomy_from_file.yaml`, which explains the scenario.

Two things a future edit can silently break:

1. **`Invoice Total` must keep `field_id` `6e0b74a1f83c2d95`** — the id of
   `Total Amount` in the taxonomy that task serves from its `get-taxonomy`
   response rule. Same id + different name is what makes it a rename.
2. **`Total Amount` must appear only in that served response, never here or in
   the prompt.** The graded `fields rename` asserts the old name, which is what
   proves the agent diffed rather than applying the file wholesale.
