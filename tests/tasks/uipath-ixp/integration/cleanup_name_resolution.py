#!/usr/bin/env python3
"""Best-effort cleanup for the title-only name-resolution integration task."""

import json
import subprocess
import sys
from pathlib import Path


def invoke(command: list[str], timeout: int = 60):
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception as exc:
        print(f"WARN: could not invoke {' '.join(command)}: {exc}")
        return None


def main() -> int:
    report_path = Path("report.json")
    if not report_path.is_file():
        print("SKIP: report.json not found")
        return 0

    try:
        title = json.loads(report_path.read_text(encoding="utf-8")).get(
            "project_title"
        )
    except Exception as exc:
        print(f"SKIP: could not read report.json: {exc}")
        return 0
    if not title:
        print("SKIP: report.json has no project_title")
        return 0

    listed = invoke(["uip", "ixp", "projects", "list", "--output", "json"])
    if listed is None or listed.returncode != 0:
        output = "" if listed is None else (listed.stderr or listed.stdout or "")
        print(f"WARN: could not list projects: {output[:300]}")
        return 0

    try:
        payload = json.loads(listed.stdout)
        data = payload.get("Data") or payload.get("data") or payload
        projects = data.get("Projects") or data.get("projects") or []
    except Exception as exc:
        print(f"WARN: could not parse projects list: {exc}")
        return 0

    expected_titles = {title, f"{title}-renamed"}
    matches = [
        project
        for project in projects
        if (project.get("Title") or project.get("title")) in expected_titles
    ]
    if not matches:
        print(f"SKIP: no project found with title {title!r} or its renamed form")
        return 0

    for project in matches:
        name = project.get("Name") or project.get("name")
        if not name:
            print(f"WARN: matched project omitted Name: {project}")
            continue
        deleted = invoke(
            ["uip", "ixp", "projects", "delete", name, "-y", "--output", "json"]
        )
        if deleted is not None and deleted.returncode == 0:
            print(f"OK: deleted IXP project {name!r}")
        else:
            output = "" if deleted is None else (deleted.stderr or deleted.stdout or "")
            print(f"WARN: could not delete {name!r}: {output[:300]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
