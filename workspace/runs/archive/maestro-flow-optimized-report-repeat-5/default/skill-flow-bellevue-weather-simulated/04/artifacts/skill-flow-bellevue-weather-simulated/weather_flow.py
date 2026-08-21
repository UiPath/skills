"""
Bellevue Weather Check Flow
----------------------------
A simulated automated flow that checks today's weather in Bellevue, WA
and tells you whether it's a good day or not.
"""

import random
from dataclasses import dataclass
from typing import Literal


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class WeatherReport:
    city: str
    condition: str           # e.g. "Sunny", "Rainy", "Overcast", "Thunderstorm"
    temperature_f: int       # degrees Fahrenheit
    humidity_pct: int        # 0-100
    wind_mph: int            # miles per hour
    uv_index: int            # 0-11+


# ---------------------------------------------------------------------------
# Step 1 – Simulate fetching current weather
# ---------------------------------------------------------------------------

# Realistic Bellevue weather scenarios (weighted toward its actual climate)
_SCENARIOS = [
    WeatherReport("Bellevue, WA", "Sunny",         78,  35, 8,  6),
    WeatherReport("Bellevue, WA", "Partly Cloudy", 65,  55, 10, 4),
    WeatherReport("Bellevue, WA", "Overcast",      58,  70, 12, 2),
    WeatherReport("Bellevue, WA", "Light Rain",    52,  80, 9,  1),
    WeatherReport("Bellevue, WA", "Heavy Rain",    48,  90, 18, 0),
    WeatherReport("Bellevue, WA", "Thunderstorm",  55,  88, 25, 0),
    WeatherReport("Bellevue, WA", "Foggy",         50,  85, 5,  1),
    WeatherReport("Bellevue, WA", "Snowy",         34,  75, 10, 1),
    WeatherReport("Bellevue, WA", "Windy",         60,  50, 32, 3),
    WeatherReport("Bellevue, WA", "Clear",         82,  30, 5,  8),
]

_WEIGHTS = [10, 15, 15, 20, 10, 5, 8, 3, 4, 10]  # probability weights


def fetch_weather() -> WeatherReport:
    """Simulate fetching the current weather for Bellevue, WA."""
    return random.choices(_SCENARIOS, weights=_WEIGHTS, k=1)[0]


# ---------------------------------------------------------------------------
# Step 2 – Evaluate whether it's a good day
# ---------------------------------------------------------------------------

# Scoring thresholds
_BAD_CONDITIONS = {"Heavy Rain", "Thunderstorm", "Snowy"}
_NEUTRAL_CONDITIONS = {"Light Rain", "Foggy", "Overcast"}
_GOOD_CONDITIONS = {"Sunny", "Partly Cloudy", "Clear", "Windy"}

def _score_weather(w: WeatherReport) -> tuple[int, list[str]]:
    """
    Returns a score (0-100) and a list of human-readable reasons.
    Higher score = better day.
    """
    score = 50  # neutral baseline
    reasons: list[str] = []

    # --- Condition ---
    if w.condition in _GOOD_CONDITIONS:
        score += 20
        reasons.append(f"Nice {w.condition.lower()} skies ☀️")
    elif w.condition in _BAD_CONDITIONS:
        score -= 25
        reasons.append(f"{w.condition} — not great for being outside 🌧️")
    else:
        reasons.append(f"{w.condition} conditions — manageable 🌥️")

    # --- Temperature ---
    if 60 <= w.temperature_f <= 80:
        score += 15
        reasons.append(f"Comfortable temperature ({w.temperature_f}°F) 👍")
    elif w.temperature_f < 40:
        score -= 15
        reasons.append(f"Pretty cold at {w.temperature_f}°F 🥶")
    elif w.temperature_f > 90:
        score -= 10
        reasons.append(f"Hot at {w.temperature_f}°F — stay hydrated 🥵")
    else:
        reasons.append(f"Temperature is {w.temperature_f}°F — okay")

    # --- Wind ---
    if w.wind_mph > 25:
        score -= 15
        reasons.append(f"Very windy at {w.wind_mph} mph 🌬️")
    elif w.wind_mph > 15:
        score -= 5
        reasons.append(f"Breezy at {w.wind_mph} mph")
    else:
        reasons.append(f"Calm winds ({w.wind_mph} mph) ✅")

    # --- Humidity ---
    if w.humidity_pct > 80:
        score -= 10
        reasons.append(f"High humidity ({w.humidity_pct}%) feels muggy 💦")
    elif w.humidity_pct < 40:
        score += 5
        reasons.append(f"Low, comfortable humidity ({w.humidity_pct}%)")

    return max(0, min(100, score)), reasons


def evaluate_day(w: WeatherReport) -> tuple[Literal["GOOD", "OKAY", "BAD"], int, list[str]]:
    """Classify the day as GOOD, OKAY, or BAD with a score and reasons."""
    score, reasons = _score_weather(w)

    if score >= 70:
        verdict: Literal["GOOD", "OKAY", "BAD"] = "GOOD"
    elif score >= 45:
        verdict = "OKAY"
    else:
        verdict = "BAD"

    return verdict, score, reasons


# ---------------------------------------------------------------------------
# Step 3 – Format the report
# ---------------------------------------------------------------------------

_VERDICT_EMOJI = {"GOOD": "✅", "OKAY": "🟡", "BAD": "❌"}
_VERDICT_MSG = {
    "GOOD": "It's a great day in Bellevue! Get outside and enjoy it.",
    "OKAY": "It's a decent day in Bellevue — nothing to complain about.",
    "BAD":  "Better stay indoors today. Not ideal weather in Bellevue.",
}


def format_report(w: WeatherReport, verdict: str, score: int, reasons: list[str]) -> str:
    """Build a human-readable weather summary."""
    lines = [
        "=" * 50,
        f"  🌆 BELLEVUE WEATHER CHECK",
        "=" * 50,
        f"  Condition   : {w.condition}",
        f"  Temperature : {w.temperature_f}°F",
        f"  Humidity    : {w.humidity_pct}%",
        f"  Wind        : {w.wind_mph} mph",
        f"  UV Index    : {w.uv_index}",
        "-" * 50,
        f"  DAY SCORE   : {score}/100",
        f"  VERDICT     : {_VERDICT_EMOJI[verdict]}  {verdict}",
        "-" * 50,
        "  WHY?",
    ]
    for r in reasons:
        lines.append(f"    • {r}")
    lines += [
        "-" * 50,
        f"  💬 {_VERDICT_MSG[verdict]}",
        "=" * 50,
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

def run_weather_flow() -> str:
    """
    Full automated flow:
      1. Fetch simulated weather
      2. Evaluate whether it's a good day
      3. Return a formatted report string
    """
    weather = fetch_weather()
    verdict, score, reasons = evaluate_day(weather)
    report = format_report(weather, verdict, score, reasons)
    return report


if __name__ == "__main__":
    print(run_weather_flow())
