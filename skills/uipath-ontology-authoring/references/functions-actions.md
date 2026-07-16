# Functions and Actions — see uipath-ontology-modeler

Functions (SPARQL read queries) and Actions (SQL write operations) patterns are maintained in a single place:

**`uipath-ontology-modeler` skill → `functions-patterns.md`**

Path: `skills/uipath-ontology-modeler/functions-patterns.md`

Do not duplicate patterns here. The authoring skill delegates all artifact generation to the modeler skill. Refer to the modeler's `functions-patterns.md` for:

- File header format and comment block
- Function template (with and without parameters)
- SPARQL patterns: count with filter, aggregate per group, join across classes
- rdfs:comment guidance for AI-usable descriptions
- Action template (one file per action, `ont:statements` plural)
- SQL statement syntax (`{{Entity}}`, `{{Entity.field}}`, `:paramName`)
- Full clinic examples (functions.ttl and updatePrescriptionStatus.ttl)
- Common mistakes
