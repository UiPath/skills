# Resolution — QuoteLookup

## Root Cause

Job `08f043df-d089-4e8e-aa22-31cde10662b4` (process `QuoteLookup`, entry point `Main.xaml`) faulted in **Deserialize XML (DeserializeXml)** "Deserialize quote body" with:

```
System.Xml.XmlException: 'soapenv' is an undeclared prefix. Line 1, position 2.
```

`Assign soapResponse` holds a well-formed SOAP envelope whose root `<soapenv:Envelope>` declares `xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"`. `Assign soapBody` then cuts out only `<soapenv:Body>...</soapenv:Body>` with `Substring`/`IndexOf`, dropping the Envelope element that carries the namespace declaration. Deserialize XML parses that fragment; the first element uses the `soapenv:` prefix with no declaration in scope, so `XDocument.Parse` throws at line 1, position 2. No HTTP activity is involved.

Matches `activity-packages/web-activities/playbooks/deserialize-xml-malformed.md` (branch A — namespace prefix never declared).

## Fix

Parse the complete envelope (`soapResponse`) and select the Body / `GetQuoteResponse` element with LINQ to XML and an `XNamespace` for `http://schemas.xmlsoap.org/soap/envelope/`, instead of cutting the XML with `Substring`. If a fragment is unavoidable, re-add `xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"` on its root element.

## Must NOT attribute

Do not attribute this to: an upstream HTTP failure / error page / empty body (the workflow has no HTTP activity); a null or empty input; a JSON deserializer error; generic "malformed XML" without identifying the missing namespace declaration caused by the Substring.
