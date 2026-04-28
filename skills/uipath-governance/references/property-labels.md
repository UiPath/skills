# Property Labels — human-readable descriptions for AOPS policy fields

Technical field names in `formData` (e.g., `azure-openai-control-toggle`, `pii-processing-mode`) aren't how admins think about their policies. The skill renders a human label next to every technical key in diagnosis findings, advise plans, and patch/deploy record summaries. Labels come from the AOPS i18n bundle, fetched at runtime from the CLI.

## Runtime fetch — the only source

```bash
uip gov aops-policy template get <productIdentifier> \
  --output-template-locale-resource <tmp>/locale-<productIdentifier>.json \
  --output json
```

Each resolved property gets a `{prop}-key` sibling that preserves the original locale key for traceability. `defaultData.data` in the output is a flat `{ value, type, label, description?, tooltip? }` map keyed by component key.

Fetch once per product per session when labels matter (the template data is cached server-side and the response is small — a few KB per product).

## When to use

Any time the skill presents a property name to the user — diagnosis findings, advise plans, deploy-record summaries, patch-record diffs. Look up the human label; fall back to the raw key if no entry exists.

| Capability | Where |
|---|---|
| Diagnose | Step 4 finding lines, Step 5 diff preview, Step 7 patch record |
| Advise | Step 4 plan presentation, deploy/patch records |
| Apply | Optional — pre-flight confirmation, deploy record summary |

## Lookup convention

Keys in the locale resource are namespaced as `<Product>.<property-key>-<suffix>` where `<suffix>` is one of:
- `-label` — short title (always prefer this for display)
- `-description` — long-form explanation (use as a tooltip or under the label)
- `-tooltip` — alternative short hint
- (no suffix) — enum values, panel titles, simple words

### Standard transformation (formData path → label key)

For a formData path like `azure-openai-control-toggle` under product `AITrustLayer`:

1. **Try direct match first:** `AITrustLayer.azure-openai-control-toggle-label`
2. **Then try the "drop `control-` before `toggle`" variant:** `AITrustLayer.azure-openai-toggle-label` ✓
3. **Fall back:** show the raw key

### Nested paths

For nested paths like `container.pii-in-flight-agents`, `harmful-content-container.harmful-content-in-flight-agents`, `allowed-llm-regions.europe`:

1. **Try the full leaf key with `-toggle-label` suffix:** `AITrustLayer.pii-in-flight-agents-toggle-label` ✓
2. **The container prefix is usually dropped** in the i18n key. Keep the leaf segment after the last dot.
3. **Region keys** (`allowed-llm-regions.europe`, `.united-states`, `.japan`) are NOT individually translated — the parent has a panel label, but each region uses the raw key. Render with title-case as a fallback: `Europe`, `United States`.

### Enum values

For string enums (e.g., `pii-processing-mode: "DetectionAndMasking"`), look up the value as a label too:
- `AITrustLayer.pii-mode-masking` → "PII Masking"
- `AITrustLayer.pii-mode-detection` → "PII Detection"
- `AITrustLayer.execution-stage-pre` → "Pre"
- `AITrustLayer.execution-stage-post` → "Post"

If no match, show the raw value.

## Presentation format

Always combine the label with the technical key for precision:

```
[Label] (technical-key): value
  ← reasoning
```

Example:
```
MOST LIKELY (1 finding):
  Open AI (azure-openai-control-toggle): Off
    ← gpt-4o-2024-11-20 is an Azure OpenAI model; provider is disabled
    Description: Disabling models will impact genAI features across products
```

For boolean values:
- `true` → display as `On` / `Enabled` / `Yes` per context
- `false` → display as `Off` / `Disabled` / `No`

## Coverage

The locale resource is emitted per product from the live AOPS template bundle — coverage mirrors whatever the AOPS team has localized. Empirically complete for AITrustLayer, Assistant, AssistantWeb, Business, Development, Automate, StudioPro. Partial or missing for Robot, StudioWeb, IntegrationService at time of writing; if a lookup fails for those, fall back to the raw key.

## Unresolved i18n references — treat as missing

The locale API sometimes returns the locale KEY itself as the "value" instead of a translated string (e.g., `allowed-llm-regions-label` resolves to `"AITrustLayer.allowed-regions-label"` — the i18n reference, not "Allowed LLM Regions"). Displaying this verbatim produces meaningless noise like:

```
❌  AITrustLayer.allowed-regions-label (allowed-llm-regions):  Off
```

**Detection rule.** Consider the returned value an unresolved reference (and fall back) when it matches this pattern:

```
^[A-Z][A-Za-z0-9]+(\.[a-z0-9][A-Za-z0-9-]*)+(-(label|description|tooltip))?$
```

In plainer terms: it begins with the product identifier (PascalCase), contains dot-delimited kebab-case segments, and optionally ends with one of the known label suffixes. If it matches, treat the lookup as **failed** — fall through to:

1. Title-case the leaf segment of the formData path (`allowed-llm-regions.europe` → `Europe`; `pii-processing-mode` → `Pii Processing Mode` → hand-tuned to `PII Processing Mode` only when the skill ships a manual override).
2. If the path has no meaningful leaf, fall back to the raw path string inside code ticks.

Never render the unresolved reference as-is in user-facing output, patch records, or deploy records. The `label` field in audit records stays empty (or takes the title-case fallback) so consumers downstream can choose their own render.
