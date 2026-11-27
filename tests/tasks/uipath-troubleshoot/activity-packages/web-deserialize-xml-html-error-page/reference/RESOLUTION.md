# Resolution — ReleaseFeedSync

## Root Cause

Job `bfdb5d4d-0e44-4441-b60c-3d42bbbc16c6` (process `ReleaseFeedSync`, entry point `Main.xaml`) faulted in **Deserialize XML (DeserializeXml)** "Deserialize release feed" with:

```
System.Xml.XmlException: The 'hr' start tag on line 5 position 2 does not match the end tag of 'body'. Line 6, position 3.
```

The upstream HTTP Request "Get release feed" (`NetHttpRequest`, GET `https://www.kernel.org/feeds/releases.xml`, `ContinueOnError = True`) was answered **404 Not Found** (job log: `Release feed HTTP status 404`). Because `ContinueOnError` is on, the 404 did not fault the HTTP activity; its body — the default nginx HTML error page (`<hr><center>nginx</center>` on line 5, `</body>` on line 6) — went from `response.TextContent` straight into Deserialize XML with no status check. `XDocument.Parse` fails on the unclosed HTML `<hr>` tag. The parser fault is a symptom of the failed HTTP call.

Matches `activity-packages/web-activities/playbooks/deserialize-xml-malformed.md` (branch C — HTML page instead of XML).

## Fix

Fix the HTTP call so it returns the feed (correct the Request URL — the path returns 404). Check `response.StatusCode` is 2xx (and the content is XML) before Deserialize XML; on non-2xx, log/throw with the status code instead of parsing the body.

## Must NOT attribute

Do not attribute this to: a namespace/prefix problem; an empty or null input; a JSON deserializer error; a DNS, SSL, timeout or proxy failure (the server answered 404); malformed XML produced by the workflow itself — the input is an HTML error page from the server.
