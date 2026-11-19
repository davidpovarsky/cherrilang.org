#!/usr/bin/env python3
"""Compile the active V2 documentation with its immutable compiler pin.

Generated action signatures and explicitly labelled historical fragments are
reference notation. Every runnable cherri fence is checked and compiled; an
invalid example must declare and emit its exact error-code sequence.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile

PINNED_CHERRI_REPO = "https://github.com/davidpovarsky/cherri.git"
PINNED_CHERRI_COMMIT = "7b0100a2a9ce5991ca8ffe82c805278e5aa7754e"
CACHE_RECEIPT = "compiler-receipt.json"
FENCES = re.compile(r"^```(?P<kind>cherri(?:-[a-z]+)?)\s*\r?\n(?P<code>.*?)^```\s*$", re.MULTILINE | re.DOTALL)
EXPECTATION = re.compile(r"<!--\s*cherri-test:\s*(.*?)\s*-->\s*$")
REPO_ROOT = Path(__file__).resolve().parent.parent


def command(args, *, cwd=None, check=True):
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=180)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def real_path(path):
    return not path.is_symlink() and not getattr(path, "is_junction", lambda: False)()


def inspect_cache(root, *, receipt_required=True):
    """Read-only validation; never run the cached compiler before provenance."""
    repo = root / "src"
    binary = root / ("cherri.exe" if os.name == "nt" else "cherri")
    paths = (root, repo, repo / ".git", binary, root / CACHE_RECEIPT)
    if any(not real_path(p) for p in paths):
        raise RuntimeError("Compiler cache contains a symbolic link/junction; preserved unchanged.")
    if not binary.is_file() or not (repo / ".git").is_dir():
        raise RuntimeError("Compiler cache is incomplete or unmanaged; preserved unchanged.")
    revision = command(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    if revision != PINNED_CHERRI_COMMIT:
        raise RuntimeError("Compiler cache source commit differs from its immutable pin; preserved unchanged.")
    dirty = command(["git", "status", "--porcelain", "--untracked-files=all", "--ignored=matching"], cwd=repo).stdout
    if dirty.strip():
        raise RuntimeError("Compiler cache source has local/ignored changes; preserved unchanged.")
    origin = command(["git", "remote", "get-url", "origin"], cwd=repo).stdout.strip()
    if origin != PINNED_CHERRI_REPO:
        raise RuntimeError("Compiler cache source origin differs from the pinned repository; preserved unchanged.")
    metadata = command(["go", "version", "-m", str(binary)]).stdout
    if not re.search(r"\bbuild\s+vcs.revision=" + re.escape(PINNED_CHERRI_COMMIT) + r"\s*$", metadata, re.MULTILINE):
        raise RuntimeError("Compiler cache binary VCS revision does not match the source pin; preserved unchanged.")
    if not re.search(r"\bbuild\s+vcs.modified=false\s*$", metadata, re.MULTILINE):
        raise RuntimeError("Compiler cache binary lacks a clean VCS build receipt; preserved unchanged.")
    expected = {
        "formatVersion": 1,
        "compilerRepository": PINNED_CHERRI_REPO,
        "compilerCommit": revision,
        "binarySha256": digest(binary),
        "vcsModified": False,
    }
    if receipt_required:
        try:
            receipt = json.loads((root / CACHE_RECEIPT).read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise RuntimeError("Compiler cache receipt is missing or invalid; preserved unchanged. Choose a new cache directory.") from error
        if receipt != expected:
            raise RuntimeError("Compiler cache receipt/digest differs from the binary; preserved unchanged.")
    return binary, expected


def ensure_pinned_cherri_binary() -> str:
    """Build in an owned sibling stage; never erase/repair an occupied cache."""
    if not re.fullmatch(r"[0-9a-f]{40}", PINNED_CHERRI_COMMIT):
        raise RuntimeError("The compiler pin must be a complete immutable Git commit.")
    root = Path(os.environ.get("CHERRI_SMOKE_CACHE_DIR",
                str(Path(tempfile.gettempdir()) / f"cherri-docs-smoke-v2-{PINNED_CHERRI_COMMIT[:12]}"))).absolute()
    if root.exists() or root.is_symlink():
        return str(inspect_cache(root)[0])
    root.parent.mkdir(parents=True, exist_ok=True)
    # Only this unique, newly created directory is eligible for automatic cleanup.
    with tempfile.TemporaryDirectory(prefix=root.name + ".stage-", dir=root.parent) as scratch:
        stage = Path(scratch)
        repo = stage / "src"
        repo.mkdir()
        print(f"Fetching pinned Cherri compiler ({PINNED_CHERRI_COMMIT}) from {PINNED_CHERRI_REPO}...")
        command(["git", "init"], cwd=repo)
        command(["git", "config", "core.autocrlf", "false"], cwd=repo)
        command(["git", "remote", "add", "origin", PINNED_CHERRI_REPO], cwd=repo)
        command(["git", "fetch", "--depth", "1", "origin", PINNED_CHERRI_COMMIT], cwd=repo)
        command(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=repo)
        binary = stage / ("cherri.exe" if os.name == "nt" else "cherri")
        print(f"Building and verifying pinned compiler {PINNED_CHERRI_COMMIT}...")
        command(["go", "build", "-buildvcs=true", "-trimpath", "-o", str(binary), "."], cwd=repo)
        _, receipt = inspect_cache(stage, receipt_required=False)
        (stage / CACHE_RECEIPT).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        inspect_cache(stage)
        # Exclusive reservation also protects an empty directory created by another
        # process. A partial interrupted promotion is rejected, never overwritten.
        try:
            root.mkdir()
        except FileExistsError as error:
            raise RuntimeError("Compiler cache was created concurrently; preserved unchanged.") from error
        for name in ("src", binary.name, CACHE_RECEIPT):
            os.rename(stage / name, root / name)
    return str(inspect_cache(root)[0])


def check_example(cherri_bin, snippet, expected_errors=()):
    with tempfile.TemporaryDirectory(prefix="cherri_doc_snip_") as work:
        work = Path(work)
        source = work / "snippet.cherri"
        source.write_text(snippet + "\n", encoding="utf-8", newline="\n")
        record = {"sourceSha256": digest(source), "expectedErrors": list(expected_errors)}
        checked = command([cherri_bin, "check", str(source), "--json", "--no-ansi"], cwd=work, check=False)
        try:
            diagnostics = json.loads(checked.stdout)
        except ValueError:
            return False, "check did not emit structured diagnostics", record
        errors = [d.get("code") for d in (diagnostics.get("diagnostics") or []) if d.get("severity") == "ERROR"]
        record.update(checkExit=checked.returncode, actualErrors=errors,
                      schemaFingerprint=diagnostics.get("schemaFingerprint"))
        if expected_errors:
            if checked.returncode == 0 or diagnostics.get("valid") is not False or errors != list(expected_errors):
                return False, f"expected exact errors {list(expected_errors)}, got {errors} (exit {checked.returncode})", record
        elif checked.returncode != 0 or diagnostics.get("valid") is not True or errors:
            return False, f"check failed: {checked.stdout}\n{checked.stderr}", record
        compiled = command([cherri_bin, str(source), "--skip-sign", "--no-ansi"], cwd=work, check=False)
        output = work / "snippet_unsigned.shortcut"
        record["compileExit"] = compiled.returncode
        if expected_errors:
            if compiled.returncode == 0 or output.exists():
                return False, "deliberately invalid source compiled or emitted an unsigned artifact", record
            return True, "exact diagnostic and compile rejection", record
        if compiled.returncode != 0:
            return False, f"compile failed (exit {compiled.returncode}):\n{compiled.stdout}\n{compiled.stderr}", record
        try:
            document = plistlib.loads(output.read_bytes())
        except (OSError, ValueError, plistlib.InvalidFileException) as error:
            return False, f"unsigned output is not a decodable plist: {error}", record
        if not isinstance(document, dict) or not isinstance(document.get("WFWorkflowActions"), list):
            return False, "unsigned output has no native workflow action array", record
        record.update(unsignedSha256=digest(output), actionCount=len(document["WFWorkflowActions"]))
        return True, "checked and compiled to a native workflow plist", record


def check_snippet(cherri_bin: str, snippet: str) -> tuple[bool, str]:
    passed, detail, _ = check_example(cherri_bin, snippet)
    return passed, detail


def verify_no_legacy_syntax(md_path: str, block_idx: int, block: str) -> tuple[bool, str]:
    if re.search(r"(?<![a-zA-Z0-9._])@[a-zA-Z_][a-zA-Z0-9_]*", block):
        return False, f"Block {block_idx} in {md_path} still contains legacy '@variable' syntax"
    if re.search(r"\bfunction\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(\s*(text|number|array|dictionary|boolean|variable)\s+[a-zA-Z_]", block):
        return False, f"Block {block_idx} in {md_path} still contains legacy C-style parameter type syntax"
    return True, "OK"


def test_file(cherri_bin: str, md_path: str, records=None) -> bool:
    records = records if records is not None else []
    path = Path(md_path)
    content = path.read_text(encoding="utf-8")
    blocks = list(FENCES.finditer(content))
    generated = path.name == "actions.md" and path.parent.name == "fork-language"
    if generated and "generated automatically from the canonical Cherri v2 ActionSchema registry" not in content:
        raise RuntimeError("Generated reference is missing its explicit canonical-generation identity.")
    passed = failed = references = 0
    print(f"Testing {len(blocks)} classified Cherri blocks in {path.name} (compiler {PINNED_CHERRI_COMMIT[:12]})...")
    for index, match in enumerate(blocks, 1):
        kind, code = match["kind"], match["code"].strip()
        if not code:
            raise RuntimeError(f"{path}:{index}: empty Cherri block has no testable meaning")
        if generated or kind in ("cherri-legacy", "cherri-fragment"):
            records.append({"file":str(path), "block":index, "classification":"generated-signature" if generated else kind,
                            "sourceSha256":hashlib.sha256(code.encode()).hexdigest(), "executed":False})
            references += 1
            continue
        if kind != "cherri":
            raise RuntimeError(f"{path}:{index}: unknown Cherri block classification {kind}")
        annotation = EXPECTATION.search(content[:match.start()])
        expected = []
        if annotation:
            fields = annotation[1].split()
            if len(fields) < 2 or fields[0] != "diagnostic" or any(not re.fullmatch(r"E_[A-Z0-9_]+", x) for x in fields[1:]):
                raise RuntimeError(f"{path}:{index}: invalid diagnostic annotation {annotation[1]!r}")
            expected = fields[1:]
        # Deliberate legacy diagnostics are executed, rather than hidden by lint.
        ok, detail, record = check_example(cherri_bin, code, expected)
        record.update(file=str(path), block=index, classification="diagnostic" if expected else "runnable", executed=True, passed=ok)
        records.append(record)
        if ok:
            passed += 1
            print(f"  [PASS] Block {index}: {detail}")
        else:
            failed += 1
            print(f"  [FAIL] Block {index}: {detail}\nCode:\n{code}")
    print(f"Summary for {path.name}: {passed} passed, {failed} failed, {references} reference-only")
    return failed == 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-out", type=Path)
    parser.add_argument("files", nargs="*", type=Path)
    args = parser.parse_args()
    binary = ensure_pinned_cherri_binary()
    targets = args.files or [
        REPO_ROOT / "fork-language" / "guide.md",
        REPO_ROOT / "fork-language" / "migration.md",
        REPO_ROOT / "fork-language" / "actions.md",
        REPO_ROOT / "language" / "functions.md",
        REPO_ROOT / "language" / "variables-constants-globals.md",
    ]
    records = []
    all_ok = True
    for target in targets:
        if not test_file(binary, str(target.absolute()), records):
            all_ok = False
    executed = [r for r in records if r["executed"]]
    if not executed:
        raise RuntimeError("No runnable or diagnostic examples were executed.")
    receipt = {
        "formatVersion":1, "compilerCommit":PINNED_CHERRI_COMMIT, "binarySha256":digest(binary),
        "passed":all_ok, "executed":len(executed),
        "runnable":sum(r["classification"] == "runnable" for r in executed),
        "diagnostic":sum(r["classification"] == "diagnostic" for r in executed),
        "referenceOnly":len(records)-len(executed), "records":records,
        "scope":"Actual structured checks and unsigned plist compilation; no Apple runtime or published-site claim.",
    }
    if args.evidence_out:
        args.evidence_out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return 0 if all_ok else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(f"FATAL: {error}", file=sys.stderr)
        sys.exit(1)
