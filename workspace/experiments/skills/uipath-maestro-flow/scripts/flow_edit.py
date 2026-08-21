#!/usr/bin/env python3
"""Apply `.flow` mutations. One plan file per call is the intended path.

    flow_edit.py apply --flow <F> --plan <plan.json>

The plan is an ordered `{"ops": [...]}` list; every op is applied in memory and the file is
written once, so N nodes/edges/variables cost one call instead of N. Nothing is written unless
every op succeeds. `flow_edit.py plan-schema` prints the op vocabulary.

Single-op subcommands (add-node, add-edge, …) exist for a one-off tweak; they build a one-op plan
and go through the same applier. Prefer `apply` whenever you have more than one change to make.

Layout values stay placeholders — `uip maestro flow format` still owns final layout.
CLI-owned node types (connector, connector trigger, wait-for-event, managed HTTP) are refused:
use `uip maestro flow node add` + `uip maestro flow node configure`.
"""
import argparse
import json
import sys

from _flow import lib as fl
from _flow import plan as P
from _flow import agent_inputs as AI


def _run(args, ops, base_dir="."):
    flow = fl.load(args.flow)
    log = P.apply_ops(flow, ops, base_dir)
    if getattr(args, "dry_run", False):
        print("dry run — %d op(s) would apply, nothing written:" % len(ops))
        for line in log:
            print("  " + line)
        return 0
    fl.save(args.flow, flow)
    for line in log:
        print(line)
    print("applied %d op(s) to %s" % (len(ops), args.flow))
    return 0


def cmd_apply(args):
    import os
    ops = P.load_plan(args.plan)
    return _run(args, ops, os.path.dirname(os.path.abspath(args.plan)))


def cmd_plan_schema(args):
    print(P.__doc__.strip())
    return 0


def _one(args, op):
    return _run(args, [op])


