#!/usr/bin/env python3
"""Seed the live name-resolution task without exposing the project Name."""

import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path


def run(command: list[str], timeout: int = 300) -> dict:
    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        output = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(command)}\n"
            f"{output[:1000]}"
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"command returned invalid JSON: {' '.join(command)}\n"
            f"{proc.stdout[:1000]}"
        ) from exc


def main() -> int:
    workspace = Path.cwd()
    fixtures = workspace / "fixtures"
    taxonomy = fixtures / "taxonomy.json"
    if not taxonomy.is_file():
        raise RuntimeError(f"taxonomy fixture not found: {taxonomy}")

    documents = workspace / "invoice_docs"
    documents.mkdir(exist_ok=True)
    invoice_files = sorted(fixtures.glob("*.png"))
    if not invoice_files:
        raise RuntimeError(f"document fixtures not found: {fixtures}")
    for invoice in invoice_files:
        shutil.copy2(invoice, documents / invoice.name)

    title = f"codereval-integ-resolve-{uuid.uuid4().hex[:8]}"
    created = run(
        [
            "uip",
            "ixp",
            "projects",
            "create",
            title,
            str(documents),
            "--skip-taxonomy",
            "--output",
            "json",
        ]
    )
    data = created.get("Data") or created.get("data") or created
    project_name = data.get("ProjectName") or data.get("project_name")
    if not project_name:
        raise RuntimeError(f"create response omitted ProjectName: {created}")

    # Expose only the user-facing title. Cleanup resolves the Name independently,
    # preserving the Title → Name behavior this task evaluates.
    (workspace / "report.json").write_text(
        json.dumps({"project_title": title}),
        encoding="utf-8",
    )

    run(
        [
            "uip",
            "ixp",
            "projects",
            "import-taxonomy",
            project_name,
            str(taxonomy),
            "--output",
            "json",
        ]
    )
    (workspace / "seed.json").write_text(
        json.dumps({"project_title": title}),
        encoding="utf-8",
    )

    # Pre-run setup passes through the transparent logger. Remove those calls
    # so criteria grade only commands issued by the agent.
    (workspace / "mocks" / "calls.log").write_text("", encoding="utf-8")
    print(f"Seeded IXP project titled {title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
