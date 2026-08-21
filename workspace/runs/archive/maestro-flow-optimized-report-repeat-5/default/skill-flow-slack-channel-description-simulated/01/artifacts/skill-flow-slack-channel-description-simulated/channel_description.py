#!/usr/bin/env python3
"""
Slack Channel Description Viewer
---------------------------------
Fetches and displays the description (purpose/topic) for a Slack channel.

Usage:
  python channel_description.py                  # interactive / simulated mode
  python channel_description.py --channel general # specify channel directly
  SLACK_TOKEN=xoxb-... python channel_description.py  # real Slack API mode
"""

import os
import sys
import argparse

# ---------------------------------------------------------------------------
# Simulated channel data (used when no real SLACK_TOKEN is provided)
# ---------------------------------------------------------------------------
SIMULATED_CHANNELS = {
    "general": {
        "topic":   "Company-wide announcements and discussion",
        "purpose": "The one channel everyone is in — share news, kudos, and general updates here.",
    },
    "engineering": {
        "topic":   "All things code & infrastructure",
        "purpose": "Technical discussions, incident alerts, and engineering team updates.",
    },
    "marketing": {
        "topic":   "Campaigns, content, and brand",
        "purpose": "Where the marketing team coordinates launches, copy reviews, and design feedback.",
    },
    "random": {
        "topic":   "Non-work fun stuff",
        "purpose": "Water-cooler chat, memes, weekend plans — anything goes here!",
    },
    "design": {
        "topic":   "UI/UX, brand assets, and creative reviews",
        "purpose": "Share mockups, gather feedback, and track design system updates.",
    },
}


def fetch_simulated(channel_name: str) -> dict | None:
    """Return fake channel info from the simulated data dictionary."""
    name = channel_name.lstrip("#").lower()
    return SIMULATED_CHANNELS.get(name)


def fetch_real(channel_name: str, token: str) -> dict | None:
    """
    Fetch real channel info from Slack using slack_sdk.
    Returns a dict with 'topic' and 'purpose' keys, or None if not found.
    """
    try:
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError
    except ImportError:
        print("  [!] slack_sdk is not installed. Run:  pip install slack-sdk")
        sys.exit(1)

    client = WebClient(token=token)
    name = channel_name.lstrip("#").lower()

    try:
        # conversations.list lets us search by name
        for page in client.conversations_list(types="public_channel,private_channel"):
            for ch in page["channels"]:
                if ch["name"].lower() == name:
                    return {
                        "topic":   ch.get("topic", {}).get("value", ""),
                        "purpose": ch.get("purpose", {}).get("value", ""),
                    }
        return None  # channel not found
    except SlackApiError as e:
        print(f"  [!] Slack API error: {e.response['error']}")
        sys.exit(1)


def display_result(channel_name: str, info: dict) -> None:
    """Pretty-print the channel description to the terminal."""
    name = channel_name.lstrip("#")
    width = 60

    print()
    print("=" * width)
    print(f"  Channel: #{name}")
    print("=" * width)

    topic = info.get("topic", "").strip()
    purpose = info.get("purpose", "").strip()

    if topic:
        print(f"\n  Topic\n  {'─' * (width - 4)}\n  {topic}")
    else:
        print(f"\n  Topic\n  {'─' * (width - 4)}\n  (no topic set)")

    if purpose:
        print(f"\n  Purpose\n  {'─' * (width - 4)}\n  {purpose}")
    else:
        print(f"\n  Purpose\n  {'─' * (width - 4)}\n  (no purpose set)")

    print()
    print("=" * width)
    print()


def list_simulated_channels() -> None:
    """Print the available simulated channel names."""
    print("\n  Available simulated channels:")
    for name in sorted(SIMULATED_CHANNELS):
        print(f"    • #{name}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch and display a Slack channel's description."
    )
    parser.add_argument(
        "--channel", "-c",
        help="Channel name to look up (with or without the # prefix)",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available channels (simulated mode only)",
    )
    args = parser.parse_args()

    token = os.environ.get("SLACK_TOKEN", "").strip()
    simulated = not token

    if simulated:
        print("\n  [INFO] No SLACK_TOKEN found — running in simulated mode.")
        print("         Set the SLACK_TOKEN environment variable to use the real Slack API.\n")

    if args.list:
        if simulated:
            list_simulated_channels()
        else:
            print("  [INFO] --list is only available in simulated mode.")
        return

    # Determine channel name
    channel = args.channel
    if not channel:
        if simulated:
            list_simulated_channels()
        channel = input("  Enter a channel name (e.g. general): ").strip()
        if not channel:
            print("  No channel name provided. Exiting.")
            sys.exit(0)

    # Fetch info
    if simulated:
        info = fetch_simulated(channel)
    else:
        info = fetch_real(channel, token)

    # Display
    if info is None:
        print(f"\n  Channel '#{channel.lstrip('#')}' not found.\n")
        if simulated:
            list_simulated_channels()
        sys.exit(1)

    display_result(channel, info)


if __name__ == "__main__":
    main()
