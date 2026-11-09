#!/usr/bin/env python3
"""
smoke_test_snippets.py - Automated smoke test verifying that cherri code snippets
in documentation compile cleanly with Cherri v2.0 compiler.
"""
import os
import re
import sys
import tempfile
import subprocess

CHERRI_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "cherri"))

def check_snippet(snippet):
    with tempfile.NamedTemporaryFile("w", suffix=".cherri", delete=False, encoding="utf-8") as f:
        f.write(snippet)
        temp_name = f.name
    try:
        cmd = ["go", "run", ".", f"--check={temp_name}"]
        proc = subprocess.run(cmd, cwd=CHERRI_DIR, capture_output=True, text=True)
        if proc.returncode != 0:
            return False, f"STDERR:\n{proc.stderr}\nSTDOUT:\n{proc.stdout}"
        return True, proc.stdout.strip()
    finally:
        if os.path.exists(temp_name):
            os.remove(temp_name)

def test_file(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Match ```cherri\n...\n``` blocks
    pattern = re.compile(r"```cherri\r?\n(.*?)```", re.DOTALL)
    blocks = pattern.findall(content)
    print(f"Testing {len(blocks)} cherri code blocks in {md_path}...")
    
    passed = 0
    failed = 0
    for idx, block in enumerate(blocks):
        stripped = block.strip()
        if not stripped or stripped.startswith("// ..."):
            continue
        ok, msg = check_snippet(block)
        if ok:
            passed += 1
            print(f"  [PASS] Block {idx+1}")
        else:
            failed += 1
            print(f"  [FAIL] Block {idx+1}:\n{msg}")
            print(f"  Code:\n{block}\n")
    print(f"Summary for {os.path.basename(md_path)}: {passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "language", "functions.md")
    ok = test_file(os.path.abspath(target))
    sys.exit(0 if ok else 1)