def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("apply", help="apply an ordered op plan in one call (preferred)")
    a.add_argument("--flow", required=True)
    a.add_argument("--plan", required=True, help='JSON file: {"ops": [ ... ]} — see `plan-schema`')
    a.add_argument("--dry-run", action="store_true", help="report what would apply, write nothing")
    a.set_defaults(fn=cmd_apply)

    s = sub.add_parser("plan-schema", help="print the op vocabulary accepted by --plan")
    s.set_defaults(fn=cmd_plan_schema)

    def flow_arg(sp):
        sp.add_argument("--flow", required=True)
        sp.add_argument("--dry-run", action="store_true")

    n = sub.add_parser("add-node", help="fallback: single node (+definition, variables.nodes, layout)")
    flow_arg(n)
    n.add_argument("--id", required=True)
    n.add_argument("--type", required=True)
    n.add_argument("--type-version")
    n.add_argument("--label")
    n.add_argument("--definition-file", help="`uip maestro flow registry get <type> --output json` saved to a file")
    n.add_argument("--inputs", help="JSON object")
    n.add_argument("--outputs", default="auto", help="auto | none | comma-separated output ids")
    n.add_argument("--allow-cli-owned", action="store_true")
    n.set_defaults(fn=lambda a: _one(a, {"op": "add-node", "id": a.id, "type": a.type,
                                         "typeVersion": a.type_version, "label": a.label,
                                         "definitionFile": a.definition_file,
                                         "inputs": json.loads(a.inputs) if a.inputs else {},
                                         "outputs": a.outputs, "allowCliOwned": a.allow_cli_owned}))

    d = sub.add_parser("delete-node", help="fallback: remove a node and cascade edges/variables/updates/layout/definition")
    flow_arg(d)
    d.add_argument("--id", required=True)
    d.set_defaults(fn=lambda a: _one(a, {"op": "delete-node", "id": a.id}))

    e = sub.add_parser("add-edge", help="fallback: single edge (both ports required)")
    flow_arg(e)
    e.add_argument("--source", required=True)
    e.add_argument("--source-port", required=True)
    e.add_argument("--target", required=True)
    e.add_argument("--target-port", required=True)
    e.add_argument("--id")
    e.set_defaults(fn=lambda a: _one(a, {"op": "add-edge", "source": a.source, "sourcePort": a.source_port,
                                         "target": a.target, "targetPort": a.target_port, "id": a.id}))

    x = sub.add_parser("delete-edge", help="fallback: remove an edge by id or endpoints")
    flow_arg(x)
    x.add_argument("--id")
    x.add_argument("--source")
    x.add_argument("--source-port")
    x.add_argument("--target")
    x.set_defaults(fn=lambda a: _one(a, {"op": "delete-edge", "id": a.id, "source": a.source,
                                         "sourcePort": a.source_port, "target": a.target}))

    i = sub.add_parser("set-input", help="fallback: in-place inputs update (dotted key path)")
    flow_arg(i)
    i.add_argument("--node", required=True)
    i.add_argument("--key", required=True)
    i.add_argument("--value", required=True)
    i.add_argument("--json", action="store_true", help="parse --value as JSON")
    i.add_argument("--allow-cli-owned", action="store_true")
    i.set_defaults(fn=lambda a: _one(a, {"op": "set-input", "node": a.node, "key": a.key,
                                         "value": json.loads(a.value) if a.json else a.value,
                                         "allowCliOwned": a.allow_cli_owned}))

    v = sub.add_parser("add-variable", help="fallback: declare a workflow variable")
    flow_arg(v)
    v.add_argument("--id", required=True)
    v.add_argument("--direction", required=True, choices=["in", "out", "inout"])
    v.add_argument("--type", default="string", choices=["string", "number", "boolean", "object", "array", "file"])
    v.add_argument("--sub-type")
    v.add_argument("--default", help="JSON literal")
    v.add_argument("--description")
    v.add_argument("--trigger-node-id")
    v.set_defaults(fn=lambda a: _one(a, {"op": "add-variable", "id": a.id, "direction": a.direction,
                                         "type": a.type, "subType": a.sub_type,
                                         "default": json.loads(a.default) if a.default else None,
                                         "description": a.description, "triggerNodeId": a.trigger_node_id}))

    o = sub.add_parser("add-output-mapping", help="fallback: map an out variable on an End/terminate node")
    flow_arg(o)
    o.add_argument("--end-node", required=True)
    o.add_argument("--var", required=True)
    o.add_argument("--source", required=True)
    o.set_defaults(fn=lambda a: _one(a, {"op": "add-output-mapping", "endNode": a.end_node,
                                         "var": a.var, "source": a.source}))

    u = sub.add_parser("add-variable-update", help="fallback: variableUpdates entry for an inout variable")
    flow_arg(u)
    u.add_argument("--node", required=True)
    u.add_argument("--variable", required=True)
    u.add_argument("--expression", required=True)
    u.set_defaults(fn=lambda a: _one(a, {"op": "add-variable-update", "node": a.node,
                                         "variable": a.variable, "expression": a.expression}))

    ag = sub.add_parser("agent-inputs", help="inline-agent input wiring: emit the three artifacts, or check alignment")
    agsub = ag.add_subparsers(dest="mode", required=True)
    em = agsub.add_parser("emit", help="print agentInputVariables[] + inputSchema + prompt tokens")
    em.add_argument("--source", action="append", required=True,
                    help="$vars.<node>.output[.<field>][:type] (repeatable)")
    em.set_defaults(fn=AI.cmd_emit)
    ck = agsub.add_parser("check", help="three-way alignment check across the flow and agent.json")
    ck.add_argument("--flow", required=True)
    ck.add_argument("--agent-json", required=True)
    ck.add_argument("--node")
    ck.add_argument("--format", choices=["text", "json"], default="text")
    ck.set_defaults(fn=AI.cmd_check)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
