# Form trigger

*Exact signatures, fields, and defaults: `formTrigger()`.*

A person starts the flow by submitting a form (`core.trigger.form`). The
submitted values ARE the flow's inputs — read them exactly like any other
input (`input('name')` / `$vars.start.output.name`).

Signature: `.trigger(formTrigger())` — the factory takes no arguments.

```ts
export default flow('expense-request')
  .input({
    invoiceAmount: types.number,
    reason: types.string,
    urgent: { type: types.boolean, default: false },
  })
  .trigger(formTrigger())
  .step('assess', script({ code: 'return $vars.start.output.invoiceAmount > 500;' }))
  .return({})
  .build();
```

## At a glance

A person starts the flow by submitting a form (`core.trigger.form`); the
submitted values ARE the flow's inputs.

```ts
export default flow('expense')
  .input({ amount: types.number, reason: types.string })
  .trigger(formTrigger())
  .step('log', script({ code: 'return $vars.start.output.amount;' }))
  .build();
```

Locally `--input` supplies the values; no rung renders a form.

## The derived schema

The form's fields are derived from `.input()` at compile time, the same rule
the designer applies to a flow's arguments: one field per input, the field id
IS the input's name (so submitted values line up by name), the label is the
name sentence-cased (`invoiceAmount` → "Invoice amount"), the field type
follows the input's type, and a field is **required exactly when its input
declares no default**. There is nothing to author on the trigger itself —
shape the form by shaping the inputs.

`check` warns (`FORM_TRIGGER_NO_INPUTS`) when the flow declares no inputs: the
person would get an empty form with only a submit button.

A `types.file` input becomes an upload field whose value is a reference to the
file, not its content ([operate.md](operate.md#debug--a-real-end-to-end-run)).
The form takes no title, description or accepted file types.

## Evidence boundary

No local rung renders a form — `--input` supplies the values locally, so a
green ladder proves the trigger type, the derived schema, and that the graph
runs. A person actually seeing and submitting the form is platform evidence.
