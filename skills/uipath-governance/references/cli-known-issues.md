# CLI Known Issues

Live bugs / sharp edges in `@uipath/aops-policy-tool` that affect this skill.

## ~~1. Missing `--input` path returns misleading 404~~ — FIXED

The CLI now validates `--input` before the API call and surfaces `"Data file not found: <resolved path>"`. Verified against the updated commit.

## 2. `policy update` is a full-replace — omitting optional flags clears server-side fields

**Behavior:** `update` requires `--identifier`, `--name`, `--product-name`. The remaining flags (`--description`, `--priority`, `--availability`, `--input`) are optional at the CLI level, but per the CLI's own description text, **omitting any of them clears that field on the server**. There is no partial-patch mode.

**Impact on skill:**
- **CREATE path:** The creation plugin always passes all flags from the pack — safe.
- **UPDATE path:** If the caller is patching only `formData` (e.g., diagnosis fix), they must still re-pass the current `--description`, `--priority`, `--availability`, otherwise those get wiped. Workaround documented in [policy-crud.md UPDATE recipe](policy-crud.md#update-recipe): always read current metadata + data via `aops-policy get` and pass them through unchanged.

**Status:** This is documented CLI behavior (not a bug), but it is a sharp edge — the skill treats all four flags as effectively required on update.

## 3. Never pipe `uip` output through `head` / `tail` / `less`

**Symptom:** `uip gov aops-policy list --output json | head -20` crashes with `EPIPE` or "broken pipe" — the CLI's terminal sink throws when its stdout is closed early.

**Impact:** truncates or obscures the actual JSON response; in some shells the non-zero exit aborts your downstream script.

**Workaround:** always redirect `uip` output to a file first, then inspect the file with whatever viewer you want.

```bash
# ❌ breaks
uip gov aops-policy list --output json | head -50

# ✓ works
uip gov aops-policy list --output json > /tmp/policies.json
head -50 /tmp/policies.json
# or use jq:
jq '.Data.result[0:5]' /tmp/policies.json
```

## 4. `template get --output-form-data` pollutes stdout with a large JSON envelope

**Symptom:** `uip gov aops-policy template get <product> --output-form-data <file>` writes the fillable blueprint to `<file>` (correct) AND prints the full template tree — including the i18n bundle — to stdout (100 KB+ for products like AITrustLayer).

**Impact:** floods agent context and terminal. Every stray byte lands in the conversation.

**Workaround:** redirect stdout to `/dev/null` — you already have the payload you care about in `<file>`.

```bash
uip gov aops-policy template get AITrustLayer \
  --output-form-data "$tmp/defaults.json" \
  --output json > /dev/null
```

Same applies to `--output-template-locale-resource <file>` and the bulk `template list --output-dir <dir>` variants.
