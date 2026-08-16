# True-brownfield decompile, edit, and merge

Use this procedure when a task supplies a deployed `.flow` and no `.flow.ts`.
Do not hand-transcribe the graph: decompile it to builder source, edit that
source, and merge only the delta back into the original.

```bash
uip maestro flow decompile Deployed.flow -o Deployed.flow.ts
uip maestro flow compile Deployed -o Deployed.baseline.flow
# Edit Deployed.flow.ts narrowly; preserve existing step ids.
uip maestro flow compile Deployed -o Deployed.edited.flow
uip maestro flow merge Deployed.flow Deployed.edited.flow \
  -o Deployed.merged.flow --baseline Deployed.baseline.flow
```

The baseline must be compiled from the pristine decompiled source, before any
edit. It lets merge distinguish authored changes from reconstructed content;
without it, merge falls back to taking the compiled graph wholesale, including
layout.

Decompile reconstructs branch, switch, loop, parallel, error/ref, and
subflow structure. It preserves original node ids so merge can reattach them.
If it emits `mock() /* TODO: unsupported node type … */`, leave that node
untouched unless the task specifically asks you to replace it; merge restores
the original unsupported node.

Validate `Deployed.merged.flow`, not the intermediate edited compile. The
decompiler also emits `Deployed.pipeline.mjs`, which chains the same four
steps when a single command is more convenient.
