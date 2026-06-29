# ASDD (Client Deliverable) Generation

The markdown SDD is the **agent-first** artifact: implementation-oriented, the input to task derivation. The **ASDD** is the **client-facing** deliverable, written in the customer's own section structure. Generate the ASDD only when the user asks for a client document, an "official ASDD", or a Word deliverable. The markdown SDD already exists and stays as-is — do not restructure it.

## Procedure

1. **Ask for the ASDD template path. Warn the user first:**

   > To produce the official ASDD I need the path to your ASDD template — the exact version and section structure you want. Without it I will produce the SDD in this skill's default structure, not the official one.

   Stop and wait for the path. Do not assume or invent the official section layout.

2. **Read the template's section structure:**
   - `.docx` → run `bash <SKILL_DIR>/scripts/docx-extract.sh "<ASDD_TEMPLATE>.docx"` and take the heading list.
   - `.md` → read the headings directly.

3. **Match** each ASDD section to its SDD source(s) using the default crosswalk below. The user's template wins on any naming or ordering difference — follow its structure, not the table's.

4. **Compute missing pieces.** For an ASDD section with no direct SDD source:
   - Derive it from SDD data when the content is present (e.g. an Executive Summary from §1 Overview + Recommended Scope; Solution Architecture from §10/§11/§13; Assumptions from the `[DEFAULT]`/`[SME REVIEW]` items).
   - When it needs engagement information the SDD does not hold (commercials, timeline, team, sign-off), insert a clearly-labelled placeholder and add it to a list the user must fill. Never fabricate client-commercial content.

5. **Assemble** the matched + computed content into the ASDD section order, then convert:

   ```bash
   bash <SKILL_DIR>/scripts/sdd-to-docx.sh "<ASSEMBLED_ASDD>.md" --reference-doc "<ASDD_TEMPLATE>.docx"
   ```

   The reference doc applies the customer's fonts, heading styles, and margins.

## Default SDD → ASDD crosswalk

Use as the starting map; override per the user's template.

| SDD section (this skill) | ASDD section (typical) |
|---|---|
| §1 Process Overview + Recommended Scope | Executive Summary / Solution Overview |
| §2 Process Map | Process Description — TO-BE |
| §3 Detailed Process Steps | Detailed Process Description |
| §4 Business Rules | Business Rules |
| §5 Data Definitions + §6 Value Mappings | Input / Output Data Definitions |
| §7 Exception Handling + §8 Error Handling | Exception Handling |
| §9 Application Inventory | Applications / Systems in Scope |
| §9 Interactive Authentication / Re-auth Handoff | Security & Access |
| §10 Master Project Architecture + §11 Project Structure + §12 Queue Architecture + §13 Implementation Mode + §14 Packages | Solution Architecture |
| §15 Credentials & Assets | Security & Credentials |
| §16 Deployment Environment | Infrastructure & Environment |
| §17 Testing Strategy | Testing Approach |
| Decisions Made | Design Decisions / Assumptions & Dependencies |
| Planner Handoff, §18 Next Steps | Omit — internal, not client-facing |

For non-RPA templates (Flow, Case, Agent, Coded Apps, API Workflow): map that template's TOC onto the ASDD skeleton the same way, omit the internal sections (Planner Handoff, Next Steps), and fold product-specific sections (e.g. Case SLA Rules, Agent Evaluation Criteria) into the nearest ASDD architecture or approach section.

## Section gaps

- **ASDD section with no SDD source** → compute from SDD data; if it needs engagement info the SDD lacks, leave a labelled placeholder for the user.
- **SDD section with no ASDD home** → put it in an ASDD appendix; do not drop content.
