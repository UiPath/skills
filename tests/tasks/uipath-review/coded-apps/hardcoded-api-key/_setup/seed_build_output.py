#!/usr/bin/env python3
"""pre_run: create the build output and project metadata of DepotMap.

These paths (`dist/`, `.uipath/`, `package-lock.json`) are ignored by the
repo's .gitignore, so they cannot be checked in as fixture files. Run from the
sandbox root; the task's pre_run removes `_setup/` afterwards so the agent never
sees this script.
"""
import json
from pathlib import Path

APP = Path("DepotMap")
FILES = {
    '.uipath/app.json': '{\n  "name": "DepotMap",\n  "version": "1.2.0",\n  "type": "Coded"\n}\n',
    'package-lock.json': '{\n  "name": "depotmap",\n  "version": "1.2.0",\n  "lockfileVersion": 3,\n  "packages": {}\n}\n',
    'dist/index.html': '<!doctype html>\n<html lang="en">\n  <head><meta charset="utf-8" /><title>DepotMap</title><script type="module" src="/assets/index-4f2a9c.js"></script></head>\n  <body><div id="root"></div></body>\n</html>\n',
    'dist/assets/index-4f2a9c.js': 'console.log("bundle placeholder for the review fixture");\n',
}

for rel, content in FILES.items():
    p = APP / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
print(f"seeded {len(FILES)} files under {APP}/")
