import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _helper import check, clean_flow, run, workdir, write

HERE = os.path.dirname(os.path.abspath(__file__))
FAKE = "%s %s" % (sys.executable, os.path.join(HERE, "fake_uip.py"))
wd = workdir()
flow = write(os.path.join(wd, "P.flow"), clean_flow())
report = os.path.join(wd, "report.json")

rc, out = run("diagnose_run.py", "--dry-run", "--job-key", "JK")
check("dry-run prints the ladder without calling the CLI",
      rc == 0 and "job status JK" in out and "instance incidents" in out, out)

os.environ.pop("FAKE_MODE", None)
rc, out = run("diagnose_run.py", "--job-key", "JK", "--flow", flow, "--cli", FAKE, "--out", report)
check("ladder exits 0", rc == 0, out)
check("resolves instance and folder from job status", "instance: I1" in out and "folder:   F1" in out, out)
check("prints the incident message", "Cannot read property" in out, out)
check("correlates the faulting element to a node",
      "node:     buildPayload (core.action.script)" in out, out)
data = json.load(open(report))
check("ladder order recorded",
      [c.split(" --output")[0].split("fake_uip.py ")[-1] for c in data["cliCalls"]] ==
      ["job status JK", "instance incidents I1 --folder-key F1",
       "incident get INC1 --folder-key F1", "instance variables I1 --folder-key F1"],
      json.dumps(data["cliCalls"], indent=2))
check("report keeps the upstream edges",
      data["correlation"]["upstreamEdges"][0]["from"] == "start", json.dumps(data["correlation"]))
check("report keeps node inputs", "script" in data["correlation"]["inputs"], out)
check("traces are not pulled by default", "job traces" not in " ".join(data["cliCalls"]), out)

rc, out = run("diagnose_run.py", "--job-key", "JK", "--flow", flow, "--cli", FAKE,
              "--out", report, "--traces", "--asset")
data = json.load(open(report))
check("traces and asset are opt-in and appended",
      "job traces" in " ".join(data["cliCalls"]) and "instance asset" in " ".join(data["cliCalls"]), out)

rc, out = run("diagnose_run.py", "--instance-id", "I1", "--folder-key", "F1", "--cli", FAKE)
check("instance id skips step 1", rc == 0 and "job status" not in out, out)

env_note = os.path.join(wd, "empty.json")
os.environ["FAKE_MODE"] = "empty"
rc, out = run("diagnose_run.py", "--instance-id", "I1", "--folder-key", "F1", "--cli", FAKE, "--out", env_note)
check("no incident exits 5", rc == 5 and "incidents: 0" in out, out)
os.environ["FAKE_MODE"] = "fail"
rc, out = run("diagnose_run.py", "--instance-id", "I1", "--folder-key", "F1", "--cli", FAKE)
check("failed CLI call exits 4", rc == 4 and "CLI call failed" in out, out)
os.environ.pop("FAKE_MODE")

rc, out = run("diagnose_run.py", "--cli", FAKE)
check("no job key or instance id fails loudly", rc == 2, out)

unmatched = write(os.path.join(wd, "other.flow"), {"nodes": [{"id": "somethingElse", "type": "core.action.script"}],
                                                  "edges": []})
rc, out = run("diagnose_run.py", "--instance-id", "I1", "--folder-key", "F1", "--cli", FAKE, "--flow", unmatched)
check("unmatched element says the deployed BPMN may differ", "deployed BPMN may differ" in out, out)
print("diagnose_run: all cases passed")
