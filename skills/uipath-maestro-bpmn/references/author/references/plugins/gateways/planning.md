# Gateway Planning

Use this reference when planning BPMN routing, branching, and joining.

## When to use

- Exclusive, inclusive, parallel, event-based, or complex decisions.
- Merging alternative paths.
- Joining parallel or inclusive work.
- Waiting for one of several events.

## Planning steps

1. Identify whether the gateway splits, joins, or does both.
2. Choose the simplest gateway type that matches the business semantics.
3. Put human-readable branch intent on outgoing sequence flows.
4. Decide the default route for exclusive and inclusive splits.
5. Decide join semantics for parallel and inclusive branches.
6. Ensure no sequence flow crosses subprocess or participant scope.
7. Plan diagram placement so conditions and routes are reviewable.

## Model may draft

- Standard gateway elements.
- Outgoing sequence flow conditions and default flow references.
- Public-safe IDs, names, and diagram geometry.
- Text annotations that explain unresolved business decisions.

## Stop conditions

Stop for user input when branch conditions are ambiguous, defaults are unknown, or a join can deadlock because the triggering split semantics are unclear.
