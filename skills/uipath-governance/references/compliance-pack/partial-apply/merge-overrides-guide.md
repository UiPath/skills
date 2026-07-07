# merge-overrides — usage

Deep-merges compliance pack overrides onto a base formData object (template defaults for new policies, or
existing deployed policy data for subset updates). Output is ready to pass directly to
`uip gov aops-policy create|update --input`.

**Script (shipped, executable):** `<SKILL_DIR>/scripts/merge-overrides.mjs`
(`<SKILL_DIR>` = the folder containing this skill's `SKILL.md`). Run it in place — do NOT recreate it.

```bash
node "<SKILL_DIR>/scripts/merge-overrides.mjs" \
  --base      "$SESSION_TEMP/products/<product>/form-data.json" \
  --overrides "$SESSION_TEMP/overrides/<product>.json" \
  --out       "$SESSION_TEMP/merged/<product>.json" \
  --summary
```

`--summary` prints the list of overridden paths — useful for confirming which compliance pack settings
were applied.

**Merge rules:**
- Objects → recursive key-by-key merge
- Arrays → wholesale replace (override wins; `[]` is a deliberate clear)
- Scalars → replace
- Explicit `null` → clear that leaf
- Paths the override doesn't touch → kept from base

**Exit codes:** `0` = merged file written · `2` = missing or malformed inputs.
