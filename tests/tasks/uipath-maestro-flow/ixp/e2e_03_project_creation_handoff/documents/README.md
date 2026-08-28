# Fixture documents — synthetic falconry licences

Three generated PNGs of a fictional "National Falconry & Raptor Registry" form.
Every value is invented; each page carries the line *"Synthetic test document"*.

## Why this domain

The task measures whether the agent recognises that **no published IXP
extractor covers the supplied documents** and hands off to `uipath-ixp` to
build one — so the fixture domain must be uncovered on the target tenant, and
`handoff.py seed` blocks the run if it is not. Under the old design each
passing run burned its own domain forever (a folder deployment has no delete
API and its registry node outlives the project): invoices, vehicle
registration, boiler inspection and marina berths were all consumed that way.
Teardown now deletes the run-scoped Orchestrator folder, which removes the
deployment's registry node, so falconry should never burn.

If it ever does (a failed teardown leaks): pick a replacement domain absent
from and semantically distant to the tenant's published nodes, produce
replacement fixtures (the Rendering section below is the spec — there is no
committed generator), and update the seed DOMAIN_MARKERS, the prompt, and this
file.

## Extractable fields

Licence Number · Ring Number · Species · Sex · Year of Hatch · Falconer ·
Falconer Address · Mews Location · Date of Issue · Licence Expiry · Licence
Class · Licence Status

## Rendering

Pillow, 1000×1350 on white: dark header band (issuer + form title), twelve
label-above-value cells in two columns with rule lines, synthetic-document
footer. Deliberately high-contrast so OCR quality is not a variable — the task
grades structure (project created, folder-deployed, node wired), never
extraction accuracy or field names.
