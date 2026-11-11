# Selector Matching Guide — how the engine reads a selector, and checking a definition

Companion of [selector-translation-guide.md](selector-translation-guide.md), read whole with it; rule numbers below are its § Rules.

## Matching semantics

How the selector engine reads what a translation writes — properties of the engine, not style preferences.

**Values match whole.** A value with no wildcard must equal the element's value exactly; there is no implied `*` at either end. `*` matches zero or more characters, `?` exactly one (never zero). **There is no escape character**, so a literal `*` or `?` in a value cannot be expressed — use `matching:<attr>='regex'` for those. Carriage returns and newlines are normalised on both sides before comparison.

**Case.** Attribute *values* are case-sensitive by default, except `app` on every tag, `tag` on `webctrl`, `role` on `java`, and the macOS state attributes. `casesensitive:<attr>='false'` lifts it per attribute. Attribute *names* are case-sensitive and must be spelled exactly as this catalog spells them — `tableRow`, `colName`, `colTooltip`, `rowName`, `labeledby`, `htmlwindowname`, `css-selector`; a misspelled case is a parse error, not a silent miss. Tag names are case-insensitive.

**Matching modes**, set per attribute with `matching:<attr>`:

| Mode | Behaviour |
|---|---|
| (absent) | wildcard matching as above |
| `regex` | ECMAScript, matched against the **whole** value (anchored); an invalid pattern is a parse error, and an inline flag (`(?i)`) is one — case is `casesensitive` (below) |
| `fuzzy` | similarity score; an imperfect match never exceeds 0.999, so only an exact match scores 1.0 |

`casesensitive:<attr>='false'` applies in `regex` mode as well. In a pattern `.` does not cross a line break — `[\s\S]` does — while a wildcard `*` crosses line breaks; a multi-line value (a table header, a cell with two lines) needs the former in a regex.

`fuzzylevel:<attr>` is the **threshold the score must reach**, from `0.0` to `1.0`, defaulting to `1.0`. Two consequences: `fuzzylevel:<attr>='0.0'` always matches on that attribute (exactly what UiPath emits when it fuzzifies), and `matching:<attr>='fuzzy'` **without** a `fuzzylevel` is *stricter* than plain equality — never write one without the other.

**`idx` is positional and 1-based**, counted in document order over the elements that already match every other attribute of that tag, within the scope of the preceding tag — not among siblings. It is omitted when the match is unique. UiPath strips `idx` (with `tableRow`, `tableCol` and `css-selector`) when it fuzzifies a selector, so an indexed target stays strict.

**Number attributes** (`idx`, `tableRow`, `tableCol`, `rowCount`, `pid`, the `nav` counts) take a plain integer only: no wildcard, no range, no comparison operator. An empty value on a number attribute means zero, not "any".

**The selector is XML.** Values are single-quoted, `&apos;` `&amp;` `&lt;` escape the characters that need it, and a repeated attribute on one tag rejects the entire selector. An empty value (`attr=''`) is an active criterion matching only an empty value — to carry an attribute without matching on it, prefix it `omit:`. Beyond `omit:`, `matching:`, `fuzzylevel:` and `casesensitive:` the driver accepts no other modifier, and there is no cap on attributes per tag. The UI Automation activities layer adds one of its own on **fuzzy** selectors and anchors: `check:<attr>='<value>'` (in practice `check:text`), a post-match verification that the resolved element's text equals the value. The fuzzy generator emits it on labels, buttons and anchors and strips it for activities whose text changes at run time (Type Into, Get Text). Preserve it when copying a driver-generated selector; never author it by hand, and never on a Type Into target.

