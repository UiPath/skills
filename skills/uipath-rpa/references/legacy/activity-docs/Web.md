# UiPath Web Activities - Legacy Reference

## Overview
HTTP/REST, SOAP, JSON, and XML activities. Package: `UiPath.Web.Activities`.

---

## Activities

### HTTP/REST
| Activity | Purpose | Key Gotcha |
|----------|---------|------------|
| `NetHttpRequest` | Modern HTTP client (.NET HttpClient) | Default timeout 10,000ms |
| `HttpClient` | Legacy REST client (RestSharp) | Default timeout 6,000ms |
| `SoapClient` | SOAP 1.1/1.2 client | Hard-coded timeout 60,000ms |

### JSON
| Activity | Purpose |
|----------|---------|
| `DeserializeJson<T>` | JSON string to typed object |
| `DeserializeJsonArray` | JSON string to JArray |
| `SerializeJson` | Object to JSON string |

### XML
| Activity | Purpose |
|----------|---------|
| `DeserializeXml` | XML string to XDocument |
| `GetXMLNodes` / `GetNodes` | Extract nodes from XML |
| `ExecuteXPath` | XPath query on XML |
| `GetXMLNodeAttributes` | Get attributes from node |

---

## NetHttpRequest - Full Configuration

### Authentication Types
- **None** - No auth
- **BasicUsernamePassword** - RFC 7617 Base64(username:password)
- **OAuthToken** - Bearer token in Authorization header
- **NegotiatedAuthentication** - Windows/Kerberos (SocketsHttpHandler.Credentials)

### Request Body Types
- None, Text, FormUrlEncoded, MultipartFormData, Binary, Stream

### Retry Policy
- **None** - No retry
- **Basic** - Fixed delay (default 500ms) between retries
- **ExponentialBackoff** - Delay = InitialDelay x (Multiplier ^ attempt) + optional jitter
- **Default retry codes**: 408, 429, 500, 502, 503, 504
- **Retry-After header respected** (seconds or HTTP-date format)
- **MaxRetryAfterDelay** caps server-suggested delay (default 30s)

### Response Handling
- **SaveResponseAsFile** - Save binary response to disk
- **FileOverwrite**: AutoRename, Replace, Discard
- **Default encoding**: UTF-8 (customizable via TextPayloadEncoding)

---

## Critical Gotchas

### Timeouts
1. **NetHttpRequest default: 10,000ms** (10 seconds) - often too low for slow APIs. Property has typo: `TimeoutInMiliseconds` (single 'l')
2. **Legacy HttpClient default: 6,000ms** (6 seconds) - very aggressive
3. **SoapClient: 60,000ms hard-coded** - no override available
4. **Platform can override** via WebApiTestingServiceContext.TimeoutInMiliseconds

### SSL/TLS
5. **DisableSslVerification=false (default)** - validates full chain
6. **When disabled**: callback returns true regardless of SSL errors (security risk)
7. **Client certificates**: PFX/PKCS12 file OR certificate subject from Windows store
8. **TLS protocol options**: Automatic (system default), Tls12, Tls13

### Redirect Handling
9. **FollowRedirects=true (default)** with MaxRedirects=3
10. **SocketsHttpHandler.AllowAutoRedirect** explicitly set to false by default, overridden by config

### Proxy
11. **WebProxyConfiguration**: Address, BypassOnLocal, BypassList (supports wildcards like "*.example.com")
12. **ProxyCredentials** for authenticated proxies

### Multipart/Form-Data
13. **Files NOT disposed until MultipartContent disposed** with request
14. **ContentType inferred from filename extension** or explicit MIME type

### SOAP Specific
15. **SOAPAction header format differs** between SOAP 1.1 (quoted) and 1.2 (in Content-Type)
16. **Action synthesized** from namespace + operation name if not in WSDL
17. **Default namespace fallback**: "http://tempuri.org"

### JSON Serialization
18. **Uses Newtonsoft.Json** (not System.Text.Json)
19. **DeserializeJson<T>** - TypeNameHandling setting can be security risk if processing untrusted JSON
20. **DateParseHandling** affects how date strings are interpreted (DateTime vs DateTimeOffset vs None)

### Cookie Handling
21. **EnableCookies=true by default** - CookieContainer maintained per session
22. **Request-style cookies** (semicolon-separated) normalized before adding to container

### Legacy HttpClient vs NetHttpRequest
23. **HttpClient (legacy)** uses RestSharp; supports OAuth1 (ConsumerKey/Secret/Token)
24. **NetHttpRequest (modern)** uses .NET HttpClient; does NOT support OAuth1
25. **Prefer NetHttpRequest** for new workflows

### Additional Validated Gotchas
26. **NetHttpRequest ContinueOnError defaults to TRUE** - HTTP errors silently swallowed by default; set to false for strict error handling
27. **SoapClient timeout is NOT user-configurable** - hardcoded 60s constant with no activity property override
28. **SSL bypass differs between legacy and modern** - Legacy HttpClient blindly returns true for all SSL errors; NetHttpRequest only bypasses when DisableSslVerification=true AND checks for actual errors
