# Summary and Context Guide

Both files are optional. Each is a JSON object. Write at most one summary and one context per ontology. If you are not sure a file adds value, leave it out.

| File | Artifact type | Media type |
|---|---|---|
| `{name}-summary.json` | `summary` | `application/json` |
| `{name}-context.json` | `context` | `application/json` |

Add them with `uip ont files add`. Pass `--type summary` or `--type context` if the CLI cannot work out the type from the file name. Run `uip ont artifacts check <file-name> --content-type application/json --type <summary|context> --file <path>` first.

---

## Summary: `{name}-summary.json`

A short description of the ontology for the agent or person who reads it. It is JSON, **not** text: a `.txt` summary is rejected. The top level must be an object (not an array or a string).

```json
{
  "name": "SalesOps",
  "description": "Customers and the sales orders they place.",
  "classes": [
    { "name": "Customer", "grain": "ONE row per customer." },
    { "name": "SalesOrder", "grain": "ONE row per order." }
  ],
  "relationships": [
    "SalesOrder placedBy Customer (SalesOrder.customer = Customer.Id)"
  ]
}
```

Keep it short and take every fact from the confirmed domain model. Do not put anything in it that the schema does not say.

---

## Context: `{name}-context.json`

A JSON-LD `@context` that maps short terms to ontology IRIs. The file is a JSON object with a root `@context` key.

```json
{
  "@context": {
    "@base": "https://ontology.uipath.com/SalesOps#",
    "ont": "https://ontology.uipath.com/SalesOps#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "orderDate": { "@id": "ont:SalesOrder.orderDate", "@type": "xsd:dateTime" },
    "totalAmount": { "@id": "ont:SalesOrder.totalAmount", "@type": "xsd:decimal" },
    "placedBy": { "@id": "ont:placedBy", "@type": "@id" }
  }
}
```

Rules:

- Root key is `@context`.
- `@base` is on `https://ontology.uipath.com/`, and matches the schema IRI of this ontology.
- Declare the `xsd` prefix.
- Every term has both `@id` and `@type`.
- A term for a relationship (object property) has `"@type": "@id"`.
- A term's `@id` uses the ontology prefix (`ont:`).
- Use only terms that are declared in the schema.
