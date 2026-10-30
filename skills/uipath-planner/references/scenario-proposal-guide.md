# Scenario Proposal Guide — scenarios for a goal

`author` reads this guide when the input is a goal, not a process: a self-paced workshop, a demo, trying a product or an application. The planner proposes scenarios; the scenario the user picks is the description `author` continues from at [author-guide.md](author-guide.md) Step 2. What this path reads: [author-guide.md § Read Plan](author-guide.md), the rows for a goal.

## Propose scenarios for a goal

1. **Ask one round:** one `AskUserQuestion` batch of two multi-select questions, each skipped when the request already answers it.
   - **Products to exercise:** RPA, agents, orchestration (Maestro Flow, BPMN, Case), document extraction, human review and apps.
   - **Systems within reach, grouped by the setup they need:** none (local files, Excel, public APIs); a tenant connection (mail, chat, a SaaS system); an application installed or hosted for the user (SAP, an internal web application).

   Group the systems by setup because every connection, account or installation is one more thing that can fail before the scenario runs; the grouping lets the user trade reach against setup. When the delivery model is known, run the [Constraint Gate](product-selection-guide.md#constraint-gate) on the products picked; a blocked product is not offered.
2. **Propose up to three scenarios** built for the answers, using only the systems within reach plus sources that need no setup. Each is a card:
   - storyline, one sentence: what arrives, what is decided or done, where the result lands
   - Components table, `# | Component | Type | Skill | Summary`, skills per [author-guide.md](author-guide.md) Step 5 and [skill-mapping-guide.md](skill-mapping-guide.md); one row makes a component genome
   - applications and the setup each needs (connection, account, installation)
   - input source (item 3)
   - what it exercises: products and skills

   Cover different shapes of [skill-mapping-guide.md § Common Combinations](skill-mapping-guide.md) where the answers allow — one skill on one application, no UI application, several skills across applications — so the pick sets the scope while complexity is still inferred ([author-guide.md](author-guide.md) Step 3). Invent the storyline for the answers: the combinations give shapes, the templates the depth, not stories. Present the cards as one single-select `AskUserQuestion`, each card in its option's preview; the user merges or amends cards through Other.
3. **An invented scenario names where its input comes from:** a public source, sample files the build writes as data files, or a generator component in the Components table. A described process brings its inputs; an invented one has none until the scenario gives them. The genome names the source in Target Applications (Actors and Systems in a process genome), and the acceptance criteria take their inputs from it.
4. **The pick is the description.** Continue at [author-guide.md](author-guide.md) Step 2 with the chosen, merged or amended card. A prototype or workshop has no sign-off, so it gets no SDD.
