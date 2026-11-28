# Extraction Guide: a decision table from a document

Read when the rule comes from a policy, guideline or checklist document. A table that validates and runs can still
disagree with the document; most such tables drop a criterion, merge several into one input, join criteria with the
wrong connective, give a criterion the wrong outcome, or approve a request whose information is missing.

## Ask first: the outcome profile and any catalog

Before reading for rules, ask the user, in one message:

1. **The decision and its outcomes**: the question the rule answers, and the exact outcome values the caller expects
   (names and wording), including what to return when the request is out of scope or information is missing.
2. **A catalog, if they have one**: the fields their data or extraction step already provides (names, types, allowed
   values). The rule must read those fields; it cannot assume facts nobody supplies.
3. **Test cases, if they have any**: requests with the outcome the document gives them.

Use what they give exactly. When they have no outcome list, propose one from the document (each outcome with its page)
and confirm it before building. When they have no catalog, design the inputs with the patterns below.

**When the user cannot be asked** (a headless run): use the outcome profile, catalog and cases the request points to.
Where it gives none, propose the outcomes from the document and go on without confirming. Write every proposal, every
assumption and every catalog gap, each with its page, in the notes file the request names (else `notes.md` next to the
project), and say in the summary which of the three the request did not supply.

With a catalog, the input patterns below become checks on it: a criterion the catalog has no field for, or a field that
bundles several criteria, is reported (with the page) rather than silently approximated.

## List the criteria first

Before choosing inputs, list every criterion in the notes, one line each: an id, the page, the fact it tests, the
outcome the document attaches to it, and how it joins the others (and / or / unless). A long document gets the same
list, section by section, never a summary. Each row's annotation names the ids it implements; before testing, check
both ways: a criterion no row names is missing, a row that names none is invented.

## Inputs

- **One input per fact the document checks.** Do not bundle several checks into one status or "requirements met"
  input (`documents_status = "deficient"`, `credit_ok = false`). A bundle hides which check failed, cannot be tested,
  and moves the policy out of the table into whoever fills the input. A long checklist still gets one input per line
  item; booleans are fine. Name them by section (`title_lien_released`, `title_vin_matches`) so they read as a group.
  A clause joining two facts with "and" or "or" is two inputs, and clauses worded differently are different inputs even
  when they share an outcome. Never a generic `criterion_1_met` whose meaning changes with the request type.
- **Scope is an input.** What the decision applies to (product, indication, diagnosis, therapy stage, plan, line of
  business) is tested in the table, not assumed from its title. A request outside scope must not reach an approval.
- **Sub-types route their own checks.** When a check applies to one type only (loan type, product, exhibit), add the
  type input and guard each such check with it.
- **Several values can hold at once → one boolean per value**, not a single-select enum and not a list (a list needs
  `list contains(...)`, which no simple cell test can say).
- **A list the document names keeps its items**, even an open one ("including but not limited to"): one value or
  boolean per named item, plus an explicit `Other` for the rest. Never close it to the values you know, and never fold
  the named items into one "any listed item" input.
- **Values the document defines** (an average, a sum, a count over a period, a date boundary): compute them from raw
  inputs in an upstream decision (see the Decision Graphs Guide). Only when the raw data cannot be an input, take the
  value as an input and say in its description exactly how the caller computes it. Effective dates in the document
  ("for services on or after …") are conditions: test the date of service.
- **Same condition, different outcome by stage or role** (first review vs second review): add the stage input; do not
  pick one outcome.
- **Units and periods are part of the input.** Put the unit in the name or the description (`dose_mg`,
  `headache_days_per_month`, `months_since_last_injection`), and test the threshold in the document's own unit. A
  number in a criterion is a number input tested in the cell, never a "meets the threshold" boolean the caller decides.
- **Describe every input.** Give each `<inputData>` a `<description>`: what the caller supplies, in the policy's words,
  with its unit and the page it comes from. It is the only record of the input's meaning when the rule is not cited.
- **Names**: snake_case; never a FEEL reserved word (`date`, `time`, `list`, `function`, `context`, `and`, `or`, `not`,
  `in`, `between`, `instance`, `of`, `satisfies`, `every`, `some`, `if`, `then`, `else`, `for`, `return`, `null`,
  `true`, `false`) as a name or property name.

## Outcomes

- **Keep the outcome the document attaches to each criterion.** A check listed under an outcome (a knock-out list, an
  exclusions list, "must be referred", "is non-covered") returns that outcome, even when another seems kinder or more
  practical.
