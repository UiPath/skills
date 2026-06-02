#!/usr/bin/env python3
"""Guardrail recommendation check — SimpleCodedAgent (all scopes).

Validates that guardrail recommendation for a customer-support coded agent
produces:
  - graph.py still parses as Python (ast.parse)
  - At least 2 guardrails added (decorator @guardrail or *<Class>Middleware spread)
  - At least one LLM-scoped adversarial-input guardrail
    (PromptInjectionValidator / UserPromptAttacksValidator / their middleware classes)
  - At least one content-safety guardrail
    (PIIDetectionValidator / HarmfulContentValidator / IntellectualPropertyValidator
     or their middleware classes)
  - All middleware classes spread with `*` (no bare middleware object)
  - Every `@guardrail` decorator appears directly above a `def` (function it decorates)
"""

import ast
import re
import sys
from pathlib import Path

GRAPH = Path("graph.py")

LLM_PROTECTION_TOKENS = {
    "PromptInjectionValidator",
    "UserPromptAttacksValidator",
    "UiPathPromptInjectionMiddleware",
    "UiPathUserPromptAttacksMiddleware",
}

# Adversarial-input validators that share security_category "adversarial_input"
# at LLM PRE. The recommender must pick ONE, not stack both (dedup rule).
PROMPT_INJECTION_TOKENS = {
    "PromptInjectionValidator",
    "UiPathPromptInjectionMiddleware",
}
USER_PROMPT_ATTACKS_TOKENS = {
    "UserPromptAttacksValidator",
    "UiPathUserPromptAttacksMiddleware",
}

CONTENT_SAFETY_TOKENS = {
    "PIIDetectionValidator",
    "HarmfulContentValidator",
    "IntellectualPropertyValidator",
    "UiPathPIIDetectionMiddleware",
    "UiPathHarmfulContentMiddleware",
    "UiPathIntellectualPropertyMiddleware",
}


def read() -> str:
    if not GRAPH.is_file():
        sys.exit(f"FAIL: {GRAPH} not found in {Path.cwd()}")
    return GRAPH.read_text()