**`<nav>`** carries exactly one of `up`, `next`, `prev`, with a count of at least 1, and never comes first in a chain. It moves from the node the preceding tag matched: `up='n'` to its n-th ancestor, `next='n'` / `prev='n'` to its n-th following / preceding sibling among the parent's child elements, hidden ones included. The landed node's tag is not checked. A `<nav>` may end the selector, and the landed node is the target; a tag after it is searched among the landed node's descendants, never the landed node itself. `<nav>` tags chain (`<nav up='1' /><nav next='1' />`). Only the first match of the tag before a `<nav>` is followed: when that path fails the search fails, without trying the tag's other matches, so that tag must be unique in its scope. A step past the first or last sibling fails. An empty tag after a node lands on that node's first child, while `idx` counts matching descendants, not children, so a child position is a `<nav>` step, never an `idx`.

## Checking a definition

Most of these rules are decidable from a definition file alone; the rest need one live command. Read a batch of definitions back by hand, or with a throwaway script written for the run when there are hundreds. A passing structural check proves shape, not that anything matches the screen.

A throwaway checker has to encode each rule's **scope**, or it reports this guide's own prescribed shapes as violations and the build "fixes" correct selectors. The two that bite: the content-attribute ban is on the **acting leaf** — an ancestor that scopes by a stable field label or row key is the prescribed shape (rule 4, last sentence) — and the `DIV` ban is on an **assumed** tag, not on one the source recorded or a known node role vouches for (rule 14). A finding count that jumps into the hundreds is the checker being wrong, not the batch.

| Check | Decide by | Rule |
|---|---|---|
| Content attribute on a Type Into / Get Text target — `value`, `text`, `visibleinnertext`, `innertext`; `aaname` unless the source recorded a label for that control | `.xaml.metadata` `ActivityType` + the tag's attributes | 4 |
| State attribute on a Check target; selection attribute on a Select Item target | same | 4 |
| A caption the source recorded beside the control (`aaname`, `visibleinnertext`, `aria-label`) sits on the acting tag instead of on a tag a `<nav>` path starts from | attributes + the source capture | 6 |
| A tag after `<nav up>` in a container that may hold several such controls; a `<nav>` path no recorded relation or documented anatomy supports | attributes + the source capture + the framework pack | 6 |
| `idx` on a control whose source capture recorded an identifier or name; `idx` bound to a workflow constant | attributes + the source capture | 7 |
| A strict target whose only attribute is a `tag` the screen repeats (`NAV`, `FORM`, `TABLE`, `P`, `BUTTON`, …): the last step's tag of a positional path the source recorded (the path belongs on it — on the web one `css-selector`), or a control the source recorded nothing positional for (a no-selector outcome: the semantic step alone where the user asked for it, a live-checks row otherwise) | attributes + the source capture | 7, 13 |
| A window selector without the stable part of a title the source recorded for that window; a title kept whole where part of it varies | definition + the titles the source recorded | 9 |
| `SemanticSelector` in `SearchSteps` where the user did not ask for the semantic step | definition | 12 |
| A Find Elements with no Target over elements the step reads by position | the definition + the workflow | [composite-interactions-guide.md](composite-interactions-guide.md), collect matching elements; desktop: [selector-translation-desktop-guide.md § Rule 8](selector-translation-desktop-guide.md) |
| A target scoped to the window a click came from, on an activity that acts after that click opened another window | the workflow + the target spec | 9; desktop: [selector-translation-desktop-guide.md § Rule 9](selector-translation-desktop-guide.md) |
| `SearchSteps` has `FuzzySelector` and `Anchors` is empty; a definition authored without a live capture carries `Anchors` | definition | 12 |
| `matching:<a>='fuzzy'` without `fuzzylevel:<a>` | attributes | § Matching semantics |
| A `matching:<a>='regex'` pattern carried from a source regex that searched, without the `[\s\S]*…[\s\S]*` wrap; an exact caption the source compared whitespace-normalised, written verbatim on `aaname` | attributes + the source criterion + one live attribute listing | 2 |
| Any attribute the node does not expose | live selector evaluator (rejects the selector outright) | 15 |
| Uniqueness, including invisible twins | live selector evaluator | 15 |
| The node a `<nav>` path lands on | target validation against the live application | 6, 15 |
| The shape the driver would have chosen | live driver default on one instance per family | 15 |

Each technology guide's § Checks adds the checks of its tags.
