# Decision Graphs

A rule holds one `.dmn`, and that file may hold more than one decision. Decisions linked by `informationRequirement` form a decision graph: the engine evaluates what a decision needs before the decision itself, and returns every decision's outputs in one run.

Read this when a request needs more than one answer, or when one answer feeds another. One answer still needs the right shape: a set of cases is a decision table and needs nothing here, one formula is a [literal expression](#literal-expressions), a calculation run over different arguments in more than one place is a [knowledge model](#knowledge-models), and a note for a reader is a [text annotation](#text-annotations).

## When to split

Split when the rule has to answer more than one question, or when one answer is an input to the next.

| Shape | One decision or several |
|---|---|
| The caller reads one value from one set of inputs | One decision |
| The caller reads two values the business decides separately — a risk band *and* an interest rate | One decision each |
| A value is decided once from the rule's own inputs and read by two later decisions | Its own decision, required by both |
| The same calculation run over *different* arguments in different places | Not a decision at all — a [knowledge model](#knowledge-models), called by each |
| One decision with a column the caller never reads, carried only to reach the next row | Still one decision; a column is not a decision |

Do not split a single answer across tables to make each table smaller. Each decision becomes an entry point a consumer can bind to, so every split is part of the rule's public shape.

## Skeleton

A two-decision graph. `rate` reads the band `risk` decides. It carries `surface="decision-graph"` **because it holds two decisions** — a rule with one table does not, and copying this skeleton into one is the most common way that attribute goes wrong.

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

**Count the upstream table's outputs first. That decides how to read it.**

| Upstream table has | It answers with | A reader names it |
|---|---|---|
| **one** output | that single value | `risk` — the decision's own name |
| **two or more** outputs | a structure keyed by output name | `assessment.severity` — one field of it |

A column name is never the handle on its own. Above, `risk` has one output whose column is `riskBand`, so `rate` reads it as `risk`:

```
<text>risk</text>            ← right
<text>riskBand</text>        ← wrong: that is the column, not the decision
<text>risk.riskBand</text>   ← wrong: only a decision with several outputs has fields
```

Reach for the dotted form **only** after counting two or more `<output>` elements. A wrong read is a valid FEEL name the engine cannot resolve, so nothing in the file looks wrong.

## Requirements

Every name a table reads needs a requirement edge to the element that declares it.

| The logic reads | Edge on the reading element |
|---|---|
| An input argument | `<informationRequirement><requiredInput href="#<inputDataId>" /></informationRequirement>` |
| Another decision | `<informationRequirement><requiredDecision href="#<decisionId>" /></informationRequirement>` |
| A knowledge model it calls | `<knowledgeRequirement><requiredKnowledge href="#<bkmId>" /></knowledgeRequirement>` |

One element per edge, each with its own `id`. A name read without an edge is `DMN_MISSING_REQUIREMENT`; an edge to an element that is not there is `DMN_DANGLING_REQUIREMENT`. A knowledge model that calls another one carries a `knowledgeRequirement` of its own.

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

The other value is `decision-table`, and it is the one `uip rules init` scaffolds. Which to write:

| The file holds | `surface` |
|---|---|
| One decision whose logic is a decision table, and nothing else | `decision-table` — what `init` already wrote, so change nothing |
| Two or more decisions | `decision-graph` |
| A business knowledge model or a text annotation, at any decision count | `decision-graph` — only the canvas draws them |

It matters in both directions. A graph that holds one decision is byte-identical to a plain
decision table, so without the marker that file opens as a bare table and the requirement edges
are invisible. And `decision-graph` on a rule that is one decision table opens it on the canvas
instead of the table editor — a worse editor for the thing the user asked for. `validate` reports
neither, so nothing tells you.

**Do not copy the skeleton above into a single-decision rule.** It is a two-decision graph, so it
carries `decision-graph`; a rule with one table keeps the surface `init` gave it.

Each decision carries `<uipath:authoring editor="…" />` naming the editor its logic opens in: `decision-table` or `literal-expression`. Attributes only — the marshaller drops the text body of an extension element it does not model.

## The diagram

Critical Rule 10 owns this: never place shapes by hand, leave `dmndi:DMNDI` out of a new `.dmn`, run `uip rules format <PROJECT_DIR>` after adding or removing any drawn element, and keep an existing `dmndi:DMNDI` when you edit a file that has one.

Every element the canvas draws counts, not only inputs and decisions: a knowledge model and a text annotation are placed too, so adding either is a reason to run `format`.

## Literal expressions

A decision answers with one value from one FEEL expression instead of a table. Use it when there are no cases to enumerate — a calculation, a formula, a single conditional.

```xml
<decision id="decision_fee" name="fee" label="Processing fee">
  <extensionElements><uipath:authoring editor="literal-expression" /></extensionElements>
  <variable id="variable_fee" name="fee" typeRef="number" />
  <informationRequirement id="informationRequirement_fee_loanAmount">
    <requiredInput href="#inputData_loanAmount" />
  </informationRequirement>
  <literalExpression id="literalExpression_fee" typeRef="number">
    <text>loanAmount * 0.015</text>
  </literalExpression>
</decision>
```

- **Always set `typeRef`** on the `literalExpression`, and give the decision's `variable` the same type. In a rule of one decision `validate` reports `DMN_LITERAL_EXPRESSION_TYPE_MISSING` without it; in a graph nothing reports it, and the engine fails at run time instead.
- The expression reads the names the decision requires, by the same rules a table's input expression follows: an input argument by its name, an upstream decision as [Reading an upstream decision](#reading-an-upstream-decision) describes.
- It answers with one value, so a reader addresses the decision itself — see [Reading an upstream decision](#reading-an-upstream-decision).
- An empty `<text>` is `DMN_LITERAL_EXPRESSION_EMPTY` — again only in a rule of one decision, so in a graph an empty formula passes `validate` and answers nothing.
- It has no rules, so it carries no `<annotation>` column and no `<annotationEntry>`.

Prefer a decision table whenever the logic is a set of cases. A table shows its cases to a reviewer; a nested `if` in one cell does not.

## Knowledge models

A `businessKnowledgeModel` is a named FEEL function that decisions call. Reach for one when the same calculation runs over **different arguments** in different places — a capacity worked out for an applicant and again for a co-applicant, from each one's own figures.

A calculation that runs **once** over the rule's own inputs is a decision, however many decisions go on to read the answer: it is worked out once and every reader shares the one value. A model cannot do that — it has no value until something calls it. Making a model out of a value that is computed once buys nothing and costs an entry point, because a decision gets one and a model does not.

```xml
<businessKnowledgeModel id="bkm_score" name="scoreModel" label="Score model">
  <variable id="variable_bkm_score" name="scoreModel" />
  <encapsulatedLogic id="encapsulatedLogic_score" kind="FEEL">
    <formalParameter id="formalParameter_score_base" name="base" typeRef="number" />
    <literalExpression id="literalExpression_score" typeRef="number">
      <text>base * 1.1</text>
    </literalExpression>
  </encapsulatedLogic>
</businessKnowledgeModel>
```

And the decision that calls it:

```xml
<decision id="decision_score" name="score" label="Score">
  <extensionElements><uipath:authoring editor="literal-expression" /></extensionElements>
  <variable id="variable_score" name="score" typeRef="number" />
  <informationRequirement id="informationRequirement_score_creditScore">
    <requiredInput href="#inputData_creditScore" />
  </informationRequirement>
  <knowledgeRequirement id="knowledgeRequirement_score">
    <requiredKnowledge href="#bkm_score" />
  </knowledgeRequirement>
  <literalExpression id="literalExpression_decision_score" typeRef="number">
    <text>scoreModel(creditScore)</text>
  </literalExpression>
</decision>
```

- **Always write the `<variable>`.** The engine rejects a knowledge model without one, and nothing in `validate` catches it — the rule fails at run time instead. Give it the model's own name and no `typeRef`: the function's return type is unstated.
- The caller calls it by that name, and carries a `knowledgeRequirement` to it. A call with no edge is `DMN_MISSING_REQUIREMENT`.
- One `formalParameter` per argument, each typed. Arguments are matched by position.
- The body is `encapsulatedLogic` holding one `literalExpression` or one `decisionTable`. `kind="FEEL"` — Java and PMML are not supported.
- A model may call another model, with its own `knowledgeRequirement`. The calls must not form a cycle.

## Text annotations

A note on the diagram, tied to the element it is about. It holds no logic, gets no entry point, and changes nothing the engine evaluates.

```xml
<textAnnotation id="textAnnotation_1">
  <text>Thresholds reviewed quarterly by Credit Risk.</text>
</textAnnotation>
<association id="association_1">
  <sourceRef href="#decision_risk" />
  <targetRef href="#textAnnotation_1" />
</association>
```

Use one for context a reviewer needs and the table cannot carry — where a threshold came from, when it is next reviewed. Per-row reasoning belongs in the annotation column instead, and a description of one element belongs in its `<description>`.

An annotation may be tied to any element except another annotation. It is drawn smaller than a decision card, and `uip rules format` places it like anything else — never write its coordinates yourself.

**`sourceRef` and `targetRef` are child elements, never attributes.** The DMN schema types them as `tDMNElementReference`, so each carries the id on its own `href`. Written as attributes on `<association>` the file still parses and `validate` still passes, but the designer reads no ends and drops the connector: the annotation draws as a box floating beside the graph, tied to nothing.

## Verifying

```bash
uip rules format <PROJECT_DIR> --output json
uip rules refresh <PROJECT_DIR> --output json
uip rules validate <PROJECT_DIR> --output json
```

`refresh` publishes one entry point per decision, `/<file>.dmn#<decisionId>`, named by the decision's `label`, plus one for the whole file carrying every input and every decision's outputs.

`validate` names the decision in each diagnostic, but it checks **less of a graph than of a single decision**. Across a graph it checks every decision's name, that each decision carries logic at all, the input-data names, and the item definitions. Beyond that:

| In a graph | Checked by `validate` |
|---|---|
| A decision table's rules, columns and cells | Only in a file that also holds a knowledge model |
| A literal expression | Never — neither its `typeRef` nor its text |
| What any decision returns | Never |

So a clean `validate` on a graph is not a working rule. Run it, then prove the values below.

<!--skill-flavor:graph-verify:start-->
Then run the whole rule:

```bash
uip rules debug <PROJECT_DIR> --inputs '<INPUTS_JSON>' --output json
```

`debug` names no decision, so the engine evaluates the graph and returns them all. **Check `Data.result.decisions[]` for every decision you authored, not only the last one.** A decision the engine skipped or answered wrongly is a passing run as far as the exit code is concerned.
<!--skill-flavor:graph-verify:end-->

## Outside the profile

A graph holds decisions, input data, knowledge models and text annotations. Say authoring is not supported yet, then offer to express the logic as decision tables:

- `knowledgeSource`, and the `authorityRequirement` that cites one
- `decisionService` and `group`
- `import` — one `.dmn` per project, never a reference to another file
- Every expression kind other than a decision table and a literal expression: context, invocation, relation, list, conditional
- A knowledge model body that is Java or PMML rather than FEEL

Never write the unsupported element.

## Anti-patterns

- Reading an upstream decision without counting its outputs first ([Reading an upstream decision](#reading-an-upstream-decision))
- A table that reads a name with no requirement edge to what declares it
- Changing a decision's `id` to tidy it up, after consumers have bound to it
- Splitting one answer across two decisions so each table is shorter
<!--skill-flavor:graph-anti-debug:start-->
- Reading only the last decision in the `debug` result
<!--skill-flavor:graph-anti-debug:end-->
- A knowledge model with no `<variable>`: `validate` passes and the engine rejects it at run time
- A nested `if` in a literal expression where the logic is a set of cases a decision table would show
