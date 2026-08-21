# Fixture documents — synthetic vehicle registration certificates

Three generated PNGs of a fictional "Driver and Vehicle Registry" form V5C/2. Every
value is invented; the pages carry the line *"Synthetic test document"*. No real
person, vehicle, registry or PII is involved.

## Why this domain

The task measures whether the agent recognises that **no published IXP extractor
covers the supplied documents** and hands off to `uipath-ixp` to build one. That
only works if the domain is genuinely uncovered on the target tenant.

The first baseline run (2026-08-21, GH run 32484423417) used invoice fixtures and
could not measure the behaviour at all: the CI tenant publishes five invoice
extractors (`InvoiceIXP`, `invoiceixp-cef0d447-ixp`, `idp-benchmark---invoices`,
`invoices-billing`, `invoice-model`) among 45 IxP nodes. The agent correctly
reused one and built a valid flow — right call, wrong test.

Vehicle registration was chosen because it is absent from every published node on
that tenant *and* semantically distant from all of them (invoices, receipts, bank
statements, passports, birth/death certificates, health insurance cards,
employment agreements, aviation reports, ICAO air transport, Fannie Mae 1003),
so reusing an existing extractor is not a reasonable alternative for the agent.

`seed.py` re-checks this at run time and fails loudly if the domain becomes
covered, so tenant drift can never silently invalidate the test again.

## Extractable fields

Certificate Number · Registration Plate · Vehicle Identification Number · Make ·
Model · Year of Manufacture · Colour · Engine Capacity · Registered Keeper ·
Keeper Address · Date of First Registration · Valid Until

## Regenerating

Rendered with Pillow at 1000×1350 on white, dark header band, label-above-value
rows with rule lines — deliberately high-contrast so OCR quality is not a
variable in the test. Any comparable clean render works; the task grades
structure (project created, folder-deployed, node wired), never extraction
accuracy or specific field names.
