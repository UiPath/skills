# SDD / ASDD (Client Deliverable) Generation

The markdown SDD is the agent-first, implementation-oriented input to task derivation. The official Word SDD / ASDD is the client-facing deliverable in the customer's section structure. Generate the client document only when requested (for example, “client doc,” “official template,” or `.docx`). Keep the existing markdown SDD unchanged; do not restructure it.

## Procedure

1. **Ask for the template path and warn first:**

   > To produce the official SDD/ASDD I need the path to your Word template — the exact version and section structure you want. Without it I will produce the SDD in this skill's default structure, not the official one.

   Stop and wait for the path. Never assume or invent the official section layout.

2. **Read the template structure:**
   - For `.docx`, run `bash <SKILL_DIR>/scripts/docx-extract.sh "<TEMPLATE>.docx"` and use the heading list; the **Contents** page lists the numbered sections.
   - For `.md`, read the headings directly.

   Match the template to the crosswalk below; the user's file controls naming and ordering.

3. **Match** every template section to its markdown-SDD source(s) using the crosswalk.

4. **Compute missing content.** Derive sections without a direct source from SDD data when possible. When required information is absent, write `[SME REVIEW]` followed by what is needed and add it to the user's fill-in list. Never fabricate.

   **Marker discipline (see SKILL.md Critical Rule 10):** `[SME REVIEW]` and `[DEFAULT]` are the only gap markers. Write them verbatim with nothing inside the brackets; put the note after the closing bracket, for example `[SME REVIEW] repository not recorded in the source SDD`. Do not use `[PLACEHOLDER]`, `[TBD]`, `<fill in>`, or decorated markers such as `[SME REVIEW — …]`. Copy markers already in the source SDD byte-for-byte; relocating content must not re-word them.

5. **Assemble** matched and computed content in template order, then run:

   ```bash
   bash <SKILL_DIR>/scripts/sdd-to-docx.sh "<ASSEMBLED>.md" --reference-doc "<TEMPLATE>.docx"
   ```

## Default crosswalk — standard UiPath SDD/ASDD template

RPA / Master-Project oriented. The user's template sections take precedence over standard section numbers.

| Template section | Markdown-SDD source and handling |
|---|---|
| Title page — *Project title* | Process / Master Project name (§1, Planner Handoff) |
| **1. PURPOSE** | §1 Process Overview (objective, scope); retain the template's standard purpose/focus prose and inject the objective. |
| **2. AUTOMATED PROCESS DETAILS** — Master Project Name, Robot Type, Orchestrator used?, Scalable, UiPath version | §1 name plus §16 Deployment Environment (Robot type, Orchestrator, UiPath/Studio version, Scalable); carry unfilled §16 markers through. |
| **3.1 Architectural structure** (diagram) | §10 Master Project Architecture data-flow diagram; for a single project, §2 Process Map. Render Mermaid separately if images are needed. |
| **3.2 Master Project Runtime Details** | Assemble one table from production environment, Robot type, Orchestrator, UiPath version, scalable, prerequisites, input data, expected output, startup/scheduling/resolutions, reporting, Orchestrator use, passwords/compliance, stored credentials, and queue names. Sources: §16, §5, §1, §8, §15, and §12 as applicable. |
| **3.3 Project name N** — dev environment, prerequisites, repository, configuration method, reused components, new reusable components | Per-subproject data from §10/§11; prerequisites from §16; configuration from §15/§11; reused and new reusable components from §14 Packages / §11 libraries. Keep one block per project. Dev-environment names and repositories are usually `[SME REVIEW]` in §16; carry markers through verbatim. |
| **3.4 Project(s) workflows** — Workflow Name, Description (I/O params) | §3 Detailed Process Steps plus §11 Project Structure (workflow list). |
| **3.5 Packages** — Package name, Description | §14 Packages. |
| **3.6 Architectural structure** (2nd diagram) | §12 Queue Architecture diagram or an alternate §10 view; use the queue/running-order view when the template duplicates 3.1. |
| **4.1 Future improvements** | Out-of-scope items plus open `[SME REVIEW]` items. If none exist, add one `[SME REVIEW]` line for the user. |
| **4.2 Other remarks** | Assumptions and `[DEFAULT]` notes. If none exist, add one `[SME REVIEW]` line. |
| **5. GLOSSARY** | Reuse the template's standard term list; append process-specific terms only when defined by the SDD. |

## Section gaps

For a template section with no SDD source, compute it from available SDD data. If engagement information is missing—such as dev-environment names, repository paths, commercials, or timeline—write `[SME REVIEW]` plus what is needed. Every such section must contain the literal `[SME REVIEW]` so reviewers can find open items.

For an SDD section with no template home, such as §17 Testing Strategy, §4 Business Rules, or §6 Value Mappings, append it under the nearest suitable section or in an appendix; never silently drop it.

## Non-RPA SDDs

For Flow / Case / Agent / Coded App / API Workflow SDDs, map that SDD's TOC to the user's template in the same way: put name and runtime details into sections 1–2, architecture and diagrams into 3.1/3.6, buildable units into 3.3–3.5, and product-specific sections into the nearest runtime or architecture section.