import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_finalize_inventory import stage_task_inventory


def test_task_moved_to_another_stage_changes_inventory():
    draft = """
### Stage 1: Intake
##### Task 1.1: Review Application
### Stage 2: Decision
##### Task 2.1: Record Decision
"""
    moved = """
### Stage 1: Intake
### Stage 2: Decision
##### Task 2.1: Review Application
##### Task 2.2: Record Decision
"""

    assert stage_task_inventory(draft) != stage_task_inventory(moved)
