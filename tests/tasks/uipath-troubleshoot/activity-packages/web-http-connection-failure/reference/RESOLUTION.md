# Resolution — CallService

## Root Cause

Job `419a6787-6cc6-4b93-bae4-ba985bf6fe67` (process `CallService`, entry point `Wf_CallService.xaml`, folder Shared) faulted in **HTTP Request (HttpClient)** with:

```
System.Net.WebException: No such host is known. (service-endpoint-unavailable.invalid:80)
```

The HttpClient request failed DNS resolution for the configured EndPoint host (service-endpoint-unavailable.invalid), faulting with WebException 'No such host is known.'. On .NET 6+ a DNS failure surfaces with this message (legacy: 'The remote name could not be resolved').

Matches `activity-packages/web-activities/playbooks/http-request-connection-failure.md`.

## Fix

Correct the EndPoint host, and ensure the robot machine can resolve and reach it (DNS / network / proxy egress).

## Must NOT attribute

Do not attribute this to: a timeout (the message is 'No such host is known.', not 'The operation has timed out.'); a deserialization/JSON error; a null input; a non-success HTTP status (the host never resolved, so no HTTP response was received).