- **When a branch fails part-way, find the document's outcome for that case.** "In the program but not eligible" and
  "not in the program" are often different outcomes; do not send both to the nearest one.
- **When several outcomes could apply** (one criterion denies, another refers), follow the precedence the document
  gives. Where it gives none, put the stricter outcome first and record the choice as a warning or note, with the page.
- **Do not promote supporting content to requirements.** Dosing tables, file checklists, study-design standards,
  stipulations and paperwork are conditions only when the document says failing them changes the outcome. A
  documentation requirement inside the criteria ("must be documented", "with a letter of medical necessity") is a
  criterion with its own input.
- **Missing information has an outcome**: the profile's, else the document's (often "pend" or "refer"); any input can
  be missing, and the table's last row returns it. **Every listed outcome is reachable** and has a test case (below).

## Table layout: one criterion per row, closed by default

A table that tests every criterion in one cell (`age >= 18 and neurologist and ...`) evaluates, but when a request
fails nobody can tell which criterion failed, a person cannot edit one threshold, and one citation cannot stand for the
row. A table whose approval row tests nothing approves every request its deny rows miss, including one with a missing
input: a comparison on null does not match, so every deny row is skipped. A negated cell (`not(true)`, `not("A")`)
does match null, so test `false` or the listed values instead. Lay the table out with hit policy FIRST:

1. **Scope and exclusion rows first** (wrong product, out-of-scope line of business, excluded indication).
2. **One deny (or refer, not-covered, ...) row per criterion**, in the order the document lists them: each row tests
   one criterion failing and returns the outcome the document attaches to it. The row that fires is the reason. An
   "unless", "except" or "is acceptable" clause gets its own input and a row above the deny row it overrides.
3. **The approval row restates every criterion positively**, one column per criterion, each cell a simple test of its
   own input (`>= 18`, `true`). It never approves on a blank cell for a criterion the document requires.
4. **The last row has no tests and returns the missing-information outcome.** A request reaches it only when some
   input was null or matched no row above.

**Write each connective as the document words it.** A condition shared by several alternatives stays outside the OR;
"X (or Y when Z)" changes X's threshold when Z holds and is not a second route. An "any of" criterion (step therapy:
one agent of a class, at its dose, for its duration) is one criterion: give it one input column whose input expression
computes it from its own inputs, test that column `true` / `false`, and deny only when it is false; never give one
alternative its own deny row, which denies requests that meet another. Do not put two criteria in one cell or column.

## Test from the document

Write `tests.json` next to the project **before authoring the table**, from the document alone; the expected outcome
comes from the document, never from reading your own table.

```json
{ "base": { "patient_age": 40, "neurologist_involved": true, "headache_days_per_month": 20 },
  "cases": [
    { "name": "age_17_denied", "rule": "deny_age", "page": 1,
      "checks": "Patient must be at least 18 years of age",
      "inputs": { "patient_age": 17 }, "expected": "Deny: initial criteria not met" },
    { "name": "age_missing_pends", "rule": "missing_info", "page": 1,
      "checks": "Patient must be at least 18 years of age",
      "omit": ["patient_age"], "expected": "Pend: information missing" } ] }
```

- `base` is one request that meets every criterion, keyed by `inputData` name (what `uip rules debug --inputs` takes).
  Each case's input is `base`, with its `inputs` laid over it and the names in `omit` removed.
- `expected` is the decision's output value; when the decision has several outputs, or other decisions' outputs are
  checked too, an object keyed by output name. Dates are ISO strings (`"2026-04-01"`).
- `checks` is the clause the case tests, copied verbatim from the page; `page` counts from 1. `rule` is the id of the
  row the case expects to fire. Every field is required.

Write cases in this order, and do not stop before the first four are complete:

1. **One per outcome.**
2. **Criterion flips**: for each criterion, fail it alone from `base`. Each flip must give the outcome the document
   attaches to that criterion; a flip that leaves the outcome unchanged is a missing or shadowed criterion.
3. **Out of scope**: one case outside the decision's scope; it must not reach an approval.
4. **Missing input**: one per required input, with that input omitted; it must not approve.
5. **Exceptions both ways**: for every "unless" / "except", one case with the exception holding and one without.
6. **Boundaries**: each threshold and date at, just below and just above, inclusive or exclusive as the document says.

**Cases the user supplies are authoritative.** Translate each into the table's inputs and add it. Where one disagrees
with your reading, re-read the document, follow the case, and record the change. Fix the rule the case exposes; never
special-case a case's inputs.

