# Document Guide

How Stage 2 runs in Document mode: the input is an SDD, PDD, design document or domain specification. The model is confirmed one table at a time (concepts, then properties and relationships, then labels), and each confirmed table is saved to `<WORKDIR>/input/model.md` before the next ([SKILL.md](../SKILL.md#saved-model)). Types, names and relationship rules are the ones in [entity-guide.md](entity-guide.md) and [relationships-guide.md](relationships-guide.md); this guide adds only how a document maps onto them.

---

## Read the document

The document is a file path, a Confluence URL or pasted text. Read it before asking anything else, and take from it:

- the **class names**, first;
- any **entity definitions or field lists** (tables, JSON bodies, column lists): a definition given in full is `supplied` and used verbatim, fields described in words are `described` ([entity-guide.md](entity-guide.md#how-a-definition-is-treated));
- **value lists**, which become choice sets;
- **external data sources**: a system, connector and connection the document names. A source with no connection name means asking for the connection and the folder that holds it.

Anything you propose from the domain rather than read from the document is `generated`: show it for confirmation.

---

## Table 1 — Business concepts

| Class | Entity name | Domain | Description (one line) | Synonyms | Subclass of |
|---|---|---|---|---|---|
| `Doctor` | `Doctor` | Care team | Medical practitioner licensed to treat patients | physician, doc | — |
| `Prescription` | `Prescription` | Treatment | A medication order issued by a doctor | script | — |

The entity name defaults to the class name and follows the entity-name rules in [entity-guide.md](entity-guide.md#xsd-to-data-fabric-type). Check it while the user approves this table: a document concept called "Order" or "Group", or a C# or VB keyword (`Case`, `Class`, `New`), gets a domain name (`SalesOrder`, `MaintenanceCrew`), and the class label may still say "Order".

The **domain** is the business area the viewer groups the class under ([owl-patterns-guide.md](owl-patterns-guide.md#domain-annotation)). Take 3–7 from the document's sections or process stages (`Master data`, `Purchasing`, `Intake`), give every class exactly one, and spell each the same way across its classes. Group by business area, not by source system.

| Document phrase | Model construct |
|---|---|
| "a/an X", "each X", "X is a" | New class |
| "also known as / aka / alias" | `skos:altLabel` on the class |
| "Y is a type of / subtype of Z", and Y has fields of its own | `SubClassOf(:Y :Z)`; Y gets its own entity |
| "Y is a type of Z", and Y has no fields of its own | Not a class: a choice-set value on Z (`Customer.tier` = `Premium`) |

**A subclass needs its own entity** (`XF-009`: every class is a property domain mapped over its own entity). A subtype with no fields of its own becomes a choice-set value on its parent.

**Not every noun is a class.** An actor, role or system named only in the narrative ("the AP Clerk captures the invoice"), with no fields and no entity, fails `XF-009`. Fold it into the relevant property's `rdfs:comment` instead (`Payment.approvedBy`: "The Accounts Payable Manager who approved this payment.").

---

## Table 2 — Properties and relationships

**Data properties.** Types per [entity-guide.md](entity-guide.md#xsd-to-data-fabric-type); field names follow its field-name rules (no underscores, none of the reserved or system field names).

| Class | Property name | XSD type | Data Fabric type | Required? |
|---|---|---|---|---|
| `Doctor` | `Doctor.licenseNo` | `xsd:string` | `STRING` | required |
| `Prescription` | `Prescription.quantity` | `xsd:integer` | `DECIMAL` (`decimalPrecision: 0`) | — |
| `Prescription` | `Prescription.status` | `xsd:string` | `CHOICE_SET_SINGLE` (`PrescriptionStatus`) | required |

Property names are `{ClassName}.{propName}` in camelCase, never `has{Prop}`.

**When you propose a `FILE` field, tell the user what it costs on upgrade:** a solution with a `FILE` field is refused on every later upgrade (`TypeIncompatible`), and `uipath-solution` finishes that upgrade by keeping the installed entity, so fields added to or changed on that entity in a later version are not applied. Ask the user to confirm the field with that in mind.

**Choice sets**, one per fixed value list:

| Choice set | Values (in order) | Used by | Select |
|---|---|---|---|
| `PrescriptionStatus` | `Active`, `Cancelled`, `Filled` | `Prescription.status` | single |

Value names are letters and digits and start with a letter. A property that allows several values uses `CHOICE_SET_MULTIPLE`.

**Object properties (relationships)**, one `RELATIONSHIP` field on the referencing entity each ([relationships-guide.md](relationships-guide.md)):

| Property | From | To | Relationship field | To column | Cardinality | Notes |
|---|---|---|---|---|---|---|
| `prescribedBy` | `Prescription` | `Doctor` | `doctor` (`RELATIONSHIP` on `Prescription`) | `Id` | exactly one | inverse: `prescribes` |
| `treatedAt` | `Visit` | `Clinic` (federated) | `clinicKey` (plain column) | `ClinicKey` | exactly one | federated target |

Use a reference field name the document gives; otherwise propose one and ask.

**Federated sources**, only when the document names external data a class reads:

| Entity | Source | Connection name | Object | Fields | Joins |
|---|---|---|---|---|---|
| `Clinic` | connector `<CONNECTOR_KEY>` | `<CONNECTION_NAME>` | `<OBJECT_NAME>` | `ClinicKey`, `Name` | — |

| Document phrase | Model construct |
|---|---|
| "X has a/an Y" | Data property `{X}.{propName}` |
| "X is linked to / belongs to Y" | Object property from X to Y, one relationship field on X |
| "X must have a Y" | Object property, required |
| "each X has exactly one Y" | Object property, exactly one |
| "X can have many Y AND Y can be shared across many X" | Junction class with its own entity ([relationships-guide.md](relationships-guide.md#many-to-many)); flag it to the user |
| "X can have many Y" (Y owned by one X) | Object property on Y pointing at X, no cardinality |
| "X is one of / has a status of A, B, C" | Choice set with those value names |
| "inverse of" | `InverseObjectProperties`, plus `SubObjectPropertyOf` for a subproperty |

Required and cardinality rules go into the schema's `rdfs:comment` text (Critical Rule 16), not a constraints file.

---

## Table 3 — Labels, descriptions and synonyms

Show one table at a time (classes, then data properties, then object properties) and wait after each.

| Class | `rdfs:label` | `rdfs:comment` (grain first) | `skos:altLabel` |
|---|---|---|---|
| `Doctor` | `"Doctor"` | `"ONE row per doctor, keyed by Id."` | `"physician"` |

| Property | `rdfs:label` | `rdfs:comment` | `skos:altLabel` |
|---|---|---|---|
| `Prescription.status` | `"Status"` | `"Values: 'Active' \| 'Cancelled' \| 'Filled' (case-sensitive)."` | — |
| `prescribedBy` | `"Prescribed by"` | `"Each Prescription is prescribed by one Doctor. Join: Prescription.doctor = Doctor.Id."` | — |

| Fact type | `rdfs:comment` form |
|---|---|
| Plain meaning | `"{What this field stores.}"` |
| Value domain (choice set) | `"Values: 'A' \| 'B' \| 'C' (case-sensitive; copy exactly)."` |
| Code list | `"'A' = meaning \| 'B' = meaning. '{Phrase}' means code IN ('A','B')."` |
| Format / scale | `"Stored 0–1 fraction; multiply by 100 for a percent answer."` |
| NULL with condition | `"NULL for ~N rows. NULLs sort last in DESC."` |
| Boolean | `"Compare true/false, never 1/0."` |

Keep domain facts (meaning, grain, value domains) in these comments, required and range rules in the property comments, and query or join guidance as its own sentence.

---

## What a document may ask for that this skill does not build

| The document asks for | Do |
|---|---|
| Query functions, write actions or business rules | Say they are not produced; record business constraints as schema comments |
| An external system with no connection named | Ask for the connection name and the folder that holds it |
| A class, field, join column, choice-set value or identifier with no unique answer | Stop and ask (`BLOCKED_AMBIGUITY`) |
