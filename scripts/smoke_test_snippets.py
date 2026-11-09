#!/usr/bin/env python3
"""
smoke_test_snippets.py - Standalone automated smoke test verifying that Cherri v2
documentation code snippets compile cleanly against a pinned Cherri compiler commit.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

PINNED_CHERRI_REPO = "https://github.com/davidpovarsky/cherri.git"
PINNED_CHERRI_COMMIT = "4f4d30f1b863e8d53cd3d56eb8ddcaffab7ce8f2"


def ensure_pinned_cherri_binary() -> str:
    """
    Clones/fetches PINNED_CHERRI_REPO at PINNED_CHERRI_COMMIT into an isolated
    cache directory, verifies the exact commit SHA, builds the compiler binary,
    and returns the binary path. Independent of any relative local sibling directory.
    """
    exe_ext = ".exe" if os.name == "nt" else ""
    cache_root = os.environ.get(
        "CHERRI_SMOKE_CACHE_DIR",
        os.path.join(tempfile.gettempdir(), f"cherri-docs-smoke-{PINNED_CHERRI_COMMIT[:12]}"),
    )
    repo_dir = os.path.join(cache_root, "src")
    bin_path = os.path.join(cache_root, f"cherri{exe_ext}")

    if os.path.isfile(bin_path) and os.path.isdir(os.path.join(repo_dir, ".git")):
        rev = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
        )
        if rev.returncode == 0 and rev.stdout.strip() == PINNED_CHERRI_COMMIT:
            return bin_path

    if os.path.exists(cache_root):
        shutil.rmtree(cache_root, ignore_errors=True)
    os.makedirs(repo_dir, exist_ok=True)

    print(f"Fetching pinned Cherri compiler ({PINNED_CHERRI_COMMIT}) from {PINNED_CHERRI_REPO}...")
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", PINNED_CHERRI_REPO],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "fetch", "--depth", "1", "origin", PINNED_CHERRI_COMMIT],
        cwd=repo_dir,
        check=True,
    )
    subprocess.run(
        ["git", "checkout", "--detach", "FETCH_HEAD"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )

    actual_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if actual_sha != PINNED_CHERRI_COMMIT:
        raise RuntimeError(
            f"Pinned commit verification failed: expected {PINNED_CHERRI_COMMIT}, got {actual_sha}"
        )

    print(f"Building pinned Cherri compiler binary at {bin_path}...")
    subprocess.run(
        ["go", "build", "-o", bin_path, "."],
        cwd=repo_dir,
        check=True,
    )
    return bin_path


def check_snippet(cherri_bin: str, snippet: str) -> tuple[bool, str]:
    work_dir = tempfile.mkdtemp(prefix="cherri_doc_snip_")
    src_path = os.path.join(work_dir, "snippet.cherri")
    try:
        with open(src_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(snippet + "\n")

        # 1. Static check (--check)
        proc_check = subprocess.run(
            [cherri_bin, f"--check={src_path}", "--no-ansi"],
            cwd=work_dir,
            capture_output=True,
            text=True,
        )
        if proc_check.returncode != 0:
            return (
                False,
                f"--check failed (exit {proc_check.returncode}):\nSTDERR:\n{proc_check.stderr}\nSTDOUT:\n{proc_check.stdout}",
            )

        # 2. Full unsigned compilation (--skip-sign)
        proc_compile = subprocess.run(
            [cherri_bin, src_path, "--skip-sign", "--no-ansi"],
            cwd=work_dir,
            capture_output=True,
            text=True,
        )
        if proc_compile.returncode != 0:
            return (
                False,
                f"compile failed (exit {proc_compile.returncode}):\nSTDERR:\n{proc_compile.stderr}\nSTDOUT:\n{proc_compile.stdout}",
            )

        unsigned_path = os.path.join(work_dir, "snippet_unsigned.shortcut")
        if not os.path.isfile(unsigned_path) or os.path.getsize(unsigned_path) == 0:
            return False, "expected non-empty snippet_unsigned.shortcut was not produced"

        return True, "OK"
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def verify_no_legacy_syntax(md_path: str, block_idx: int, block: str) -> tuple[bool, str]:
    """Ensures no legacy @var, @result, or legacy typed parameter syntax remains in V2 docs."""
    if re.search(r"(?<![a-zA-Z0-9._])@[a-zA-Z_][a-zA-Z0-9_]*", block):
        return False, f"Block {block_idx} in {md_path} still contains legacy '@variable' syntax"
    if re.search(r"\bfunction\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(\s*(text|number|array|dictionary|boolean|variable)\s+[a-zA-Z_]", block):
        return False, f"Block {block_idx} in {md_path} still contains legacy C-style parameter type syntax"
    return True, "OK"


def test_file(cherri_bin: str, md_path: str) -> bool:
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(r"```cherri\r?\n(.*?)```", re.DOTALL)
    blocks = pattern.findall(content)
    print(f"Testing {len(blocks)} cherri code blocks in {os.path.basename(md_path)} (pinned commit {PINNED_CHERRI_COMMIT[:12]})...")

    passed = 0
    failed = 0
    for idx, block in enumerate(blocks, start=1):
        stripped = block.strip()
        if not stripped or stripped.startswith("// ..."):
            continue

        syntax_ok, syntax_msg = verify_no_legacy_syntax(md_path, idx, stripped)
        if not syntax_ok:
            failed += 1
            print(f"  [FAIL] Block {idx}: {syntax_msg}")
            continue

        ok, msg = check_snippet(cherri_bin, stripped)
        if ok:
            passed += 1
            print(f"  [PASS] Block {idx}")
        else:
            failed += 1
            print(f"  [FAIL] Block {idx}:\n{msg}\n  Code:\n{stripped}\n")

    print(f"Summary for {os.path.basename(md_path)}: {passed} passed, {failed} failed")
    return failed == 0 and passed > 0


def main() -> int:
    cherri_bin = ensure_pinned_cherri_binary()

    # Negative self-check: verify an invalid snippet fails compilation as expected
    bad_ok, _ = check_snippet(cherri_bin, "fn broken(a: ) { return }")
    if bad_ok:
        print("FATAL: negative self-check unexpectedly passed on invalid Cherri syntax")
        return 1

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    targets = sys.argv[1:] if len(sys.argv) > 1 else [
        os.path.join(repo_root, "language", "functions.md"),
        os.path.join(repo_root, "language", "variables-constants-globals.md"),
    ]

    all_ok = True
    for target in targets:
        if not test_file(cherri_bin, os.path.abspath(target)):
            all_ok = False

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
