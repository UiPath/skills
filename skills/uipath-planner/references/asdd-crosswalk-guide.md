# SDD / ASDD (Client Deliverable) Generation

The markdown SDD this skill writes is the **agent-first** artifact: implementation-oriented, the input to task derivation. The official Word **SDD / ASDD** is the **client-facing** deliverable, in the customer's own section structure. Generate the client document only when the user asks for it (client doc, "official template", `.docx`). The markdown SDD already exists and stays as-is — do not restructure it.

## Procedure

1. **Ask for the template path. Warn the user first:**

   > To produce the official SDD/ASDD I need the path to your Word template — the exact version and section structure you want. Without it I will produce the SDD in this skill's default structure, not the official one.

   Stop and wait for the path. Do not assume or invent the official section layout.

2. **Read the template's section structure:**
   - `.docx` → run `bash <SKILL_DIR>/scripts/docx-extract.sh "<TEMPLATE>.docx"` and take the heading list (the **Contents** page lists the numbered sections).
   - `.md` → read the headings directly.

   Match against the standard layout in the crosswalk below. The user's file wins on any naming or ordering difference — follow its sections.

3. **Match** each template section to its markdown-SDD source(s) per the crosswalk.

4. **Compute missing pieces.** For a template section with no direct SDD source, derive it from SDD data when present; when it needs information the SDD does not hold, insert a labelled placeholder and add it to a list the user must fill. Never fabricate.

5. **Assemble** the matched + computed content into the template's section order, then convert:

   ```bash
   bash <SKILL_DIR>/scripts/sdd-to-docx.sh "<ASSEMBLED>.md" --reference-doc "<TEMPLATE>.docx"
   ```

## Default crosswalk — standard UiPath SDD/ASDD template

RPA / Master-Project oriented. Left column = the template's sections; fill each from the markdown SDD (RPA template section numbers shown).

| Template section | Fill from the markdown SDD | Notes |
|---|---|---|
| Title page — *Project title* | Process / Master Project name (§1, Planner Handoff) | — |
| **1. PURPOSE** | §1 Process Overview (objective, scope) | Keep the template's standard purpose/focus prose; inject the objective. |
| **2. AUTOMATED PROCESS DETAILS** — Master Project Name, Robot Type, Orchestrator used?, Scalable, UiPath version | §1 (name) + §16 Deployment Environment (Robot type, Orchestrator, UiPath/Studio version, Scalable) | Direct map. `[SME REVIEW]` carries through where §16 is unfilled. |
| **3.1 Architectural structure** (diagram) | §10 Master Project Architecture data-flow diagram; §2 Process Map for a single project | Place the Mermaid diagram (render separately if images are needed). |
| **3.2 Master Project Runtime Details** | Production environment→§16; Prerequisites to run→§16 Runtime Prerequisites; Input Data→§5 Data Definitions; Expected output→§1/§5; How to start→§16 Trigger; Reporting→§16/§8; How is Orchestrator used→§16; Password/compliance→§15 Credentials & Assets + constraints; Stored credentials→§15; List of queue names→§12 Queue Architecture; Schedule→§16; Resolutions→§16 | Assemble one table from several SDD sections. |
| **3.3 Project name N** (per project) — dev environment, prerequisites, repository, configuration method, reused components, new reusable components | §10/§11 per sub-project; prerequisites→§16; configuration method→§15/§11; reused + new reusable components→§14 Packages / §11 (libraries) | One block per project in §10/§11. Dev-environment name and repository are usually `[SME REVIEW]` → placeholder. |
| **3.4 Project(s) workflows** — Workflow Name, Description (I/O params) | §3 Detailed Process Steps + §11 Project Structure (workflow list) | — |
| **3.5 Packages** — Package name, Description | §14 Packages | Direct map. |
| **3.6 Architectural structure** (2nd diagram) | §12 Queue Architecture diagram, or an alternate §10 view | May duplicate 3.1 in the template — emit the queue/running-order view here. |
| **4.1 Future improvements** | Out of Scope items + open `[SME REVIEW]` items | Compute candidates; else placeholder for the user. |
| **4.2 Other remarks** | Assumptions / `[DEFAULT]` notes | Placeholder if none. |
| **5. GLOSSARY** | The template's standard term list | Reuse as-is; append process-specific terms only if the SDD defined any. |

## Section gaps

- **Template section with no SDD source** → compute from SDD data; if it needs engagement info the SDD lacks (dev-environment names, repository paths, commercials, timeline), leave a labelled placeholder for the user.
- **SDD section with no template home** (e.g. §17 Testing Strategy, §4 Business Rules, §6 Value Mappings when the template omits them) → append under the nearest fit or an appendix; do not silently drop content.

## Non-RPA SDDs

The standard template is RPA / Master-Project oriented. For a Flow / Case / Agent / Coded App / API Workflow SDD, map that SDD's TOC onto the user's template sections the same way: name and runtime details into 1–2, architecture/diagram into 3.1/3.6, the buildable units into 3.3–3.5, and fold product-specific sections into the nearest runtime or architecture section.
