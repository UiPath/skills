"""Gate bookkeeping and the shape of the JSON verdict.

The only module that knows the house output format ontology_preflight.py established, so a change
to that contract has exactly one place to happen. GATES order is part of the contract: gate_results
is emitted in it, and every gate appears even when skipped. A skip is never a pass.
"""

from __future__ import annotations


GATES = (
    "ttl-parses-and-well-formed",
    "signature-resolves",
    "input-matches-marker",
    "input-strictness",
    "writes-cover-edits",
    "fields-exist-in-schema",
    "job-language",
    "typecheck",
)


class GateLog:
    def __init__(self) -> None:
        self.entries: dict[str, list[tuple[str, str]]] = {gate: [] for gate in GATES}

    def add(self, gate: str, status: str, diagnostic: str = "") -> None:
        self.entries[gate].append((status, diagnostic))

    def results(self) -> list[dict]:
        results = []
        for gate in GATES:
            entries = self.entries[gate]
            statuses = {status for status, _ in entries}
            if "failed" in statuses:
                status = "failed"
            elif "passed" in statuses:
                status = "passed"
            else:
                status = "skipped"
            diagnostics = [
                detail if entry_status == "failed" else f"skipped: {detail}"
                for entry_status, detail in entries
                if entry_status in ("failed", "skipped") and detail
            ]
            results.append(
                {
                    "id": gate,
                    "status": status,
                    "passed": None if status == "skipped" else status == "passed",
                    "diagnostics": diagnostics,
                }
            )
        return results

    def errors(self) -> dict[str, list[str]]:
        return {
            gate: [detail for status, detail in self.entries[gate] if status == "failed"]
            for gate in GATES
            if any(status == "failed" for status, _ in self.entries[gate])
        }
