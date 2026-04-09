# Merge Node — Implementation

## Node Type

`core.logic.merge`

## Registry Validation

```bash
uip flow registry get core.logic.merge --output json
```

Confirm: input port `input` (accepts multiple connections), output port `output`.

## JSON Structure

```json
{
  "id": "joinBranches",
  "type": "core.logic.merge",
  "typeVersion": "1.0.0",
  "display": { "label": "Join Branches" },
  "inputs": {},
  "model": { "type": "bpmn:ParallelGateway" }
}
```

## Adding via CLI

```bash
uip flow node add <ProjectName>.flow core.logic.merge --output json \
  --label "Join Branches" \
  --position 600,300
```

## Wiring Pattern

```bash
# Both parallel branches connect to the same merge node
uip flow edge add <ProjectName>.flow callApiA joinBranches --output json \
  --source-port success --target-port input

uip flow edge add <ProjectName>.flow callApiB joinBranches --output json \
  --source-port success --target-port input

# Continue after merge
uip flow edge add <ProjectName>.flow joinBranches combineResults --output json \
  --source-port output --target-port input
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Merge never completes | One parallel branch has no path to the merge node | Ensure all forked branches reach the merge |
| Unexpected execution order | Branches assumed to complete in order | Merge waits for all — don't depend on arrival order |
