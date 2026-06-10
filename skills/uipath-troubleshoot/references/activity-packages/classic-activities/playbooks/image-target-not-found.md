---
confidence: medium
---

# Image Target Not Found / Did Not Vanish

## Context

A classic image-based activity did not behave as expected. The most common case is `Wait Image
Vanish`: either the image was never matched on screen, or it was still present when the timeout
expired (which surfaces as `ActivityTimeoutException` / "Activity timeout exceeded"). Image matching
compares a captured bitmap against the live screen, so it is sensitive to any rendering difference.

What this looks like:
- `Wait Image Vanish` times out because the image is still detected on screen
- An image is never matched even though a human can see it
- The behavior differs between the developer machine and the robot machine, or between runs

What can cause it:
- Display scaling / DPI differs between design time and run time, so the captured image no longer
  matches pixel-for-pixel
- Screen resolution, color depth, theme (light/dark), or font rendering differs on the robot machine
- The underlying operation the image represents never completed, so the image genuinely never
  vanishes (the wait is correctly reporting a stuck state)
- The robot session is locked or in a disconnected RDP session, so the screen does not render
- The accuracy/similarity threshold is too strict for the small rendering differences present
- Anti-aliasing, transparency, or animation makes the region unstable frame to frame

What to look for:
- Whether the robot machine's display scaling, resolution, and theme match where the image was
  captured
- Whether the session was interactive and unlocked during the run
- Whether the image genuinely should have vanished (did the underlying operation finish?)
- Whether the same step works on the developer machine but not the robot

## Investigation

1. Confirm the activity is image-based and what it is waiting for (image to vanish / to be matched).
2. Compare the robot machine's display scaling, resolution, color depth, and theme against the
   environment where the image was captured.
3. Verify the robot session was interactive and unlocked at run time.
4. Determine whether the underlying operation that should make the image vanish actually completed.
5. If matching is flaky, review the configured accuracy/similarity threshold against the rendering
   differences observed.

## Resolution

- **If display scaling/resolution/theme differ:** align the robot machine's display settings with the
  capture environment, or re-capture the image on the robot machine.
- **If the session was locked/disconnected:** run the process in an interactive, unlocked session.
- **If the underlying operation never finished:** fix that operation — the image not vanishing is a
  correct symptom of the real problem, not an image-matching fault.
- **If matching is too strict for minor rendering differences:** adjust the accuracy/similarity
  threshold to a realistic value, or select a more stable image region.
- Prefer selector-based automation over image-based where the application supports it, since image
  matching is inherently environment-sensitive.
