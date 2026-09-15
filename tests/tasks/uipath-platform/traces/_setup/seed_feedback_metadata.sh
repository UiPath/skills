#!/bin/sh
# Seeds the structured review payload traces_feedback_metadata_smoke.yaml expects
# in the sandbox: a nested JSON document too large to retype on the command line.
set -eu

cat > review-meta.json <<'JSON'
{
  "reviewer": "qa-sweep",
  "round": 3,
  "rubric": {
    "grounding": 2,
    "completeness": 4,
    "tone": 5
  },
  "sampledFrom": ["monthly-export", "escalation-queue"],
  "notes": "Totals line was dropped on two of the five sampled documents."
}
JSON

echo "OK: seeded review-meta.json"
