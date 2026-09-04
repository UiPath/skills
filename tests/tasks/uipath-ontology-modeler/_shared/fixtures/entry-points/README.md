Golden fixtures for `tools/entry_points.py`.

Each `*.golden.json` is a manifest Studio Web itself derived, taken verbatim from the Solution
export that deployed and ran on a live tenant. The `.ts` beside it is the job that manifest was
derived from. The deriver has to reproduce these exactly: they are the only evidence of what the
platform actually accepts, and the two jobs cover different shapes (a single-entity read with a
row interface, and a per-row loop reading one entity to write another).

`uniqueId` and `filePath` are identity rather than contract, so the tests compare the `input` and
`output` schemas only.

Note these two jobs declare their row fields as REQUIRED, which the contract guide now tells
authors not to do — a required row field is rejected before the handler if the read spells the
column differently. They are kept verbatim on purpose: their whole value is proving the deriver
reproduces what Studio Web produced for these exact inputs, and changing the input would destroy
the comparison. The rule they predate is documented where authors read it, not here.
