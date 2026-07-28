#!/usr/bin/env python3
"""Grade the hardcoded-config review.

Planted (HardcodedBot/Main.xaml): a prod API URL, an absolute folder path, a
magic-number timeout and a threshold baked into Assign / Log Message activities.

PASS requires the report to (a) flag the hardcoding AS a problem and (b) point
at externalization (Config file / Assets), via prose or the ST-USG-005 /
ST-DBP-021 codes. "No hardcoded values" does not count. The planted hardcoded
URL must still exist in the fixture.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
from grader_common import report_text, asserts, asserts_any, fixture_contains  # noqa: E402

PROJECT = "HardcodedBot"
RULE_CODES = ("ST-USG-005", "ST-DBP-021")


def main() -> None:
    text = report_text(500)
    lower = text.lower()

    if not fixture_contains(f"{PROJECT}/Main.xaml", "prod-api.acme.com"):
        sys.exit(f"FAIL: {PROJECT}/Main.xaml no longer contains the planted hardcoded "
                 "URL (fixture appears mutated).")

    cited = [c for c in RULE_CODES if c in text]
    has_hardcode = asserts_any(text, ["hardcod", "hard-cod", "hard cod", "magic number",
                                      "magic-number", "baked in", "baked-in"], presence=True)
    has_externalize = any(w in lower for w in ("config", "asset", "externaliz", "parameteriz",
                                              "environment variable", "settings file"))

    if cited:
        print(f"OK: report cites rule code(s): {cited}")
    elif has_hardcode and has_externalize:
        print("OK: report flags hardcoded values and recommends Config/Assets")
    else:
        miss = []
        if not has_hardcode:
            miss.append("no hardcoding flagged as a problem")
        if not has_externalize:
            miss.append("no Config/Assets externalization recommendation")
        sys.exit("FAIL: report does not identify the hardcoded-config defect — "
                 + "; ".join(miss) + " (expected ST-USG-005 / ST-DBP-021 or prose).")
    print("PASS")


if __name__ == "__main__":
    main()
