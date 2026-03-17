# CreateEventConnections

Key attributes:
- `CalendarArgument` — calendar selector; use Browse mode with `BrowserId` set to the **email address** (Google account) owning the calendar
- `CalendarInputMode` — `"Browse"` or `"UrlOrId"`
- `Title` — event title string
- `StartDateTime` — `DateTime`
- `EndDateTime` — `DateTime`
- `AllDayEvent` — `"True"` / `"False"`
- `Timezone` — IANA timezone string (e.g., `"Europe/London"`)
- `PreferredReturnTimezone` — timezone for returned event times
- `ShowAs` — free/busy status (`"Busy"`, `"Free"`)
- `Visibility` — `"Default"`, `"Public"`, or `"Private"`
- `SendNotification` — `"True"` / `"False"`
- `GuestCanInviteOthers` — `"True"` / `"False"`
- `GuestCanModifyEvent` — `"True"` / `"False"`
- `GuestCanSeeAttendeesList` — `"True"` / `"False"`
- `AddConferenceData` — `"True"` to add Google Meet link
- Output: `Result` as `UiPath.GSuite.Calendar.Models.GSuiteEventItem`
