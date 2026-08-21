#!/usr/bin/env python3
"""Fake `uip maestro flow` used by the diagnose_run tests. Prints canned CLI envelopes."""
import json
import os
import sys

argv = sys.argv[1:]
mode = os.environ.get("FAKE_MODE", "ok")
joined = " ".join(argv)

if mode == "fail" and "incidents" in joined:
    sys.stderr.write("boom\n")
    sys.exit(3)

if argv[:2] == ["job", "status"]:
    out = {"Result": "Success", "Data": {"instanceId": "I1", "folderKey": "F1", "state": "Faulted"}}
elif argv[:2] == ["instance", "incidents"]:
    if mode == "empty":
        out = {"Result": "Success", "Data": []}
    else:
        out = {"Result": "Success", "Data": [{"id": "INC1", "elementId": "buildPayload"}]}
elif argv[:2] == ["incident", "get"]:
    out = {"Result": "Success", "Data": {"id": "INC1", "category": "ScriptError",
                                         "message": "Cannot read property 'output' of undefined",
                                         "elementId": "buildPayload"}}
elif argv[:2] == ["instance", "variables"]:
    out = {"Result": "Success", "Data": {"buildPayload.output": None}}
elif argv[:2] == ["instance", "asset"]:
    out = {"Result": "Success", "Data": {"bpmn": "<definitions/>"}}
elif argv[:2] == ["job", "traces"]:
    out = {"Result": "Success", "Data": [{"step": "start"}]}
else:
    sys.stderr.write("unexpected call: %s\n" % joined)
    sys.exit(9)
print(json.dumps(out))