def main() -> None:
    src = read()

    # 1. Syntactic — graph.py still parses
    try:
        ast.parse(src)
    except SyntaxError as e:
        sys.exit(f"FAIL: graph.py no longer parses as Python: {e}")
    print("OK: graph.py parses as valid Python")

    # 1b. Adapter-registration import: guardrail symbols must come from
    #     uipath_langchain.guardrails (registers the LangChain adapter as an import
    #     side effect). Importing from uipath.platform.guardrails type-checks and runs
    #     but makes every guardrail silently no-op.
    if "uipath_langchain.guardrails" not in src:
        sys.exit(
            "FAIL: graph.py never imports from uipath_langchain.guardrails. Without it the "
            "LangChain guardrail adapter is not registered and every guardrail silently "
            "no-ops. Import guardrail/validators from uipath_langchain.guardrails."
        )
    if re.search(r"from\s+uipath\.platform\.guardrails\s+import", src):
        sys.exit(
            "FAIL: graph.py imports guardrail symbols from uipath.platform.guardrails. Use "
            "uipath_langchain.guardrails instead — the platform module exposes identical "
            "names but does not register the adapter, so guardrails silently no-op."
        )
    print("OK: guardrail symbols imported from uipath_langchain.guardrails (adapter registers)")

    # 2. Count distinct guardrails added.
    decorator_matches = re.findall(r"@guardrail\s*\(", src)
    middleware_matches = re.findall(r"\*([A-Za-z_][A-Za-z0-9_]*Middleware)\s*\(", src)
    total = len(decorator_matches) + len(middleware_matches)
    if total < 2:
        sys.exit(
            f"FAIL: expected >= 2 guardrails, found {total} "
            f"(@guardrail decorators: {len(decorator_matches)}, "
            f"*Middleware spreads: {len(middleware_matches)})"
        )
    print(
        f"OK: {total} guardrail(s) added "
        f"(@guardrail x{len(decorator_matches)}, *Middleware x{len(middleware_matches)})"
    )

    # 3. LLM-scoped adversarial-input guardrail
    llm_hits = [t for t in LLM_PROTECTION_TOKENS if t in src]
    if not llm_hits:
        sys.exit(
            f"FAIL: no LLM-scoped adversarial-input guardrail found. Expected one of "
            f"{sorted(LLM_PROTECTION_TOKENS)}"
        )
    print(f"OK: LLM-scoped adversarial-input guardrail(s) present: {sorted(llm_hits)}")

    # 3b. De-dup rule: must NOT stack both prompt_injection AND user_prompt_attacks —
    #     they share security_category "adversarial_input" at LLM PRE. Recommend one.
    has_prompt_injection = any(t in src for t in PROMPT_INJECTION_TOKENS)
    has_user_prompt_attacks = any(t in src for t in USER_PROMPT_ATTACKS_TOKENS)
    if has_prompt_injection and has_user_prompt_attacks:
        sys.exit(
            "FAIL: both prompt_injection and user_prompt_attacks validators are present. "
            "They cover the same security_category (adversarial_input) at LLM PRE — "
            "the recommender must pick exactly one, not stack both."
        )
    print("OK: adversarial-input validators are de-duplicated (not both stacked)")

    # 4. Content-safety guardrail
    content_hits = [t for t in CONTENT_SAFETY_TOKENS if t in src]
    if not content_hits:
        sys.exit(
            f"FAIL: no content-safety guardrail found. Expected one of "
            f"{sorted(CONTENT_SAFETY_TOKENS)}"
        )
    print(f"OK: content-safety guardrail(s) present: {sorted(content_hits)}")

    # 5. Every middleware class must be spread with `*` — no bare middleware object
    #    in middleware=[...]. Look for "<ClassName>Middleware(" not preceded by "*".
    bare_middleware = re.findall(r"(?<!\*)\b([A-Za-z_][A-Za-z0-9_]*Middleware)\s*\(", src)
    # Filter to only those that are actually used (also appear in middleware spread or as bare)
    # — but the regex above already finds the bare uses. Any hit is a violation.
    if bare_middleware:
        sys.exit(
            f"FAIL: middleware class(es) not spread with `*`: {bare_middleware}. "
            f"All UiPath…Middleware classes must be unpacked with `*` into middleware=[...]"
        )
    print("OK: all middleware classes are spread with `*`")

    # 6. Every @guardrail decorator must appear directly above a function definition
    #    (allowing stacked decorators in between). Catch obviously-stranded decorators.
    if decorator_matches:
        # Match @guardrail(...) followed (within 500 chars and any number of further
        # @decorators) by a `def `. If a @guardrail has no def after it, that's a fail.
        # We tokenize to avoid greedy matches.
        if not re.search(r"@guardrail\s*\([\s\S]*?\)[\s\S]{0,500}?def\s+\w+", src):
            sys.exit(
                "FAIL: at least one @guardrail decorator is not placed above a function "
                "definition (function or factory)"
            )
        print("OK: @guardrail decorators are followed by function definitions")

    # 7. Default-action rule: a security-critical guardrail must Block, not just Log.
    #    recommend_all always yields at least one adversarial-input guardrail (checked
    #    in step 3), whose catalog-default action is Block — so BlockAction must appear.
    if "BlockAction" not in src:
        sys.exit(
            "FAIL: no BlockAction found. The recommended adversarial-input / content-safety "
            "guardrail(s) default to Block in the catalog — a security-critical guardrail "
            "must block, not be silently downgraded to log-only."
        )
    print("OK: BlockAction present (security-critical guardrail blocks)")

    print("OK: coded recommend-all check passed")


if __name__ == "__main__":
    main()
