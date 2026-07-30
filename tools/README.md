# Shared Ontology Tools

This directory contains repository-level utilities shared by the UiPath ontology skills.

## `ontology_preflight.py`

`ontology_preflight.py` is the neutral, dependency-free validator for ontology artifact workdirs. It is shared by:

- `uipath-ontology-authoring`, which owns deployment orchestration and invokes preflight before backend creation or upload;
- `uipath-ontology-modeler`, which uses it to validate locally generated artifacts before handing them back.

The validator does not log in, call UiPath Cloud, create ontology stubs, upload files, or change user data. It reports JSON gates and an exact artifact inventory.

Run it from the repository root:

```bash
python3 tools/ontology_preflight.py \
  --workdir <ontology-workdir> \
  --ontology-name <ontology-name> \
  --mapping-mode auto
```

Keep this utility at the repository level. Do not place it inside either sibling skill; doing so would create an unnecessary structural dependency between the skills.
