Golden fixtures for `tools/entry_points.py`.

Each `*.golden.json` is a manifest Studio Web itself derived, taken verbatim from the Solution
export that deployed and ran on a live tenant. The `.ts` beside it is the job that manifest was
derived from. The deriver has to reproduce these exactly: they are the only evidence of what the
platform actually accepts, and the two jobs cover different shapes (a single-entity read with a
row interface, and a per-row loop reading one entity to write another).

`uniqueId` and `filePath` are identity rather than contract, so the tests compare the `input` and
`output` schemas only.
