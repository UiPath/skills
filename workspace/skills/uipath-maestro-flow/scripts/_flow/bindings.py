"""Audit (and optionally emit) the top-level `bindings[]` pairs that uipath.core.* resource nodes need.

For every resource node the script reads its definition's model.bindings.resourceKey /
resourceSubType and the <bindings.NAME> placeholders in model.context[], then checks the flow's
top-level bindings[] for a matching (resourceKey, name) entry. Missing entries pass
`uip maestro flow validate` and fail at debug with "Folder does not exist...".
"""
import json
import re

from . import lib as fl

PLACEHOLDER = re.compile(r"^<bindings\.(.+)>$")
SAFE = re.compile(r"[^A-Za-z0-9]+")


def _model_bindings(definition):
    return ((definition or {}).get("model") or {}).get("bindings") or {}


def _needed_names(definition):
    ctx = ((definition or {}).get("model") or {}).get("context") or []
    names = []
    for entry in ctx if isinstance(ctx, list) else []:
        value = (entry or {}).get("value") if isinstance(entry, dict) else None
        if isinstance(value, str):
            m = PLACEHOLDER.match(value)
            if m:
                names.append(m.group(1))
    return sorted(set(names))


def _entry_id(resource_key, name):
    return "b" + SAFE.sub("_", "%s_%s" % (resource_key, name)).strip("_")


def collect(flow):
    out, missing = [], []
    present = {}
    for b in flow.get("bindings") or []:
        if isinstance(b, dict):
            key = (b.get("resourceKey"), b.get("name"))
            present.setdefault(key, []).append(b.get("id"))
    for key, ids in sorted(present.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
        if len(ids) > 1:
            out.append(fl.finding("warning", "DUPLICATE_BINDING",
                                  "%d entries share (resourceKey=%s, name=%s); share one instead"
                                  % (len(ids), key[0], key[1]), path="bindings"))

    needed = set()
    for node in flow["nodes"]:
        ntype = node.get("type", "")
        nid = node.get("id")
        if not fl.is_resource_node(ntype):
            continue
        definition = fl.definition_for(flow, node)
        if definition is None:
            out.append(fl.finding("error", "NO_DEFINITION",
                                  "no definitions[] entry for %s; copy it from `registry get`" % ntype, node=nid))
            continue
        mb = _model_bindings(definition)
        resource_key = mb.get("resourceKey")
        names = _needed_names(definition) or ["name", "folderPath"]
        if not resource_key:
            out.append(fl.finding("warning", "NO_RESOURCE_KEY",
                                  "definition has no model.bindings.resourceKey; cannot match binding entries", node=nid))
            continue
        for name in names:
            needed.add((resource_key, name))
            if (resource_key, name) in present:
                continue
            out.append(fl.finding("error", "MISSING_BINDING",
                                  "no bindings[] entry for (resourceKey=%s, name=%s); validate passes, debug fails "
                                  "with \"Folder does not exist or the user does not have access to the folder\""
                                  % (resource_key, name), node=nid))
            entry = {
                "id": _entry_id(resource_key, name),
                "name": name,
                "type": "string",
                "resourceKey": resource_key,
            }
            if mb.get("resource"):
                entry["resource"] = mb["resource"]
            default = None
            if name == "name":
                default = resource_key.rsplit(".", 1)[-1]
            elif name == "folderPath":
                default = resource_key.rsplit(".", 1)[0] if "." in resource_key else None
            if default is not None:
                entry["default"] = default
            entry["propertyAttribute"] = name
            if mb.get("resourceSubType"):
                entry["resourceSubType"] = mb["resourceSubType"]
            if entry not in missing:
                missing.append(entry)
    for key in sorted(present, key=lambda k: (str(k[0]), str(k[1]))):
        if key not in needed and key[0] is not None:
            out.append(fl.finding("info", "UNUSED_BINDING",
                                  "no resource node needs (resourceKey=%s, name=%s)" % key, path="bindings"))
    return out, missing

