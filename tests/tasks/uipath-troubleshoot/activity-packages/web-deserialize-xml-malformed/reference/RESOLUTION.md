# Resolution — ParseDocument

## Root Cause

Job `9937b232-5a94-44ab-8aee-ce6ea52d3bb4` (process `ParseDocument`, entry point `Wf_ParseDocument.xaml`, folder Shared) faulted in **Deserialize XML (DeserializeXml)** with:

```
System.Xml.XmlException: Data at the root level is invalid. Line 1, position 1.
```

The DeserializeXml activity's XMLString is a hardcoded non-XML literal ("not a valid xml document"); XDocument.Parse rejects it at the root. No upstream HTTP activity in the workflow.

Matches `activity-packages/web-activities/playbooks/deserialize-malformed-input.md`.

## Fix

Ensure the input is well-formed XML. If it comes from an HTTP response, verify a 2xx status and XML content before parsing.

## Must NOT attribute

Do not attribute this to: an HTTP connection failure/timeout/DNS/SSL (no HTTP activity exists); a JSON error (this is XML, System.Xml.XmlException); a null/empty input; an invented endpoint.
