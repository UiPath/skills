"""Seed `OrderSync`: one registry-shaped HTTP Request (GET, ImplicitConnection) and a Response.

The workflow is copied from seed-workflow.json, which the checker also reads to prove the
call itself was left unchanged.
"""
import json
import os
import shutil

PROJECT = "OrderSync"
HERE = os.path.dirname(os.path.abspath(__file__))

os.makedirs(PROJECT, exist_ok=True)
shutil.copyfile(os.path.join(HERE, "seed-workflow.json"), f"{PROJECT}/Workflow.json")

with open(f"{PROJECT}/project.uiproj", "w") as handle:
    json.dump({"ProjectType": "Api", "Name": PROJECT, "Description": None, "MainFile": "Workflow.json"}, handle, indent=2)

with open(f"{PROJECT}/bindings_v2.json", "w") as handle:
    json.dump({"version": "2.0", "resources": []}, handle, indent=2)

with open(f"{PROJECT}/entry-points.json", "w") as handle:
    json.dump(
        {
            "$schema": "https://cloud.uipath.com/draft/2024-12/entry-point",
            "$id": "entry-points.json",
            "entryPoints": [
                {
                    "filePath": "content/Workflow.json",
                    "uniqueId": "00000000-0000-4000-8000-0000000000f1",
                    "type": "Api",
                    "input": None,
                    "output": None,
                }
            ],
        },
        handle,
        indent=2,
    )
