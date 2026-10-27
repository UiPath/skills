> when: authoring or checking a process taken from an image (sketch, whiteboard, sticky notes, screenshot)

## Authoring from an image

When the process comes from an image, the job is transcription: every item in the
image becomes a node and every visible connector becomes a flow. A plausible
process "inspired by" the image is not a transcription. The usual failure is
dropping and merging items while summarizing, then building from the summary.

1. **Inventory before you interpret.** Before proposing any topology, write
   down every visible item: its exact wording, its colour/shape, and its rough
   position. Then list every visible connector as source → target, with its
   label and whether it is certain or ambiguous. Mark unreadable or crossed-out
   items instead of guessing or skipping them. Keep this list in a notes file
   outside the project folder.
2. **Confirm the inventory, not a summary.** The structure you confirm under
   SKILL.md Rule 4 must list every node and flow from the inventory. Never offer a
   condensed or "interpreted" topology as the recommended option. Ask a
   separate question for each ambiguity, and for anything you would add that
   the image does not show (start/end events, merge gateways the canvas
   requires, a reading of an implied link).
3. **Transcribe 1:1.** One node per item, keeping the image's wording and its
   Yes/No branch labels. Add technical scaffolding only where the canvas
   requires it, and name each addition in your final report.
4. **Keep the image in view.** Earlier-turn images may leave your context:
   hosts can replace them with a text placeholder, especially after the user
   sends a new message. Before any fidelity work, including when the user says
   the result does not match, check that you can actually see the image. If
   you cannot, re-read it from its file path (the attachment path the host
   provided). If that also fails, ask the user to re-attach it. Never rebuild
   from memory of the image, from your earlier summary, or from a sub-agent's
   text description. If a sub-agent transcribed the image, check its result
   against the image yourself before editing.
5. **Verify fidelity before finishing.** After `validate` passes, look at the
   image again and compare it with the BPMN node by node and flow by flow.
   Report any remaining mismatch rather than calling the result done.
   Validation proves the file is structurally valid, not that it matches the
   image.
