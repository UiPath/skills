# Authoring from an image

Applies when the process comes from an image: a sketch, a whiteboard or sticky-note photo, or a screenshot of another diagram.
The job is transcription: every item in the image becomes a node, and every visible connector becomes a flow.
A plausible process "inspired by" the image is not a transcription.
The usual failure is dropping or merging items while summarizing, then building from the summary.

1. **Inventory before you interpret.** Before writing any `.bpmn.ts`, list every visible item: its exact wording, its color and shape, and its rough position.
   Then list every visible connector as source → target, with its label, marked certain or ambiguous.
   Mark an unreadable or crossed-out item as such instead of guessing or skipping it.
   Keep the inventory outside `<Project>` (in Studio Web, under `/tmp/`, since nothing under `/solution` may be deleted).
2. **Confirm the inventory, not a summary.**
   - In a build, ask the user to confirm the full inventory before authoring, every node and flow, never a condensed or "interpreted" topology as the recommended option.
     Ask a separate question for each ambiguity and for each element you would add that the image does not show (start or end event, a join, a reading of an implied link).
     When the request says nobody will answer, take the most literal reading and list each choice on the final report's `Assumed:` line.
   - In a [draft](draft-skeleton.md), the skeleton is the transcription and its gate is the confirmation: give each ambiguous item its own box rather than merging it into a neighbour, and let the user correct it with *Change it*.
3. **Transcribe 1:1.** One node per item, with the image's wording as its `name` (in a draft, followed by the box's ` [Kind]`, per [Draft first](draft-skeleton.md) rule 5), and the image's branch labels (Yes/No) as the `label` of each `.choose()` arm.
   Add an element the image does not show only where the process needs it to compile or validate (start and end events, a named join), and in a build name each addition on the final report's `Assumed:` line.
4. **Keep the image in view.** A host can replace an earlier turn's image with a text placeholder, especially after the user sends a new message.
   Before any fidelity work, including when the user says the result does not match, check that you can see the image.
   If you cannot, read it again from the attachment path the host gave; if that fails, ask the user to attach it again.
   Never rebuild from memory of the image, from your own earlier inventory alone, or from a sub-agent's description of it; check a sub-agent's transcription against the image yourself before editing.
5. **Verify fidelity before finishing.** After `validate` passes, run `uip maestro bpmn check <Name>.bpmn.ts --graph` (in Studio Web, `.flow-sdk/<Name>.bpmn.ts`) and compare its output with the image, node by node and flow by flow.
   Fix a mismatch in the source and run the loop again; report one you cannot fix under `Unverified:` rather than calling the result done.
   `validate` proves the file is valid, not that it matches the image.
