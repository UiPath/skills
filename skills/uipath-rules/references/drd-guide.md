# Decision Graphs

A rule holds one `.dmn`, and that file may hold more than one decision. Decisions linked by `informationRequirement` form a decision graph: the engine evaluates what a decision needs before the decision itself, and returns every decision's outputs in one run.

Read this when a request needs more than one answer, or when one answer feeds another. A single decision needs nothing here — author its table and stop.

## When to split

Split when the rule has to answer more than one question, or when one answer is an input to the next.

| Shape | One decision or several |
|---|---|
| The caller reads one value from one set of inputs | One decision |
| The caller reads two values the business decides separately — a risk band *and* an interest rate | One decision each |
| A value is decided once and read by two later decisions | Its own decision, required by both |
| One decision with a column the caller never reads, carried only to reach the next row | Still one decision; a column is not a decision |

Do not split a single answer across tables to make each table smaller. Each decision becomes an entry point a consumer can bind to, so every split is part of the rule's public shape.

## Skeleton

A two-decision graph. `rate` reads the band `risk` decides.

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<definitions xmlns="https://www.omg.org/spec/DMN/20230324/MODEL/"
             xmlns:dmndi="https://www.omg.org/spec/DMN/20230324/DMNDI/"
             xmlns:dc="http://www.omg.org/spec/DMN/20180521/DC/"
             xmlns:di="http://www.omg.org/spec/DMN/20180521/DI/"
             xmlns:uipath="http://uipath.com/schema/1.0/dmn/authoring"
             id="definitions_loan" name="LoanRules" namespace="http://uipath.com/dmn/ns_loan">
  <extensionElements>
    <uipath:authoring surface="decision-graph" />
  </extensionElements>

  <decision id="decision_risk" name="risk" label="Risk band">
    <extensionElements><uipath:authoring editor="decision-table" /></extensionElements>
    <variable id="variable_risk" name="risk" typeRef="string" />
    <informationRequirement id="informationRequirement_risk_creditScore">
      <requiredInput href="#inputData_creditScore" />
    </informationRequirement>
    <decisionTable id="decisionTable_risk" hitPolicy="FIRST">
      <input id="input_risk_creditScore" label="Credit score">
        <inputExpression id="inputExpression_risk_creditScore" typeRef="number">
          <text>creditScore</text>
        </inputExpression>
      </input>
      <output id="output_riskBand" label="Risk band" name="riskBand" typeRef="string" />
      <annotation name="Annotation" />
      <rule id="rule_risk_1">
        <inputEntry id="inputEntry_risk_1"><text>&lt; 580</text></inputEntry>
        <outputEntry id="outputEntry_risk_1"><text>"High"</text></outputEntry>
        <annotationEntry><text>Subprime</text></annotationEntry>
      </rule>
      <rule id="rule_risk_2">
        <inputEntry id="inputEntry_risk_2"><text>-</text></inputEntry>
        <outputEntry id="outputEntry_risk_2"><text>"Low"</text></outputEntry>
        <annotationEntry><text>Default</text></annotationEntry>
      </rule>
    </decisionTable>
  </decision>

  <decision id="decision_rate" name="rate" label="Interest rate">
    <extensionElements><uipath:authoring editor="decision-table" /></extensionElements>
    <variable id="variable_rate" name="rate" typeRef="number" />
    <informationRequirement id="informationRequirement_rate_risk">
      <requiredDecision href="#decision_risk" />
    </informationRequirement>
    <decisionTable id="decisionTable_rate" hitPolicy="FIRST">
      <input id="input_rate_risk" label="Risk band">
        <inputExpression id="inputExpression_rate_risk" typeRef="string">
          <text>risk</text>
        </inputExpression>
      </input>
      <output id="output_interestRate" label="Interest rate" name="interestRate" typeRef="number" />
      <annotation name="Annotation" />
      <rule id="rule_rate_1">
        <inputEntry id="inputEntry_rate_1"><text>"High"</text></inputEntry>
        <outputEntry id="outputEntry_rate_1"><text>12.5</text></outputEntry>
        <annotationEntry><text>High risk</text></annotationEntry>
      </rule>
      <rule id="rule_rate_2">
        <inputEntry id="inputEntry_rate_2"><text>-</text></inputEntry>
        <outputEntry id="outputEntry_rate_2"><text>6</text></outputEntry>
        <annotationEntry><text>Everything else</text></annotationEntry>
      </rule>
    </decisionTable>
  </decision>

  <inputData id="inputData_creditScore" name="creditScore">
    <variable id="variable_creditScore" name="creditScore" typeRef="number" />
  </inputData>
