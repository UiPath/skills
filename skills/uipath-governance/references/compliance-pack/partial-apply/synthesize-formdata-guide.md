# synthesize-formdata — usage

Extracts compliance pack catalog contributions for a given product + clause subset and writes them as a
flat formData overrides object.

**Script (shipped, executable):** `<SKILL_DIR>/scripts/synthesize-formdata.mjs`
(`<SKILL_DIR>` = the folder containing this skill's `SKILL.md`). Run it in place — do NOT recreate it.

```bash
node "<SKILL_DIR>/scripts/synthesize-formdata.mjs" \
  --catalog    "$SESSION_TEMP/catalog.json" \
  --product    "<productIdentifier>" \
  --clause-ids "<clauseId1,clauseId2,...>" \
  --out        "$SESSION_TEMP/overrides/<product>.json"
```

**Exit codes:** `0` = written · `2` = bad args · `3` = no contributions for product+clauses (skip this
product, continue).

**Warnings on stderr:** the script uses `console.warn` (→ stderr, not stdout). Lines starting with `⚠`
indicate controls whose values are org-specific (`notEmpty`) or are access-policy checks (`exists`) —
collect those values from the user before proceeding (see [impl.md](impl.md) Step 1b).