Run every case, one call each, with the case's input object (`base` with its `inputs` laid over it and its `omit`
names removed) in a file:

```bash
uip rules debug <PROJECT_DIR> --inputs @<CASE_FILE> --output json
```

`actual` is the decision's value in `Data.result.decisions[].outputs` (SKILL.md, Verify). Write `test-results.json` next
to `tests.json`: a JSON list with one object per case, each with `name`, `expected`, `actual` and `pass`. A case that
was not run is not a pass. Fix the table and run all cases again; after 3 rounds with failures left, stop and list the
failing cases (SKILL.md rule 7).

Report how many cases ran, how many failed at first, how many still fail, and which of the six kinds you did not write.

## Cite (only with the digitizer's output)

Cite when the request gives the digitizer's `dom.json` for the document; the boxes come from it. Without `dom.json`, do
not cite: skip this section and say in the summary that the rule carries no citations.

Every rule row traces to the words in the document that justify it, and every input and outcome value is checked
against them. With one criterion per row (above), a row's citation is that criterion's clause.

1. Write `cites.json` next to the project:
   ```json
   { "rules":    { "<rule id>": [ { "page": 2, "quote": "words copied exactly from the page" } ] },
     "inputs":   { "<input name>": { "sourceType": "document", "meaning": "what the caller supplies, in the policy's words",
                                     "values": ["<each value the policy names, for a categorical input>"],
                                     "cites": [ { "page": 1, "quote": "..." } ] } },
     "outcomes": { "<outcome value>": [ { "page": 1, "quote": "..." } ] },
     "warnings": [ { "text": "what was assumed or is ambiguous, with its page", "rule": "<rule id>", "field": "<input name>" } ] }
   ```
   - Copy the quote **exactly** from the page text, at least 2 words: no paraphrase, no merged sentences. Pages count
     from 1. Use `...` between fragments of one clause that are separated on the page. Quote enough words to be unique
     on that page.
   - A clause that runs onto the next page is two citations, one per page. A word hyphenated across a line break
     cannot be matched: end or start the quote next to it.
   - A row cites the clause it implements and, where different, the clause that states its outcome.
   - What the document does not state gets `{ "none": "<why>" }` instead of a list: a catch-all row such as the
     missing-information row, an outcome the caller's profile adds, a `system` input.
   - An input's `sourceType` is `document` when its value is read from the case file against the policy's criterion,
     `system` when the calling system supplies it (date of service, line of business, request stage). `meaning`
     becomes the input's `sourceMapping`; for a judgment criterion ("medically necessary") state it in the policy's
     words, not as a threshold you invented. `values` are the values the policy names, for a categorical input; leave
     it out otherwise.
   - Every assumption or ambiguity you resolved (each line you would write in notes) is also a `warnings` entry, with
     `rule` or `field` when it concerns one row or input. A reviewer reads them in the `.dmn`.
2. Check the citations and write them into the `.dmn`:
   ```bash
   node "<SKILL_DIR>/scripts/cite.mjs" --dmn "<RULES_DMN>" --cites cites.json --dom "<DOM_JSON>" --write
   ```
   `<SKILL_DIR>` is the folder holding this skill's `SKILL.md`. Exit 0: every citation resolved and was written; exit 1:
   fix what `problems` lists and run it again; exit 2: a usage error (fix the command); `node` missing: say the rule
   carries no citations. The script finds each quote on its page; it never takes coordinates from you. (`cite.mjs` is a
   stop-gap until the attribution CLI resolves citations.) `--write` puts the uipdm elements in the `.dmn` (`sourceRefs`
   with page boxes on rows, `inputVariable` on inputs, `qualityWarning` on the definitions), replacing the ones a
   previous run wrote, and checks them against `uipdm.xsd`. Input and outcome quotes are checked but carry no box in the
   `.dmn`.
3. Fix every problem it reports and run it again until it exits 0: `not found` (reworded, or the wrong page:
   `foundOnPage` tells you where it is), `matches N places` (quote more words), `not cited` (an element with no
   citation), `no id` / `share this id` (give every rule row a unique id), `check-uipdm.mjs failed` (an element the
   schema rejects). Then `refresh` and `validate` again.
4. After any later edit to the table, run step 2 again: rows added or renamed need their citations, and rows removed
   take theirs with them. Never hand-write or delete `uipdm:` elements.

Report cite.mjs's final `coverage`, `resolved` and `uipdmCheck` lines.
