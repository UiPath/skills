# Time Trigger

`UiPath.Core.Activities.TimeTrigger`

Schedule a recurrent time to start a job.

**Package:** `UiPath.System.Activities`
**Category:** Triggers

## Properties

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Frequency` | Frequency | `TimeFrequency` | — | The scheduling frequency mode. Determines which other scheduling properties are shown. |
| `TimeZone` | Time Zone | `string` | — | The time zone used to interpret scheduling times. Supports IANA and Windows time zone identifiers. |
| `CronExpression` | Cron Expression | `string` | `"0 0 12 ? * MON-FRI *"` | A Quartz-style cron expression. Visible only when `Frequency` is `CronExpression`. |
| `DailyRepeat` | Daily Repeat | `int?` | — | Repeat interval in days. Visible only when `Frequency` is `Daily`. |
| `DailyStartingTime` | Daily Starting Time | `DateTime?` | — | The time of day to start when using the Daily frequency. Visible only when `Frequency` is `Daily`. |
| `HourlyRepeat` | Hourly Repeat | `int?` | — | Repeat interval in hours. Visible only when `Frequency` is `Hourly`. |
| `HourlyStartingMinutes` | Hourly Starting Minutes | `int?` | — | Minutes past the hour at which to start when using the Hourly frequency. Visible only when `Frequency` is `Hourly`. |
| `MinuteByMinuteRepeat` | Minute By Minute Repeat | `int?` | — | Repeat interval in minutes. Visible only when `Frequency` is `MinuteByMinute`. |
| `WeeklyDaysToRunOn` | Weekly Days To Run On | `List<DayOfWeek>` | — | Days of the week on which to trigger. Visible when `Frequency` is `Weekly`. |
| `WeeklyStartingTime` | Weekly Starting Time | `DateTime?` | — | The time of day to start when using the Weekly frequency. Visible only when `Frequency` is `Weekly`. |
| `MonthlyRepeat` | Monthly Repeat | `int?` | — | Repeat interval in months. Visible only when `Frequency` is `Monthly`. |
| `MonthDaySelection` | Month Day Selection | `MonthDaySelectionType` | — | Controls whether to trigger on specific calendar days or on a weekday-of-month pattern. Visible only when `Frequency` is `Monthly`. |
| `MonthlyDaysToRunOn` | Monthly Days To Run On | `List<DayOfWeek>` | — | Days of the week to use with the monthly weekday pattern. |
| `DaysOfMonthToRunOn` | Days of the month | `List<string>` | — | Specific calendar day numbers of the month to trigger on. |
| `MonthlyStartingTime` | Monthly Starting Time | `DateTime?` | — | The time of day to start when using the Monthly frequency. Visible only when `Frequency` is `Monthly`. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `CurrentJobInfo` | Runtime information about the triggered job, including Process name, Workflow name, User Name, User Email, and Timestamp. |

## Valid Configurations

The properties shown in the designer depend on the selected `Frequency` value:

### Hourly

Set `Frequency` to `Hourly`. Configure:
- `HourlyRepeat` — run every N hours.
- `HourlyStartingMinutes` — minutes past the hour when the trigger fires.

### Daily

Set `Frequency` to `Daily`. Configure:
- `DailyRepeat` — run every N days.
- `DailyStartingTime` — time of day (hour and minute) at which to fire.

### Weekly

Set `Frequency` to `Weekly`. Configure:
- `WeeklyDaysToRunOn` — which days of the week to fire.
- `WeeklyStartingTime` — time of day at which to fire on those days.

### Monthly

Set `Frequency` to `Monthly`. Configure:
- `MonthlyRepeat` — run every N months.
- `MonthDaySelection` — choose between specific calendar days (`DaysOfMonthToRunOn`) or a weekday-of-month pattern (`MonthlyDaysToRunOn`).
- `MonthlyStartingTime` — time of day at which to fire.

### Minute By Minute

Set `Frequency` to `MinuteByMinute`. Configure:
- `MinuteByMinuteRepeat` — run every N minutes.

### Cron Expression

Set `Frequency` to `CronExpression`. Configure:
- `CronExpression` — a Quartz-style seven-field cron string (seconds, minutes, hours, day-of-month, month, day-of-week, year).
- `TriggerEveryPlaceHolder` is displayed as a read-only hint when `Frequency` is `Weekly` or `CronExpression`.

### Enum Reference

**`TimeFrequency`**

| Value | Description |
|-------|-------------|
| `Hourly` | Trigger every N hours |
| `Daily` | Trigger every N days at a specified time |
| `Weekly` | Trigger on specified days of the week |
| `Monthly` | Trigger on specified days of the month |
| `MinuteByMinute` | Trigger every N minutes |
| `CronExpression` | Trigger according to a Quartz cron expression |

**`MonthDaySelectionType`**

| Value | Description |
|-------|-------------|
| `DayOfMonth` | Trigger on specific numbered days of the month |
| `DayOfWeek` | Trigger on a named weekday occurrence within the month |

## XAML Example

```xml
<!-- Daily at 09:00, every weekday -->
<ui:TimeTrigger
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Time Trigger"
    Frequency="Daily"
    DailyRepeat="1"
    DailyStartingTime="[New DateTime(2000,1,1,9,0,0)]"
    TimeZone="UTC"
    Result="{x:Reference jobInfo}" />
```

```xml
<!-- Cron expression: every weekday at noon -->
<ui:TimeTrigger
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Time Trigger"
    Frequency="CronExpression"
    CronExpression="0 0 12 ? * MON-FRI *"
    TimeZone="UTC"
    Result="{x:Reference jobInfo}" />
```

## Notes

- **Time Trigger** is a scope/container activity. Place the automation logic to execute on each scheduled firing inside its body.
- The `Result` output provides a `CurrentJobInfo` object accessible within the trigger body for runtime context.
- `TimeZone` accepts standard IANA time zone identifiers (e.g., `America/New_York`) or Windows time zone names (e.g., `Eastern Standard Time`).
- Cron expressions follow the Quartz scheduler format with seven fields. The default `"0 0 12 ? * MON-FRI *"` fires at 12:00 noon every weekday.
