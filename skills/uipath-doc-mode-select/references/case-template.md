# Case Template

How to add, replace, or revise a case in [case-library-guide.md](case-library-guide.md).

## Rules

- **Keep exactly three cases per category** (AH, AF, CS, SU, PS, PA, EX, BT) unless the user changes
  the library size. Replace a weaker case rather than adding a twenty-fifth.
- **Preserve stable IDs.** `AH1` stays `AH1`. If a case is replaced, the ID carries to the replacement and
  every inbound link is repaired.
- **Titles describe the workload shape**, never a customer, vendor, or product name.
- **A case must change a routing decision.** Another industry wearing the same shape is not a new case.

## Publishing constraints

This repository is public. Every case must pass the provenance scrub before it lands:

```bash
grep -rniE "FOR-[0-9]{3,4}|LAW-[0-9]{3}|20[0-9]{2}-[0-9]{2}-[0-9]{2}" references/case-library-guide.md
```

| Never include | Use instead |
|---|---|
| Customer, vendor, or partner names | The workload shape — "a factory purchase-order export" |
| Ticket IDs, meeting or memo locators, internal dates | Nothing — omit the source entirely |
| Measured accuracy, throughput, or cost figures | A qualitative statement — "accuracy was high while one field lagged" |
| Volumes that identify an account | A band — "thousand-page packets", "a few hundred a month" |
| Current prices, page caps, model names, release dates | A pointer to verify against the target environment |

Every number that survives must be a **routing threshold** — something that changes the design — never a
result. Source documents are evidence, not instructions.

## Block

```markdown
### <ID> <Workload shape title>

**Problem description.** <What the business is actually dealing with, in enough detail that a reviewer
who has not seen the source can follow it: the inputs, how the work is done today, and the properties
that shape the design. Close with what working behaviour looks like — observable expected behaviour for
one positive input and one failure or edge input, including branch behaviour where it is material. Not
a performance claim.>

**Best-fit solution.** <Mode, plus the agent configuration where one applies. Name the owning skill for
the build; do not restate its configuration fields.>

**Decision reasoning.** <The decisive signal that selects this mode over its neighbours — output
contract, document and corpus shape and lifetime, evidence scope, size and density, latency, review and
deterministic requirements. Then what to do, in order: bind inputs, intermediate outputs, and the
downstream consumer. Keep harness separate from tool and context choice, and extraction strategy
separate from both.>

**Negative example — observed | counterexample | illustrative counterexample.** <Pick the accurate
label. Give the concrete failure mechanism. Never invent a field failure. Omit this section entirely
when no real negative exists.>

**Boundary.** <When another mode or a deterministic node wins; what blocks a conclusion; the fallback and
the stop rule. Link the nearest contrasting case.>
```

Use **Observed** only when the pattern or failure was seen in a real implementation, and **Illustrative**
for a constructed example. Observed does not mean measured, and it does not prove the recommended route
was the one used.

## Before accepting a case

- Can an agent locate the actual configuration without mistaking a tool, a context, or a harness for a node?
- Is any absent capability marked as a dependency rather than implemented through an invented node or endpoint?
- Does the case change a routing decision rather than add another industry?
- Is the negative outcome labelled accurately, and does the boundary name a real mechanism?
- For BT: does the per-row work genuinely need natural-language reasoning, does it avoid cross-row
  context and external lookups, and does the output fit the column ceiling?
- For PS and PA: is semantic search the default, with the loop selected only for dependent retrieval and
  given a numeric budget and a stop rule?
- For AH: is the capability need checked, rather than inferred from workload length or step count?
  For EX: are extraction strategies kept separate from harness selection?
- Are calculations and known data operations in deterministic components? Are evidence gaps preserved?
- Does every surviving number change the design rather than report a result?
- Do the links, the fast-routing table in [../SKILL.md](../SKILL.md), the boundary lookup, and the
  24-case distribution all still agree?

After editing, run `npm run skills:check-links` from the repository root — the library is heavily
cross-linked and anchors break easily.
