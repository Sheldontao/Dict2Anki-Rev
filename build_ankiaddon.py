#!/usr/bin/env python3
"""Package this add-on folder into an AnkiWeb-uploadable .ankiaddon file.

AnkiWeb requires a flat zip: the add-on folder contents at the zip root, with no
top-level folder, no __pycache__, and no .DS_Store.

Usage:
    python3 build_ankiaddon.py            # writes dist/Dict2Anki-Rev-<VERSION>.ankiaddon
    python3 build_ankiaddon.py --out X    # custom output path

What is included:
    __init__.py      add-on entry point
    addon/           all add-on modules
    config.json      defaults; credentials are blanked before packaging
    LICENSE
    README.md
    changelog.md

What is deliberately excluded:
    meta.json        written by Anki itself on install; carries local config + cookies
    tests/ docs/     development only
    ulterior/        saved HTML fixtures used by tests
    AnkiExampleTemplate.apkg, .DS_Store, __pycache__, .venv/, .claude/, .context/
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
INCLUDE_FILES = ["__init__.py", "config.json", "LICENSE", "README.md", "changelog.md"]
INCLUDE_DIRS = ["addon"]
EXCLUDE_NAMES = {".DS_Store", "__pycache__", ".pytest_cache"}
CREDENTIAL_PLACEHOLDER = {"username": "", "password": "", "cookie": ""}


def read_version() -> str:
    """Read VERSION from addon/constants.py without importing aqt."""
    path = os.path.join(ROOT, "addon", "constants.py")
    with open(path, encoding="utf-8") as fh:
        match = re.search(r"^VERSION\s*=\s*['\"]([^'\"]+)['\"]", fh.read(), re.M)
    if not match:
        sys.exit("could not find VERSION in addon/constants.py")
    return match.group(1)


def sanitize_config(raw: dict) -> dict:
    """Strip any locally stored credentials so they never ship to users."""
    out = json.loads(json.dumps(raw))  # deep copy
    if isinstance(out.get("credential"), list):
        out["credential"] = [CREDENTIAL_PLACEHOLDER for _ in out["credential"]]
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", help="output .ankiaddon path")
    args = parser.parse_args()

    version = read_version()
    out_path = args.out or os.path.join(ROOT, "dist", f"Dict2Anki-Rev-{version}.ankiaddon")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    if os.path.exists(out_path):
        os.remove(out_path)

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in INCLUDE_FILES:
            src = os.path.join(ROOT, name)
            if not os.path.exists(src):
                sys.exit(f"missing required file: {name}")
            if name == "config.json":
                with open(src, encoding="utf-8") as fh:
                    data = sanitize_config(json.load(fh))
                zf.writestr(name, json.dumps(data, indent=4, ensure_ascii=False) + "\n")
            else:
                zf.write(src, name)

        for d in INCLUDE_DIRS:
            base = os.path.join(ROOT, d)
            for dirpath, dirnames, filenames in os.walk(base):
                dirnames[:] = [x for x in dirnames if x not in EXCLUDE_NAMES]
                for fn in sorted(filenames):
                    if fn in EXCLUDE_NAMES or fn.endswith(".pyc"):
                        continue
                    full = os.path.join(dirpath, fn)
                    zf.write(full, os.path.relpath(full, ROOT))

    # Report
    print(f"built {out_path} ({os.path.getsize(out_path)} bytes)")
    with zipfile.ZipFile(out_path) as zf:
        bad = [n for n in zf.namelist() if "__pycache__" in n or n.endswith(".DS_Store")
               or n.startswith("meta.json")]
        if bad:
            sys.exit(f"ERROR: package contains rejected entries: {bad}")
        print(f"{len(zf.namelist())} entries")
        for n in sorted(zf.namelist()):
            print("   ", n)


if __name__ == "__main__":
    main()
