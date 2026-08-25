---
confidence: medium
---

# OCR Input & Runtime Errors

## Context

A UiPath OCR activity failed on its input or during recognition — a missing/invalid image, an unsupported parameter, or a runtime timeout — or it returned an empty result with no exception. Route on the message text (and on the no-exception empty-result case).

What this looks like:
- `No image input was provided. Bind one of Image or ImageFile.` (`ArgumentException`) — both `Image` and `ImageFile` were null.
- `ArgumentNullException` on the image argument — an unresolved image variable.
- `Rotation angle is not supported` (`NotSupportedException`) — a rotation other than 0 / 90 / 180 / 270 was passed to the local server.
- `OCR timeout exceeded <timeout>.` (`TimeoutException`) — recognition did not complete within the timeout, after internal retries.
- `Usage must be Document.` / `Usage must be Screen.` (`ArgumentException`) — a scrape engine was called with the wrong usage.
- Empty output, **no exception** — no text was detected; the activity returns an empty `OCROutput`.

What can cause it:
- Neither (or an unresolved) image input is bound.
- An unsupported rotation value, or an image too large/complex to finish within the timeout.
- The wrong scrape-engine usage for the calling activity.
- The target genuinely contains no legible text at the given resolution (empty-result, not an error).

What to look for:
- The message (or the empty-result, no-exception case) and the image source the activity used at run time.
- Whether exactly one of `Image` / `ImageFile` is bound to a valid, readable image.
- The `Timeout` value and the image size/complexity for a timeout; the input legibility for an empty result.

## Investigation

1. Capture the message (or note the empty-result, no-exception case) and the image source the activity used.
2. Confirm exactly one of `Image` / `ImageFile` is bound to a valid, readable image resolved at run time.
3. For a timeout, check image size/complexity against the `Timeout`; for empty output, confirm the input actually contains legible text at adequate resolution.

## Resolution

### `No image input was provided` / `ArgumentNullException`
Bind exactly one valid image (`Image` or `ImageFile`), and ensure the upstream step that produces it resolved before the OCR activity.

### `Rotation angle is not supported`
Use a supported rotation (0 / 90 / 180 / 270), or pre-rotate the image before OCR.

### `OCR timeout exceeded`
Reduce the image size/complexity or raise the `Timeout`; confirm the engine/endpoint is responsive (an unresponsive endpoint is an endpoint issue, not an input one).

### `Usage must be Document.` / `Usage must be Screen.`
Use the OCR engine variant matching the calling activity — Document usage for document OCR, Screen usage for screen OCR.

### Empty result, no exception
This is not an exception path. Verify the input contains legible text at adequate resolution, adjust the OCR engine/scale, or handle the empty-result case in the workflow — do not treat the empty string as a fault.
