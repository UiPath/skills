#!/usr/bin/env python3
"""Verify that the Credit Analyst is assigned only on the high side of $5M."""

from __future__ import annotations

import re
import sys
from pathlib import Path


THRESHOLD = r"(?:\$?\s*5\s*(?:m(?:illion)?|million)\b|5,?000,?000(?:\.0+)?\b|5_000_000\b|5e6\b)"
HIGH_SIDE = rf"(?:>(?!=)\s*{THRESHOLD}|(?:over|above|greater\s+than|more\s+than|in\s+excess\s+of)\s*{THRESHOLD})"
LOW_SIDE = re.compile(
    rf"(?:<=|<)\s*{THRESHOLD}|\b(?:at\s+or\s+below|below|under|up\s+to|no\s+more\s+than|not\s+more\s+than)\b",
    re.IGNORECASE,
)
OTHER_ROLE = re.compile(r"\bunderwriter\b", re.IGNORECASE)
OTHER_ROLE_CONTRAST = re.compile(
    r"\b(?:instead\s+of|rather\s+than|not)\s+(?:the\s+)?underwriter\b",
    re.IGNORECASE,
)
NEGATION = re.compile(
    r"\b(?:do\s+not|must\s+not|should\s+not|cannot|can't|never|not|ineligible)\b",
    re.IGNORECASE,
)
POST_ACTOR_NEGATION = re.compile(
    r"^\W*(?:role\s+)?(?:"
    r"(?:must|should|can|is|are|be)\s+not\b|cannot\b|can't\b|never\b|ineligible\b|"
    r"not\s+(?:be\s+)?(?:assigned|routed|required|eligible|permitted)\b)",
    re.IGNORECASE,
)
EXECUTION_SIGNAL = re.compile(
    r"(?:=js:|vars\.|\b\w*(?:owner|recipient)\b|\b(?:assign|assignment|route|condition|guard|when|if|task|require)\w*\b)",
    re.IGNORECASE,
)


# the same rule written from the low side: "<= $5M -> Underwriter, else Credit Analyst"
LOW_THEN_ELSE = re.compile(
    rf"(?:<=\s*|\b(?:at\s+or\s+below|not\s+more\s+than|no\s+more\s+than|up\s+to)\s+){THRESHOLD}"
    rf".{{0,120}}?underwriter.{{0,40}}?(?::|\belse\b|\botherwise\b).{{0,40}}?credit\s*analyst",
    re.IGNORECASE,
)


def has_credit_analyst_gate(text: str) -> bool:
    """Accept a high-side comparator in either phrase order, or a low-side one whose else-branch is the Credit Analyst."""
    for line in text.splitlines():
        for clause in re.split(r";|(?<=[.!])\s+", line):
            if LOW_THEN_ELSE.search(clause) and EXECUTION_SIGNAL.search(clause) and not NEGATION.search(clause):
                return True
    patterns = (
        (
            re.compile(
                rf"credit\s*analyst(?P<between>.{{0,160}}?){HIGH_SIDE}",
                re.IGNORECASE,
            ),
            False,
        ),
        (
            re.compile(
                rf"{HIGH_SIDE}(?P<between>.{{0,160}}?)credit\s*analyst",
                re.IGNORECASE,
            ),
            True,
        ),
    )
    for line in text.splitlines():
        for clause in re.split(r";|(?<=[.!])\s+", line):
            for pattern, reject_other_role_prefix in patterns:
                for match in pattern.finditer(clause):
                    between = match.group("between")
                    if (
                        LOW_SIDE.search(between)
                        or (
                            OTHER_ROLE.search(between)
                            and not OTHER_ROLE_CONTRAST.search(between)
                        )
                        or NEGATION.search(OTHER_ROLE_CONTRAST.sub("", match.group(0)))
                        or NEGATION.search(clause[: match.start()])
                        or POST_ACTOR_NEGATION.search(clause[match.end() :])
                        or not EXECUTION_SIGNAL.search(clause)
                    ):
                        continue
                    if reject_other_role_prefix and OTHER_ROLE.search(
                        clause[: match.start()]
                    ) and not LOW_SIDE.search(clause[: match.start()]):
                        continue
                    return True
    return False


def main() -> None:
    paths = [Path(value) for value in sys.argv[1:]]
    existing = [path for path in paths if path.is_file()]
    if not existing:
        sys.exit("FAIL: no SDD artifact was found")
    text = "\n".join(path.read_text(encoding="utf-8") for path in existing)
    if not has_credit_analyst_gate(text):
        sys.exit(
            "FAIL: no executable high-side Credit Analyst gate ties the role "
            "to loans over $5M"
        )
    print("OK: Credit Analyst is gated to loans over $5M")


if __name__ == "__main__":
    main()