</definitions>
```

No `dmndi:DMNDI` element — see [The diagram](#the-diagram).

## Reading an upstream decision

**A decision reads another decision by that decision's `variable` name, never by its output column name.** Above, `rate` reads `risk`, not `riskBand`. This is the mistake a graph most often ships with, and nothing in the file looks wrong: the column name is right there in the upstream table, and a wrong read is a valid FEEL name the engine simply cannot resolve.

A decision whose table has several outputs answers with a structure, so a reader addresses one field of it — `risk.riskBand`. With one output, the decision answers with that one value and `risk` is the whole answer.

## Requirements

Every name a table reads needs a requirement edge to the element that declares it.

| The table reads | Edge on the reading decision |
|---|---|
| An input argument | `<informationRequirement><requiredInput href="#<inputDataId>" /></informationRequirement>` |
| Another decision | `<informationRequirement><requiredDecision href="#<decisionId>" /></informationRequirement>` |

One `informationRequirement` element per edge, each with its own `id`. A name read without an edge is `DMN_MISSING_REQUIREMENT`; an edge to an element that is not there is `DMN_DANGLING_REQUIREMENT`.

The graph must be acyclic. Two decisions that each require the other cannot be evaluated, and neither can a longer loop.

## Ids, names and labels

Three different things, and consumers depend on all three differently.

| Attribute | What it is | Changing it |
|---|---|---|
| `id` | What the entry point addresses — `/<file>.dmn#<decisionId>` | Breaks every consumer bound to that decision. Never change it on an existing decision |
| `name` | The FEEL identifier other decisions read. Matches the decision's `variable` `name` | Breaks the tables that read it |
| `label` | The display name, shown in the designer and as the entry point's `displayName` | Safe |

Give `name` a plain identifier — no spaces, no leading digit. Put the readable wording in `label`. Keep each decision's `variable` `name` identical to the decision's own `name`.

## The authoring marker

`<uipath:authoring surface="decision-graph" />` in the `definitions` `extensionElements` says the file is a graph. Declare `xmlns:uipath="http://uipath.com/schema/1.0/dmn/authoring"` on `definitions` — a prefix bound anywhere else is not read.

It matters because a graph that holds one decision is byte-identical to a plain decision table; without the marker that file opens as a bare table. Write it on any file authored as a graph, whatever its decision count.

Each decision carries `<uipath:authoring editor="decision-table" />`. Attributes only — the marshaller drops the text body of an extension element it does not model.

## The diagram

Leave `dmndi:DMNDI` out of a new `.dmn`. Run `uip rules format <PROJECT_DIR>` after adding or removing an input or a decision: it draws a shape for each new element, leaves placed shapes where the user left them, and drops the shapes of deleted ones.

Never place shapes by hand. `validate` does not look at the diagram and no diagnostic covers layout, so hand-written coordinates are reported by nothing and land on top of one another in the designer.

## Verifying

```bash
uip rules format <PROJECT_DIR> --output json
uip rules refresh <PROJECT_DIR> --output json
uip rules validate <PROJECT_DIR> --output json
```

`refresh` publishes one entry point per decision, `/<file>.dmn#<decisionId>`, named by the decision's `label`, plus one for the whole file carrying every input and every decision's outputs. `validate` checks every decision of a graph and names the decision in each diagnostic.

<!--skill-flavor:graph-verify:start-->
Then run the whole rule:

```bash
uip rules debug <PROJECT_DIR> --inputs '<INPUTS_JSON>' --output json
```

`debug` names no decision, so the engine evaluates the graph and returns them all. **Check `Data.result.decisions[]` for every decision you authored, not only the last one.** A decision the engine skipped or answered wrongly is a passing run as far as the exit code is concerned.
<!--skill-flavor:graph-verify:end-->

## Outside the profile

A graph holds decisions whose logic is a decision table, and nothing else. Say authoring is not supported yet, then offer to express the logic as decision tables:

- `businessKnowledgeModel` and `knowledgeSource`
- `decisionService` and `group`
- `import` — one `.dmn` per project, never a reference to another file
- `literalExpression`, and every other expression kind: context, invocation, relation, list, conditional

Never write the unsupported element.

## Anti-patterns

- Reading an upstream decision by its output column name instead of its `variable` name
- A table that reads a name with no requirement edge to what declares it
- Changing a decision's `id` to tidy it up, after consumers have bound to it
- Splitting one answer across two decisions so each table is shorter
- Reading only the last decision in the `debug` result
