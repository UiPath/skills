# BPMN Phase 0 interview

Use Phase 0 only when the request is prose and neither an existing `.bpmn` nor
a supplied `sdd.md` is available. Its output is a reviewable BPMN SDD, not
registry discovery or a partially authored BPMN file.

Before the interview, read the BPMN SDD template and generation rules from this
skill. Create `sdd.draft.md` at the requested working path before asking for
registry information or writing a BPMN file. Do not run registry discovery
before registry authoring begins after SDD approval.

## Interview sequence

1. **Listen.** Capture the requested outcome, trigger, actors, inputs, and any
   stated success or failure outcome. Reuse clear facts; label assumptions.
2. **Sketch.** Write the smallest complete draft graph in `sdd.draft.md` with
   stable logical node and flow IDs, an initial variable inventory, and known
   resource intent.
3. **Ask.** Ask only shape-changing questions: a missing start or end outcome,
   branch condition, ownership boundary, exception event, subprocess, loop,
   data producer, or required resource intent. Do not turn Phase 0 into a
   registry interview.
4. **Resolve.** Incorporate answers, make unresolved resource intent explicit,
   and check graph completeness and variable lineage. Leave unknown required
   resource details as `UNRESOLVED`; never fabricate a key, ID, or connection.
5. **Approve.** Present the complete `sdd.draft.md` for explicit approval.
   Use the host's supported user-input mechanism when available so approval is a
   resumable checkpoint, not the end of the agent turn.
   Do not rename, replace, or create `sdd.md` until the user explicitly
   approves the SDD. After approval, promote the exact reviewed content to
   `sdd.md`; only then may registry authoring start.

## Approval and resumption

- Approval of the SDD is separate from later confirmation of a discovered
  technical resource. If discovery finds a different candidate, preserve the
  SDD intent and ask for the normal resource-selection confirmation.
- If `sdd.draft.md` already exists and `sdd.md` does not, resume from the
  draft. Ask only for unresolved shape-changing decisions, then request
  explicit approval.
- Never overwrite a supplied `sdd.md`. It enters semantic intake directly and
  skips Phase 0.
- A reviewable SDD may contain required unresolved resources. It cannot advance
  to executable BPMN until those resources are resolved.
