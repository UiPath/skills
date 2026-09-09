# Resolution — PaymentGatewaySync

## Root Cause

Job `7b2e1c04-9f3a-4d21-8c6e-2a5f9b1d3e40` (process `PaymentGatewaySync`,
entry point `Wf_PostPayment.xaml`, folder Shared) faulted in **HTTP Request
(HttpClient)** with:

```
System.Net.WebException: The remote server returned an error: (407) Proxy Authentication Required.
```

The unattended robot sits behind a **corporate proxy** required for outbound
internet. The `407` means the proxy is in the request path but the robot's
HTTP call carries **no proxy credentials** — so the proxy refuses it. The Web
activities expose no proxy configuration property and do not reliably pick up
the interactive user's system proxy when running under the robot's
**service/unattended account** (Session 0). That is why the same process
succeeds from Studio on the developer's laptop (which has the user's proxy
context) but fails on the scheduled unattended run.

Matches `activity-packages/web-activities/playbooks/http-request-proxy-blocked.md`.

## Fix

Route the robot's HTTP egress through the corporate proxy **with credentials**:

- Configure the robot's run account / machine to use the corporate proxy for
  outbound HTTP (system proxy for the service account, or set the proxy
  programmatically before the call — `New System.Net.WebProxy(proxyAddress)`
  with a `NetworkCredential`, then `System.Net.WebRequest.DefaultWebProxy =
  proxy`), and supply the proxy credentials the `407` demands.
- Alternatively, have the corporate proxy/firewall allow the robot's egress to
  `payments.partner.example` (whitelist), or add the host to the proxy bypass
  list if it should skip the proxy.
- Verify from the robot machine under the run account that the call now
  returns a real HTTP status.

## Must NOT attribute

Do not attribute this to: a DNS resolution failure or connection-refused
transport error (the message is `(407) Proxy Authentication Required`, not
"No such host is known." / "Unable to connect"); an SSL/TLS trust failure; a
wrong `EndPoint` (the same URL works from the laptop); or an authentication
problem on the **target payment API** (401/403 on the API) — a `407` is the
**proxy** demanding auth, not the destination server. It is not a code bug in
the workflow: the request config is correct; the robot's network path lacks
the proxy.
