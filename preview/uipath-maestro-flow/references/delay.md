# Delay

*Behavior and worked examples. Exact signatures, fields, and defaults: [`delay()`](api.md#delay-function).*

Delay pauses the current path for a duration.

Signature: `delay({ duration: string })`.

```ts
.step('cooldown', delay({ duration: 'PT30S' }))
.step('resumedAt', script({ code: 'return new Date().toISOString();' }))
```

When the scenario needs a resume timestamp, compute it after the wait as shown.
The surface exposes relative durations, not an absolute-date wait.

Normal replay may skip real elapsed time. When timing is itself part of the
requirement, use the real-time wait rung with a deliberately short fixture
duration and measure before/after timestamps; product scheduling behavior still
requires platform evidence.

The duration is ISO-8601: `PT30S`, `PT15M`, `PT2H`, `P1D`, `P1W`.
