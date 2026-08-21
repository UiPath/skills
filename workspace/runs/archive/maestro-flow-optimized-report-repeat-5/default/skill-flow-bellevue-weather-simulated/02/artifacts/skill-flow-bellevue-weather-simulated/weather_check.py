"""
Bellevue Weather Check Flow
Simulates fetching current weather for Bellevue, WA and determines
whether it's a nice day.
"""

import random


# ---------------------------------------------------------------------------
# Simulated weather data
# ---------------------------------------------------------------------------

WEATHER_CONDITIONS = [
    {
        "condition": "Sunny",
        "temp_f": 72,
        "humidity_pct": 35,
        "wind_mph": 5,
        "precipitation_in": 0.0,
    },
    {
        "condition": "Partly Cloudy",
        "temp_f": 65,
        "humidity_pct": 55,
        "wind_mph": 10,
        "precipitation_in": 0.0,
    },
    {
        "condition": "Overcast",
        "temp_f": 58,
        "humidity_pct": 70,
        "wind_mph": 12,
        "precipitation_in": 0.0,
    },
    {
        "condition": "Light Rain",
        "temp_f": 52,
        "humidity_pct": 85,
        "wind_mph": 15,
        "precipitation_in": 0.25,
    },
    {
        "condition": "Heavy Rain",
        "temp_f": 47,
        "humidity_pct": 95,
        "wind_mph": 22,
        "precipitation_in": 1.1,
    },
    {
        "condition": "Thunderstorms",
        "temp_f": 55,
        "humidity_pct": 90,
        "wind_mph": 35,
        "precipitation_in": 0.80,
    },
    {
        "condition": "Fog",
        "temp_f": 50,
        "humidity_pct": 98,
        "wind_mph": 3,
        "precipitation_in": 0.0,
    },
    {
        "condition": "Clear and Cool",
        "temp_f": 60,
        "humidity_pct": 45,
        "wind_mph": 8,
        "precipitation_in": 0.0,
    },
]


# ---------------------------------------------------------------------------
# Step 1 – Fetch weather (simulated)
# ---------------------------------------------------------------------------

def fetch_weather(location: str) -> dict:
    """Return a simulated weather reading for *location*."""
    data = random.choice(WEATHER_CONDITIONS)
    return {
        "location": location,
        **data,
    }


# ---------------------------------------------------------------------------
# Step 2 – Evaluate whether it's a nice day
# ---------------------------------------------------------------------------

NICE_DAY_RULES = {
    "min_temp_f": 55,
    "max_temp_f": 85,
    "max_precipitation_in": 0.05,
    "max_wind_mph": 20,
    "bad_conditions": {"Heavy Rain", "Thunderstorms", "Fog"},
}


def evaluate_day(weather: dict) -> tuple[bool, list[str]]:
    """
    Return (is_nice, reasons).
    *reasons* lists each factor that made the day NOT nice.
    """
    rules = NICE_DAY_RULES
    reasons = []

    if weather["temp_f"] < rules["min_temp_f"]:
        reasons.append(
            f"Too cold ({weather['temp_f']}°F — minimum is {rules['min_temp_f']}°F)"
        )
    if weather["temp_f"] > rules["max_temp_f"]:
        reasons.append(
            f"Too hot ({weather['temp_f']}°F — maximum is {rules['max_temp_f']}°F)"
        )
    if weather["precipitation_in"] > rules["max_precipitation_in"]:
        reasons.append(
            f"Too much rain ({weather['precipitation_in']}\" — threshold is {rules['max_precipitation_in']}\")"
        )
    if weather["wind_mph"] > rules["max_wind_mph"]:
        reasons.append(
            f"Too windy ({weather['wind_mph']} mph — max is {rules['max_wind_mph']} mph)"
        )
    if weather["condition"] in rules["bad_conditions"]:
        reasons.append(f"Unpleasant condition: {weather['condition']}")

    return (len(reasons) == 0, reasons)


# ---------------------------------------------------------------------------
# Step 3 – Report
# ---------------------------------------------------------------------------

def report(weather: dict, is_nice: bool, reasons: list[str]) -> str:
    lines = [
        "=" * 50,
        f"  Bellevue Weather Check — {weather['location']}",
        "=" * 50,
        f"  Condition   : {weather['condition']}",
        f"  Temperature : {weather['temp_f']}°F",
        f"  Humidity    : {weather['humidity_pct']}%",
        f"  Wind        : {weather['wind_mph']} mph",
        f"  Precipitation: {weather['precipitation_in']}\"",
        "-" * 50,
    ]

    if is_nice:
        lines.append("  ☀️  VERDICT: It's a NICE DAY! Get outside!")
    else:
        lines.append("  🌧️  VERDICT: NOT a nice day. Stay cozy indoors.")
        lines.append("")
        lines.append("  Reasons:")
        for r in reasons:
            lines.append(f"    • {r}")

    lines.append("=" * 50)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

def run_flow(location: str = "Bellevue, WA") -> None:
    print(f"\nChecking weather for {location}...\n")

    # Step 1 – fetch
    weather = fetch_weather(location)

    # Step 2 – evaluate
    is_nice, reasons = evaluate_day(weather)

    # Step 3 – report
    output = report(weather, is_nice, reasons)
    print(output)


if __name__ == "__main__":
    run_flow()
