#!/usr/bin/env python3
"""Print the result ids a run of the given task YAMLs must produce, one per line.

A plain task yields its `task_id`; a dataset task yields `<task_id>/<row id>` for every row (what
coder-eval's expand_dataset names them). A dataset that samples rows yields `<task_id>!sampled`:
which rows run is not knowable here, so the publication scrub treats it as inconclusive.
"""

from __future__ import annotations

import json
import pathlib
import sys

import yaml


def ids_for(path: pathlib.Path) -> list[str]:
    task = yaml.safe_load(path.read_text(encoding="utf-8"))
    task_id = str(task["task_id"])
    dataset = task.get("dataset")
    if dataset is None:
        return [task_id]
    if dataset.get("sample_per_stratum") is not None:
        return [f"{task_id}!sampled"]
    if dataset.get("rows") is not None:
        rows = list(dataset["rows"])
    else:
        rows = []
        for rel in dataset["paths"]:
            lines = (path.parent / rel).read_text(encoding="utf-8").splitlines()
            rows.extend(json.loads(line) for line in lines if line.strip())
    field = dataset.get("id_field", "id")
    return [f"{task_id}/{row[field]}" for row in rows]


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print("\n".join(ids_for(pathlib.Path(arg))))
