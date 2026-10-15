# Publish corpus

PDDs (and two PDD + SDD pairs) produced by Cartographer's own eval suite (Scribe,
coder-evalboard run 2026-09-29_03-14-04; the SDD pairs from adhoc-2026-10-09_17-38-45),
staged as `*-template.*` so `_setup/seed_publish.py` stamps each run's reference token
into the title.

- **Synthetic** sets (fictional organizations) are as Scribe wrote them, plus the token.
- **Customer-scenario** sets are anonymized: organization, customer-internal system,
  agency and person names replaced with fictional ones; commercial products kept.
  Only names changed; structure, tables and figures are as generated.

Each folder is one dataset row in `../corpus.jsonl`; its answer key is
`../expected/<id>.json`, which lives outside the sandbox. When adding a set, add all
three and run `pytest tests/tasks/uipath-automationhub/publish_from_pdd_corpus`.

`README.md` is not a template, so it is copied into the sandbox but never rendered.
