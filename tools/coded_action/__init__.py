"""Offline validation of coded-action pairs: one action TTL and the job that implements it.

A coded action moves computation out to a job on Orchestrator while keeping the commit boundary
declarative. That split is what this package checks, because the two halves are one contract and
nothing at runtime will tell you they disagree until after the job has already run:

  - the `func:name(args)` marker in the TTL binds the job's input by NAME to the action's params
    and declared reads, so a rename on either side faults the job before its handler;
  - `ont:writes` is the union over every branch the job could take, and an edit outside it is
    refused whole at `Preparing write statement`, after the job ran, with nothing written;
  - `type<T>()` is inert at runtime, so the schema the platform validates against is derived from
    the job's interfaces at stage time -- a contract that cannot be lowered cannot be deployed.

Everything is read by masking and depth-scanning text, never by a parser, because this stays
dependency-free. The rule that follows from that: a shape a scanner does not recognise is reported
as unresolved, never read as "nothing there". Absence must not pass as success.

Nothing is importable from this module. The public surface is tools/coded_action_preflight.py.
"""
