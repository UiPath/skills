---
confidence: high
---

# sdk.isAuthenticated() Returns false After Callback

## Context

What this looks like:
- The browser returns from UiPath with `?code=...` in the URL (the OAuth authorization succeeded), but `sdk.isAuthenticated()` stays `false`
- The app bounces the user back to sign-in even though they just logged in — a loop where `?code=` reappears each round
- No OAuth `error=` on the callback URL (the provider did not reject anything)

What can cause it:
- The app checks `sdk.isAuthenticated()` **without first calling `sdk.completeOAuth()`** to exchange the `?code=` for tokens
- The app does custom `URLSearchParams` / `window.location` parsing of the callback instead of the SDK's `sdk.isInOAuthCallback()` + `sdk.completeOAuth()`
- Stale PKCE state in browser storage from a previous, interrupted attempt

What to look for:
- **Discriminator vs [redirect-uri-mismatch.md](./redirect-uri-mismatch.md):** there the provider *rejects* the redirect (`error=redirect_uri_mismatch`, never returns a code). Here the code *returns fine* (`?code=` present) but the app never exchanges it. Route by whether a `?code=` came back.
- Whether the app's bootstrap code calls `completeOAuth()` on the callback before gating on `isAuthenticated()`

## Investigation

1. Confirm a `?code=` is present in the callback URL (authorization succeeded) and there is no `error=` param.

2. Inspect how the app handles the callback — the bug is in the auth bootstrap:

   ```bash
   grep -rnE "completeOAuth|isInOAuthCallback|isAuthenticated|URLSearchParams|location\.search" src/
   ```

   Red flag: `isAuthenticated()` (or a manual `params.has('code')` branch) with no `completeOAuth()` call on the callback path.

## Resolution

- **Use the SDK callback sequence** in the app's bootstrap, in this order:

  ```typescript
  if (sdk.isInOAuthCallback()) {
    await sdk.completeOAuth();   // exchange ?code= for tokens — required before isAuthenticated()
  }
  if (!sdk.isAuthenticated()) {
    await sdk.initialize();      // start a fresh OAuth flow
    return;
  }
  // authenticated — safe to use SDK services
  ```

  Replace any custom `URLSearchParams`/`window.location` code-detection with `sdk.isInOAuthCallback()`.

- **Clear stale PKCE state** (localStorage/sessionStorage/cookies) and re-authenticate after the fix, so a leftover interrupted exchange does not mask the corrected flow.
