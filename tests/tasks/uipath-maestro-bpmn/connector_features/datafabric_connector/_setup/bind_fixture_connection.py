#!/usr/bin/env python3
"""Point a fixture project at this tenant's Data Fabric connection and folder entity.

    bind_fixture_connection.py <dir>

A fixture carries placeholders instead of tenant ids, since a solution saved on
one tenant names connections and entities another tenant does not have:

    __DF_CONNECTION_ID__   a live uipath-uipath-dataservice connection (pinged)
    __DF_FOLDER_KEY__      that connection's folder key
    __DF_FOLDER_PATH__     that connection's folder, XML-escaped (fixtures use it in .bpmn attributes)
    __ENTITY_NAME__        the entity `_setup/ensure_folder_entity.py` recorded
    __ENTITY_KEY__         its key
    __ENTITY_FOLDER_KEY__  its folder key

Every file under <dir> is rewritten in place. Run it after ensure_folder_entity.py.
"""
import json
import os
import sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preflight_connections import _connections, _first_live  # noqa: E402


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    root = sys.argv[1]
    connection, refused = _first_live(_connections("uipath-uipath-dataservice"))
    if connection is None:
        sys.exit(f"FAIL: no live uipath-uipath-dataservice connection: {refused}")
    with open(os.path.join("_setup", "picker_entity.json")) as f:
        entity = json.load(f)
    values = {
        "__DF_CONNECTION_ID__": str(connection["Id"]),
        "__DF_FOLDER_KEY__": str(connection.get("FolderKey") or ""),
        "__DF_FOLDER_PATH__": escape(str(connection.get("Folder") or ""), {'"': "&quot;"}),
        "__ENTITY_NAME__": entity["name"],
        "__ENTITY_KEY__": entity["key"],
        "__ENTITY_FOLDER_KEY__": entity["folderKey"],
    }
    changed = 0
    for dirpath, _, names in os.walk(root):
        for name in names:
            path = os.path.join(dirpath, name)
            with open(path) as f:
                text = f.read()
            new = text
            for placeholder, value in values.items():
                new = new.replace(placeholder, value)
            if new != text:
                with open(path, "w") as f:
                    f.write(new)
                changed += 1
    print(f"OK: bound {changed} fixture file(s) to connection {connection['Id']} and entity {entity['name']}")


if __name__ == "__main__":
    main()
