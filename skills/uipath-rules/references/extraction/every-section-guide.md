# Every Section: Extra Stops

Read with [guided-guide.md](guided-guide.md) when the user chose `Every section`. The work is the guided path, unchanged. This guide adds two kinds of stop; each is one AskUserQuestion call with the result shown with it (extraction rule 1).

1. **Approve the inputs and structure.** In the one call for blocking questions (Inputs and structure), also ask to approve the inputs, outputs, and structure. With no blocking question, the call still happens for this approval. Options: `Approve all (Recommended)` | `Change some`. Write the `.dmn` skeleton after the approval.
2. **Approve each section's rows.** Write one section at a time, not the remaining sections together. After each section in Extraction, stop: approve the section's rows, or answer its blocking questions (extraction rule 8); apply the answers, show the table again, and repeat until approved. Options: `Approve section (Recommended)` | `Change rows`. Run `refresh` and `validate` as one command after each approved section.

Finish is unchanged: it shows its result and asks nothing.

## Inputs and structure layout

```markdown
**Hit policy:** FIRST

| Input | Type | Source | Allowed values | Your request |
|---|---|---|---|---|
| employmentMonths | number | document | - | matches |
| deviceCategory | string | document | Laptop, Phone, Tablet | not given |

| Output | Type | Values |
|---|---|---|
| decision | string | Approved, Denied, Referred |
```

Options: `Approve (Recommended)` | `Rename or change`.

### Inputs, more than 8 (Inputs and structure)

```markdown
**Inputs:** 14, in 3 groups. Judgments shown in full; the rest by name and type.

| Input | Type | Source | Why shown |
|---|---|---|---|
| clinicalNeedAssessed | boolean | document, assessed | judgment criterion |
| dosesPerCourseCap | number | system | customer-defined |

**Eligibility:** age (number), residencyConfirmed (boolean), employmentMonths (number)
**History:** priorClaims (number), bankruptcyLast7Years (boolean)
```

Options: `Approve all (Recommended)` | `Change some`.

## Section layout

Show the section as the guided guide says (Extraction, Show). Where the rows are printed in the conversation, show only the section's rows, then the diff line:

```markdown
**Section: Eligibility (p.1)**

| # | employmentMonths | deviceCategory | decision | Annotation | Cited |
|---|---|---|---|---|---|
| 1 | < 6 | - | "Denied" | Under six months | p.1 "less than six months of service" |

**Earlier rows:** unchanged
```

A row with many citations shows its count instead of every quote (`p.1 - 13 quotes, see cites.json`); list the quotes under the table on request.

Options: `Approve section (Recommended)` | `Change rows`. Blocking questions are listed under the table and asked as their own questions.
