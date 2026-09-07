<!--skill-flavor:loop-validate-cannot-catch:start-->
> **`flow validate` cannot catch this.** The wrong accessor is valid JS over an `any`-typed array — it validates clean and silently produces `NaN`/`undefined` at runtime. Confirm the shape with one `uip flow debug` run before wiring downstream consumers; if it prints `TimedOut after 300s` with `(no run logs emitted)`, ask the user to run Debug from the designer instead.
<!--skill-flavor:loop-validate-cannot-catch:end-->
