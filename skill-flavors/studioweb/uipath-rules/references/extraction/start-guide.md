<!--skill-flavor:host-paths-extra:start-->

**In this host.** `pdftotext` and Python are not installed: read the document with the file reader and cite from that text; do not write a `document.md`. `mktemp` is not installed: `<TEMP_DIR>` is `/tmp/rules-<RULE_NAME>`, made with `mkdir -p`. `node` cannot open a file in the skill folder: before running a script from `<SKILL_DIR>/scripts/`, copy it into `<TEMP_DIR>` with `cp` and run the copy. `node` reads only `/solution` and `/tmp`, so also copy into `<TEMP_DIR>` any file the script reads from elsewhere (a `dom.json` under `/attachments`, for example) and pass the copy's path. For the uipdm check (Finish, step 4), copy both `<SKILL_DIR>/scripts/check-uipdm.mjs` and `<SKILL_DIR>/references/uipdm.xsd` into `<TEMP_DIR>` and run `node "<TEMP_DIR>/check-uipdm.mjs" <DMN_FILE>`.
<!--skill-flavor:host-paths-extra:end-->
<!--skill-flavor:one-shot-offer:start-->
**One-shot level.** This host cannot run Quick draft. List only the two review levels. When the user asks for Quick draft or IXP rules extraction, say in one sentence that it is not available in Studio Web yet, and continue with the guided flow.
<!--skill-flavor:one-shot-offer:end-->
