# Resolution — FetchReport

## Root Cause

Job `3bdb5a85-b6ae-4e1f-b5a5-2488ca74de12` (process `FetchReport`, entry point `Wf_FetchReport.xaml`, folder Shared) faulted in **HTTP Request (HttpClient)** with:

```
System.Net.WebException: The operation has timed out.
```

The HttpClient request exceeded its TimeoutMS (2000 ms) against a slow endpoint and faulted with 'The operation has timed out.'. On .NET 6+ this surfaces as System.Net.WebException (not System.TimeoutException); match on the message.

Matches `activity-packages/web-activities/playbooks/http-request-timeout.md`.

## Fix

Raise TimeoutMS to cover the endpoint's real response time, or treat a hung/slow endpoint as a target-service availability issue (retry/escalate). The message 'The operation has timed out.' is the timeout discriminator.

## Must NOT attribute

Do not attribute this to: a DNS/host-not-found or connection-refused failure (the message is 'The operation has timed out.', not 'No such host is known.'); a deserialization/JSON error; a null input; an invented different cause.
