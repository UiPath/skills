<!--skill-flavor:workflow-input-source:start-->
| `$workflow.input` | The workflow's input arguments supplied by the execution caller. Constant for the entire run. | Workflow run |
<!--skill-flavor:workflow-input-source:end-->

<!--skill-flavor:workflow-input-example:start-->
// The execution caller supplied { "name": "Alice", "count": 3 } as workflow input.
<!--skill-flavor:workflow-input-example:end-->

<!--skill-flavor:runtime-content-normalization:start-->
Inside a JsInvoke script, normalize `content` supplied as either a JSON string or a pre-parsed value:
<!--skill-flavor:runtime-content-normalization:end-->
