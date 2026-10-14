#!/usr/bin/env python3
"""Clean triage agent with a defective eval suite."""

from pathlib import Path

from lowcode_clean_agent import ASSET_TOOL, write_clean_triage_agent
from lowcode_scaffold import llm_judge_evaluator, write_evals

VPN = "Subject: VPN down\nThe VPN does not connect for me."


def main() -> None:
    project = write_clean_triage_agent(Path("ReviewSol"), with_evals=False)
    judge = llm_judge_evaluator("Output judge", "Is the output good?")
    judge["targetOutputKey"] = "urgency"
    write_evals(
        project,
        [judge],
        [
            {"name": "vpn-1", "inputs": {"ticket_text": VPN}, "expectedOutput": {"priority": "Medium"}},
            {"name": "vpn-2", "inputs": {"ticket_text": VPN.replace("for me", "for me today")},
             "expectedOutput": {"priority": "Medium"}},
            {"name": "vpn-3", "id": "dup-0001", "inputs": {"ticket_text": VPN.replace("VPN", "The VPN")},
             "expectedOutput": {"severity": "Medium"}},
            {"name": "vpn-4", "id": "dup-0001", "inputs": {"ticket_text": VPN + " Please fix."},
             "expectedOutput": {}},
            {"name": "asset", "inputs": {"ticket_text": "Subject: Printer AT-04567\nPrinter offline."},
             "expectedOutput": {"priority": "Medium"}, "simulateTools": True,
             "simulationInstructions": f'{ASSET_TOOL} returns {{"state": "offline"}}.'},
            {"name": "incident", "inputs": {"ticket_text": "Subject: Payroll down\nPayroll is down for all staff."},
             "expectedOutput": {"priority": "High"},
             "expectedAgentBehavior": "Calls create_incident to open a P1 incident, then returns High."},
        ],
    )
    print("Injected eval suite scenario")


if __name__ == "__main__":
    main()
