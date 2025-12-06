#!/usr/bin/env python3
"""
Scan files under app/ for uses of `get_db_connection` and add an import line
if it's missing:

    from app.core.firestore_db import get_db_connection

It attempts to insert the import after the initial block of imports / docstring.
It will not duplicate the import if an equivalent import already exists.

Run:
    python3 scripts/fix_get_db_imports.py
"""

import io
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
IMPORT_LINE = "from app.core.firestore_db import get_db_connection\n"

py_files = list(APP_DIR.rglob("*.py"))

def has_equivalent_import(text):
    # accept a few variants to avoid duplicates
    patterns = [
        r"from\s+app\.core\.firestore_db\s+import\s+get_db_connection\b",
        r"from\s+core\.firestore_db\s+import\s+get_db_connection\b",
        r"from\s+app\.core\.firestore_db\s+import\s+\*",
        r"get_db_connection\s*=\s*",
    ]
    for p in patterns:
        if re.search(p, text):
            return True
    return False

def find_insert_index(lines):
    """
    Find index after the initial block of comments/docstring and imports
    where we should insert an import.
    """
    i = 0
    n = len(lines)
    # skip shebang and encoding comments
    while i < n and (lines[i].startswith("#!") or re.match(r"#\s*-*\s*coding", lines[i])):
        i += 1
    # skip module docstring
    if i < n and re.match(r'\s*(?:\"\"\"|\'\'\')', lines[i]):
        quote = re.match(r'\s*(\"\"\"|\'\'\')', lines[i]).group(1)
        i += 1
        while i < n and quote not in lines[i]:
            i += 1
        # skip closing docstring line
        if i < n:
            i += 1
    # now skip any leading imports and blank lines
    while i < n and (re.match(r"\s*(import|from)\s+", lines[i]) or lines[i].strip() == ""):
        i += 1
    # insert just before the first non-import / non-blank line
    return i

def process_file(path: Path):
    text = path.read_text(encoding="utf-8")
    if "get_db_connection" not in text:
        return False, "no usage"
    if has_equivalent_import(text):
        return False, "already imported"
    lines = text.splitlines(keepends=True)
    idx = find_insert_index(lines)
    # if file is empty or only imports, append import at the end
    if idx is None:
        idx = 0
    # Insert import with a blank line after it for readability
    new_lines = lines[:idx] + [IMPORT_LINE, "\n"] + lines[idx:]
    path.write_text("".join(new_lines), encoding="utf-8")
    return True, "import added"

def main():
    fixed = []
    skipped = []
    for f in py_files:
        changed, reason = process_file(f)
        if changed:
            fixed.append(str(f.relative_to(ROOT)))
        else:
            skipped.append((str(f.relative_to(ROOT)), reason))

    print("=== Auto-inserted get_db_connection imports ===")
    if fixed:
        for p in fixed:
            print(" +", p)
    else:
        print(" (none)")

    print("\n=== Skipped files (reason) ===")
    for p, r in skipped:
        print(" -", p, ":", r)

    print("\nNext manual steps (from your flake8 output):")
    print(" - Open app/core/firestore_db.py and move module-level imports to the top of the file (E402).")
    print(" - Remove unused imports / variables (F401 / F841). You can run autoflake to help remove unused imports:")
    print("     pip install autoflake")
    print("     autoflake --remove-all-unused-imports --in-place -r app/")
    print(" - Fix the F541 missing-placeholder f-string in app/routers/demo.py at the indicated line (remove the leading 'f' if there are no placeholders).")
    print(" - Add missing imports (e.g., timedelta) where reported (e.g., from datetime import timedelta).")
    print(" - Remove trailing whitespace and blank-line whitespace (W291 / W293). Tools like ruff/black can help.")
    print("\nAfter making changes, re-run:")
    print("    flake8 app/ --max-line-length=100 --ignore=E203,W503 --count")
    print("If you want, I can generate a PR with these automated import insertions — tell me and I'll create one.")

if __name__ == "__main__":
    main()