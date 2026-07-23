#!/usr/bin/env python3
"""Seed and clean up the live name-resolution test project."""

import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path


def run_json(*args, timeout=300):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)
    return json.loads(result.stdout)


def payload_data(payload):
    return payload.get("Data") or payload.get("data") or payload


def seed():
    workspace = Path.cwd()
    fixtures = workspace / "fixtures"
    documents = workspace / "invoice_docs"
    documents.mkdir(exist_ok=True)
    for source in fixtures.glob("*.png"):
        shutil.copy2(source, documents / source.name)

    title = f"codereval-integ-resolve-{uuid.uuid4().hex[:8]}"
    project = payload_data(
        run_json(
            "uip",
            "ixp",
            "projects",
            "create",
            title,
            str(documents),
            "--skip-taxonomy",
            "--output",
            "json",
        )
    )
    name = project.get("ProjectName") or project.get("project_name")
    if not name:
        raise RuntimeError("project create response omitted ProjectName")

    run_json(
        "uip",
        "ixp",
        "projects",
        "import-taxonomy",
        name,
        str(fixtures / "taxonomy.json"),
        "--output",
        "json",
    )
    (workspace / "seed.json").write_text(
        json.dumps({"project_title": title}), encoding="utf-8"
    )
    (workspace / "mocks" / "calls.log").write_text("", encoding="utf-8")


def cleanup():
    title = json.loads(Path("seed.json").read_text(encoding="utf-8"))[
        "project_title"
    ]
    projects = payload_data(
        run_json("uip", "ixp", "projects", "list", "--output", "json", timeout=60)
    )
    projects = projects.get("Projects") or projects.get("projects") or []
    expected_titles = {title, f"{title}-renamed"}
    for project in projects:
        if (project.get("Title") or project.get("title")) not in expected_titles:
            continue
        name = project.get("Name") or project.get("name")
        if name:
            run_json(
                "uip",
                "ixp",
                "projects",
                "delete",
                name,
                "-y",
                "--output",
                "json",
                timeout=60,
            )


if __name__ == "__main__":
    if sys.argv[1] == "seed":
        seed()
    else:
        try:
            cleanup()
        except Exception as error:
            print(f"WARN: name-resolution cleanup failed: {error}")
