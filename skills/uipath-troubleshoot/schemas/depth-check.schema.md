# Depth Check Schema

File: `.local/investigations/depth-check.json`

Written during: DEPTH CHECK
Read during: RESOLUTION (verdict + gaps surfaced in the final output)

## Structure

```json
{
  "schema_version": "1.1",
  "verdict": "verified",
  "hypothesis_id": "H1",
  "playbook_path": "<path from state.json.matched_playbooks>",
  "named_cause": "<verbatim or quoted paraphrase from the playbook's 'What can cause it' list>",
  "evidence_for_cause": [
    "<file path under .local/investigations/evidence/ or .local/investigations/raw/>"
  ],
  "resolution_alignment": "matches",
  "gaps": [
    {
      "kind": "factual",
      "check": 2,
      "detail": "<one-line description of the gap>"
    }
  ]
}
```

## Rules

- `verdict`: `verified` | `shallow`. `shallow` requires at least one `gaps` entry
- `resolution_alignment`: `matches` | `mismatch` | `missing`
- `named_cause` quotes the playbook's cause list — a vague generalization fails check 1
- `evidence_for_cause` lists only files containing the datum that pins the cause (fresh-eyes rule: re-read from disk before writing)
- `gaps[].kind`: `factual` | `textual` — routing is on `kind`, not `check`. Factual → one more TEST round on the same hypothesis; textual → accept at `confidence: medium`, no re-test
- `gaps[].check`: `1`, `2`, `3`, or the string `"causal_precedence"` (a distinct identifier, not a fourth numbered check). Factual applies to check 2 only; textual applies to checks 1, 3, and `"causal_precedence"`
- One check yielding both factual and textual character (evidence missing AND cause paraphrased) → two separate gap entries, one of each kind
- Multiple hypotheses flagged `is_root_cause: true` → one entry per hypothesis as an array under a top-level `"checks"` key instead of a single flat object
