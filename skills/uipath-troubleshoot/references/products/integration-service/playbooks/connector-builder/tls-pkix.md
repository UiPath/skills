---
confidence: medium
---

# Custom Connector TLS and PKIX Failures

## Context

Signature: connection provisioning or an operation fails with
`javax.net.ssl.SSLHandshakeException`, `PKIX path building failed`,
`unable to find valid certification path`, hostname verification, protocol, or cipher errors.

Browser, Postman, Python, or Studio success does not prove that the server sends a complete
certificate chain. Those clients can use cached intermediates, AIA fetching, or a different
trust store.

Required anchors: exact hostname and port, failing phase, UTC timestamp, environment/runtime,
full TLS exception and nested cause, and the certificate chain actually served during the
failing endpoint's handshake. Never attach private keys or credentials.

### What can cause it

- The server did not send a required intermediate certificate.
- The endpoint uses a private or untrusted root without a supported trust configuration.
- The leaf or intermediate certificate is expired or not yet valid.
- The certificate SAN/hostname does not match the endpoint that failed.
- The provider and Integration Service runtime have no mutually supported TLS protocol or cipher.
- A proxy or TLS-inspection device presented a different, untrusted certificate chain.

## Investigation

1. **Confirm the failing hostname.** OAuth authorize, token, API, and regional hosts may differ.
   Inspect the endpoint that actually failed rather than only the connector base URL.
2. **Capture the served chain.** This is user-required unless an approved platform
   trace already records the handshake; this playbook does not authorize an
   invented shell command. Ask for output from a neutral TLS inspection that does
   not silently add cached intermediates. Record leaf subject/SAN, issuer,
   validity, chain order, and whether each required intermediate was served.
3. **Classify the exact TLS branch:**
   - missing intermediate;
   - untrusted/private root;
   - expired or not-yet-valid certificate;
   - hostname/SAN mismatch;
   - TLS protocol/cipher incompatibility;
   - interception proxy presenting a different chain.
4. **Compare environments and clients.** If only the IS runtime fails, compare the actual
   served chain, DNS destination, proxy path, and trust model. Do not jump directly to “Java
   bug” or “install the root.”
5. **For PKIX,** build the chain from leaf to a trusted root. A leaf whose issuer is not present
   in the served chain is evidence of a missing intermediate even when a browser succeeds.
6. **For private/internal CAs,** establish whether the target deployment has a supported trust
   configuration. Do not prescribe an undocumented trust-store modification.

### Diagnosis

| Evidence | Diagnosis |
|---|---|
| Server sends leaf but omits required intermediate | Provider/server certificate-chain defect |
| Complete chain terminates at a private/untrusted root | Trust-policy/deployment limitation or configuration |
| Certificate validity window excludes failure time | Expired/not-yet-valid provider certificate |
| Requested hostname is absent from SAN | Hostname/certificate mismatch |
| Chain and hostname are valid; handshake rejects protocol/cipher | TLS compatibility or proxy branch |
| IS resolves through a proxy that substitutes the certificate | Network interception/trust branch |

## Resolution

Quote one confirmed cause verbatim from **What can cause it**, then correct only
that TLS branch. If evidence does not isolate one cause, stop at the missing
discriminator.

Diagnosis is read-only. Obtain explicit approval before changing provider TLS,
proxy/trust configuration, or the connector endpoint.

- **Missing intermediate:** provider configures the server/load balancer to send the leaf plus
  required intermediate certificates in the correct order. This is preferred over client-side
  workarounds.
- **Private root:** use only a documented, supported certificate-trust procedure for that
  deployment; otherwise record the limitation and escalate.
- **Validity or hostname:** provider renews/reissues and deploys the correct certificate.
- **Protocol/cipher:** provider and platform owners align on a mutually supported secure
  protocol/cipher after capturing handshake evidence.
- **Interception:** network owner configures the supported trust/proxy path or excludes the
  endpoint according to policy.

Do not recommend upgrading Java unless a reproducible version-specific defect is established.

### Verification

Reinspect the served chain, then create/ping the connection or execute the operation from
Integration Service. Desktop-client success is not sufficient.

### Escalation Bundle

Include hostname/port, environment/region, timestamp, full nested TLS exception, redacted
certificate subjects/issuers/SANs/validity/fingerprints, served-chain order, DNS/proxy findings,
and the exact IS phase that failed.
