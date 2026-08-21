import json
import os
import subprocess
import sys
import tempfile

SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def run(script, *args):
    proc = subprocess.run([sys.executable, os.path.join(SCRIPTS, script)] + [str(a) for a in args],
                          capture_output=True, text=True, cwd=SCRIPTS)
    return proc.returncode, proc.stdout + proc.stderr


def workdir():
    return tempfile.mkdtemp(prefix="flowtest-")


def write(path, obj):
    with open(path, "w") as fh:
        if isinstance(obj, str):
            fh.write(obj)
        else:
            json.dump(obj, fh, indent=2)
    return path


def read(path):
    with open(path) as fh:
        return json.load(fh)


def node(nid, ntype, version="1.0", **kw):
    n = {"id": nid, "type": ntype, "typeVersion": version, "display": {"label": nid}, "inputs": {}}
    n.update(kw)
    return n


def edge(src, sp, tgt, tp="input"):
    return {"id": "edge_%s_%s_%s_%s" % (src, sp, tgt, tp),
            "sourceNodeId": src, "sourcePort": sp, "targetNodeId": tgt, "targetPort": tp}


def layout(*ids, **sizes):
    return {"nodes": {i: {"position": {"x": 0, "y": 0},
                          "size": sizes.get(i, {"width": 96, "height": 96}),
                          "collapsed": False} for i in ids}}


def node_vars(*pairs):
    return [{"id": "%s.%s" % (n, o), "type": "object", "binding": {"nodeId": n, "outputId": o}} for n, o in pairs]


def clean_flow():
    """trigger -> script -> end, fully wired, variables and layout consistent."""
    return {
        "id": "11111111-1111-1111-1111-111111111111",
        "nodes": [
            node("start", "core.trigger.manual", inputs={"entryPointId": "22222222-2222-2222-2222-222222222222"},
                 outputs={"output": {"type": "object", "description": "d", "source": "null", "var": "output"}}),
            node("buildPayload", "core.action.script", inputs={"script": "return { total: $vars.start.output.amount };"},
                 outputs={"output": {"type": "object", "description": "d", "source": "=result.response", "var": "output"},
                          "error": {"type": "object", "description": "d", "source": "=Error", "var": "error"}}),
            node("done", "core.control.end", outputs={"total": {"source": "=js:$vars.buildPayload.output.total"}}),
        ],
        "edges": [edge("start", "output", "buildPayload"), edge("buildPayload", "success", "done")],
        "definitions": [
            {"nodeType": "core.trigger.manual", "version": "1.0"},
            {"nodeType": "core.action.script", "version": "1.0"},
            {"nodeType": "core.control.end", "version": "1.0"},
        ],
        "variables": {
            "globals": [{"id": "total", "direction": "out", "type": "number"}],
            "nodes": node_vars(("start", "output"), ("buildPayload", "output"), ("buildPayload", "error")),
        },
        "layout": layout("start", "buildPayload", "done"),
    }


def check(label, cond, detail=""):
    if not cond:
        print("FAIL %s %s" % (label, detail))
        sys.exit(1)
    print("ok   %s" % label)
