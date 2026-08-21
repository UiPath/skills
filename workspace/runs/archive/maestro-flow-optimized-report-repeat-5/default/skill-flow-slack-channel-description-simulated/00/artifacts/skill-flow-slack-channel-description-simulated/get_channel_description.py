#!/usr/bin/env python3
"""
Slack Channel Description Fetcher
----------------------------------
Fetches and displays the description of the #office-bellevue Slack channel.

Usage:
    python get_channel_description.py

Configuration:
    - By default runs in SIMULATED mode (no Slack token needed).
    - To use real Slack data, set the SLACK_API_TOKEN environment variable:

        export SLACK_API_TOKEN="xoxb-your-token-here"
        python get_channel_description.py

How to get a Slack API token (when you're ready):
    1. Go to https://api.slack.com/apps and click "Create New App"
    2. Choose "From scratch", give it a name, and pick your workspace
    3. Under "OAuth & Permissions", add the scope: channels:read
    4. Click "Install to Workspace" and copy the "Bot User OAuth Token"
    5. Set it as the SLACK_API_TOKEN environment variable (see above)
"""

import os
import sys

# ── Configuration ─────────────────────────────────────────────────────────────

CHANNEL_NAME = "office-bellevue"   # Channel to look up (without the #)
SLACK_API_TOKEN = os.environ.get("SLACK_API_TOKEN", "")

# ── Simulated data (used when no real token is provided) ──────────────────────

SIMULATED_DESCRIPTION = (
    "Everything for the Bellevue office — announcements, events, "
    "desk bookings, and day-to-day office coordination. "
    "Say hi if you're working from Bellevue today! 👋"
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def display_result(description: str, simulated: bool) -> None:
    """Print the channel description in a clear, readable format."""
    mode_label = " (simulated)" if simulated else ""
    print()
    print("=" * 55)
    print(f"  Slack Channel: #{CHANNEL_NAME}{mode_label}")
    print("=" * 55)
    if description:
        print(f"  Description: {description}")
    else:
        print("  Description: (none set)")
    print("=" * 55)
    print()


def fetch_real_description(token: str) -> str:
    """
    Fetch the channel description from the real Slack API.
    Requires the `requests` library:  pip install requests
    """
    try:
        import requests
    except ImportError:
        print("ERROR: The 'requests' library is not installed.")
        print("       Run:  pip install requests")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}
    cursor = None
    page = 0

    while True:
        page += 1
        params = {
            "exclude_archived": "true",
            "limit": 200,
            "types": "public_channel,private_channel",
        }
        if cursor:
            params["cursor"] = cursor

        response = requests.get(
            "https://slack.com/api/conversations.list",
            headers=headers,
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("ok"):
            error = data.get("error", "unknown error")
            print(f"ERROR: Slack API returned an error: {error}")
            if error == "missing_scope":
                print("       Make sure your token has the 'channels:read' scope.")
            sys.exit(1)

        channels = data.get("channels", [])
        for channel in channels:
            if channel.get("name") == CHANNEL_NAME:
                purpose = channel.get("purpose", {}).get("value", "")
                topic   = channel.get("topic",   {}).get("value", "")
                # Return purpose (description) first, fall back to topic
                return purpose or topic or ""

        # Follow pagination cursor if more pages exist
        next_cursor = data.get("response_metadata", {}).get("next_cursor", "")
        if not next_cursor:
            break
        cursor = next_cursor

    # Channel not found
    print(f"ERROR: Channel #{CHANNEL_NAME} was not found in your workspace.")
    print("       Check the channel name or ensure the bot has been added to it.")
    sys.exit(1)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if SLACK_API_TOKEN:
        # Real mode — call the Slack API
        print(f"Fetching description for #{CHANNEL_NAME} from Slack...")
        description = fetch_real_description(SLACK_API_TOKEN)
        display_result(description, simulated=False)
    else:
        # Simulated mode — show example data, no network call needed
        print("No SLACK_API_TOKEN found — running in simulated mode.")
        display_result(SIMULATED_DESCRIPTION, simulated=True)


if __name__ == "__main__":
    main()
