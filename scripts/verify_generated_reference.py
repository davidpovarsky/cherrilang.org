#!/usr/bin/env python3
"""Regenerate the pinned public reference and retain actual CLI/test evidence.

Uses the already verified compiler cache. Never fetches, checks out, rebuilds
the Cherri compiler, edits either source tree, or grants formal acceptance.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import time

sys.dont_write_bytecode = True
import smoke_test_snippets as smoke

COMPILER_SHA = "57b6d919757e1d0262993c6f11c6dc1cd17d6177"
DOCS_ORIGIN = "https://github.com/davidpovarsky/cherrilang.org"
PACKAGE = "github.com/electrikmilk/cherri/tools/language-docs"
PARENTS = (
    "TestGeneratedReferenceIncludesSeparateMacroContracts",
    "TestP15D01PrimaryParameterContract",
    "TestP15D01AllGeneratedSignaturesAndCategories",
    "TestP15D01CheckGateProducesAndRejectsFaults",
)
MUTATIONS = (
    "optional_primary", "typed_default", "callable_identity", "wire_key",
    "return_type", "macro_identity", "missing_category", "extra_section",
)
EXPECTED_TESTS = frozenset(PARENTS + tuple(PARENTS[-1] + "/" + name for name in MUTATIONS))
TEST_PATTERN = "^(" + "|".join(PARENTS) + ")$"
FRONTMATTER = (b"---\ntitle: Actions Reference\nparent: Language v2.0\nlayout: default\n"
               b"nav_order: 2\npermalink: /fork-language/actions\n---\n\n")
MAX_LOG = 16 * 1024 * 1024
MAX_REFERENCE = 4 * 1024 * 1024
DOCS_FILES = (
    ".github/workflows/docs-smoke-test.yml", "scripts/smoke_test_snippets.py",
    "scripts/test_smoke_test_snippets.py", "scripts/verify_generated_reference.py",
    "fork-language/actions.md",
)
COMPILER_FILES = (
    "go.mod", "go.sum", "tools/language-docs/main.go",
    "tools/language-docs/macro_metadata_test.go", "tools/language-docs/p15_contract_test.go",
    "docs/language-v2/actions-reference.md",
)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def utc(value):
    require(isinstance(value, str), "missing UTC timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.utcoffset() is not None and parsed.utcoffset().total_seconds() == 0,
            "timestamp is not UTC")
    return parsed


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    def invalid(_):
        raise RuntimeError("nonfinite JSON value")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def read_original(path, maximum):
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_ino != 0,
            "original must be one regular, non-linked file: " + str(path))
    require(before.st_size <= maximum, "original exceeds read bound: " + str(path))
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        require((opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino), "original identity changed")
        raw = stream.read(maximum + 1)
    after = path.lstat()
    require(len(raw) == before.st_size <= maximum and
            (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), "original changed while reading")
    return raw, {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                 "device": before.st_dev, "inode": before.st_ino, "mtime_ns": before.st_mtime_ns}


def group_alive(pid):
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False


class Processes:
    def __init__(self, output):
        self.output = output
        info = output.lstat()
        self.identity = info.st_dev, info.st_ino
        self.rows = []
        self.environment = dict(os.environ, GIT_NO_REPLACE_OBJECTS="1",
                                PYTHONDONTWRITEBYTECODE="1", GOMAXPROCS="2")

    def write(self, path, value):
        info = self.output.lstat()
        require(stat.S_ISDIR(info.st_mode) and (info.st_dev, info.st_ino) == self.identity,
                "owned evidence directory changed")
        path.write_bytes(encoded(value))

    def run(self, label, arguments, cwd, budget):
        require(re.fullmatch(r"[a-z0-9-]+", label) and not any(r["label"] == label for r in self.rows),
                "duplicate/invalid process label")
        cwd = Path.cwd().resolve() if cwd is None else Path(cwd).resolve(strict=True)
        row = {"label": label, "command": list(arguments), "cwd": str(cwd), "budget_seconds": budget,
               "started_utc": stamp(), "finished_utc": None, "state": "STARTING", "pid": None,
               "returncode": None, "timed_out": False, "orphaned_group": False, "signals": [],
               "cleanup_complete": False}
        self.rows.append(row)
        receipt = self.output / (label + ".process.json")
        stdout_path, stderr_path = (self.output / (label + suffix) for suffix in
                                    (".stdout.original", ".stderr.original"))
        self.write(receipt, row)
        process = None
        raised = None
        start = time.monotonic()
        print("DOCS_GENERATOR_START " + label, flush=True)
        with stdout_path.open("xb", buffering=0) as stdout, stderr_path.open("xb", buffering=0) as stderr:
            try:
                process = subprocess.Popen(arguments, cwd=cwd, env=self.environment,
                                           stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                           start_new_session=True)
                row.update(pid=process.pid, process_group=process.pid, state="RUNNING")
                self.write(receipt, row)
                try:
                    process.wait(timeout=max(0, budget - (time.monotonic() - start)))
                    if time.monotonic() - start > budget:
                        row["timed_out"] = True
                except subprocess.TimeoutExpired:
                    row["timed_out"] = True
            except BaseException as error:
                raised = error
                row["interruption"] = type(error).__name__
            finally:
                if process is not None:
                    alive = group_alive(process.pid)
                    row["orphaned_group"] = alive and process.poll() is not None and not row["timed_out"]
                    if alive:
                        # This session/group was created by this exact Popen.
                        # Never signal a name, a shared Go process, or another group.
                        for sig in (signal.SIGTERM, signal.SIGKILL):
                            if not group_alive(process.pid):
                                break
                            try:
                                os.killpg(process.pid, sig)
                                row["signals"].append(signal.Signals(sig).name)
                            except ProcessLookupError:
                                break
                            try:
                                process.wait(timeout=2)
                            except subprocess.TimeoutExpired:
                                pass
                            until = time.monotonic() + 1
                            while group_alive(process.pid) and time.monotonic() < until:
                                time.sleep(0.025)
                    try:
                        process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        pass
                    row["returncode"] = process.returncode
                    row["cleanup_complete"] = process.returncode is not None and not group_alive(process.pid)
                else:
                    row["cleanup_complete"] = True
        row.update(finished_utc=stamp(), elapsed_seconds=round(time.monotonic() - start, 6), state="TERMINAL")
        try:
            stdout, row["stdout"] = read_original(stdout_path, MAX_LOG)
            stderr, row["stderr"] = read_original(stderr_path, MAX_LOG)
        except BaseException as error:
            row["evidence_error"] = str(error)
            self.write(receipt, row)
            raise
        row["passed"] = (row["returncode"] == 0 and not row["timed_out"] and not row["orphaned_group"]
                         and row["cleanup_complete"] and raised is None)
        self.write(receipt, row)
        print("DOCS_GENERATOR_END " + json.dumps({k: row[k] for k in
              ("label", "passed", "returncode", "timed_out", "elapsed_seconds")}), flush=True)
        if raised is not None:
            raise raised
        require(row["passed"], "actual process failed: " + label)
        return row, stdout, stderr

    def metadata(self, label, arguments, cwd):
        return self.run(label, arguments, cwd, 15)[1]


def source_state(processes, phase, role, repo, expected_sha, files):
    def git(name, *arguments):
        return processes.metadata(phase + "-" + role + "-" + name,
                                  ["git", "--no-replace-objects", *arguments], repo)

    require(repo.is_dir() and not repo.is_symlink(), "source root must be a real directory")
    head = git("head", "rev-parse", "HEAD").decode().strip()
    require(head == expected_sha, "source HEAD differs: " + role)
    require(Path(git("root", "rev-parse", "--show-toplevel").decode().strip()).resolve() == repo,
            "source top-level differs: " + role)
    require(not git("status", "status", "--porcelain=v1", "--untracked-files=all", "--ignored=matching"),
            "source has tracked/untracked/ignored changes: " + role)
    staged = git("stage", "ls-files", "--stage", "-z")
    flags = git("flags", "ls-files", "-v", "-z")
    require(all(item.startswith(b"H ") for item in flags.split(b"\0") if item),
            "source has hidden/skip-worktree index flags: " + role)
    entries = {}
    for item in staged.split(b"\0"):
        if not item:
            continue
        fields, path = item.split(b"\t", 1)
        mode, blob, stage = fields.decode().split()
        require(stage == "0", "source has unmerged index")
        entries[path.decode()] = mode, blob
    witnesses = {}
    for relative in files:
        raw, witness = read_original(repo / relative, MAX_REFERENCE)
        require(relative in entries and entries[relative][0] in ("100644", "100755"),
                "source witness is not one tracked regular file")
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        require(blob == entries[relative][1], "source witness differs from Git blob: " + relative)
        witnesses[relative] = dict(witness, git_blob=blob)
    return {"root": str(repo), "head": head, "clean": True, "files": witnesses,
            "tracked_stage_sha256": hashlib.sha256(staged).hexdigest(),
            "tracked_flags_sha256": hashlib.sha256(flags).hexdigest()}


def cache_state(processes, phase, cache):
    original_command = smoke.command
    counter = 0

    def observed_command(arguments, *, cwd=None, check=True):
        nonlocal counter
        counter += 1
        # Preserve inspect_cache's real checks, while capturing and supervising
        # every command. This adapter never substitutes a result or calls build.
        allowed = (arguments[:3] == ["git", "rev-parse", "HEAD"] or
                   arguments[:2] == ["git", "status"] or
                   arguments == ["git", "remote", "get-url", "origin"] or
                   arguments[:3] == ["go", "version", "-m"])
        require(allowed, "cache inspector attempted a non-read-only command")
        row, out, err = processes.run(phase + "-cache-" + str(counter), arguments, cwd, 15)
        return subprocess.CompletedProcess(arguments, row["returncode"], out.decode("utf-8"), err.decode("utf-8"))

    smoke.command = observed_command
    try:
        binary, receipt = smoke.inspect_cache(cache)
    finally:
        smoke.command = original_command
    raw, receipt_file = read_original(cache / smoke.CACHE_RECEIPT, 65536)
    require(encoded(strict_json(raw)) == encoded(receipt), "cache receipt differs in typed JSON fields")
    (processes.output / (phase + "-compiler-cache-receipt.original.json")).write_bytes(raw)
    _, binary_file = read_original(binary, 128 * 1024 * 1024)
    require(binary_file["sha256"] == receipt["binarySha256"], "verified binary changed")
    return {"receipt": receipt, "receipt_file": receipt_file, "binary": binary_file}


def verify_go_events(raw, process):
    run, passed = Counter(), Counter()
    package_start = package_pass = 0
    start, finish = utc(process["started_utc"]), utc(process["finished_utc"])
    for number, line in enumerate(raw.splitlines(), 1):
        require(line.strip(), "blank/non-JSON Go event")
        event = strict_json(line)
        require(isinstance(event, dict) and event.get("Package") == PACKAGE, "foreign Go package")
        require(start <= utc(event.get("Time")) <= finish, "Go event outside actual process interval")
        action = event.get("Action")
        require(action in ("start", "run", "pass", "output"), "failed/skipped/unknown Go event")
        require(not package_pass, "Go event after package terminal")
        if "Elapsed" in event:
            elapsed = event["Elapsed"]
            require(type(elapsed) in (int, float) and math.isfinite(elapsed) and elapsed >= 0,
                    "invalid Go elapsed value")
        if "Test" in event:
            name = event["Test"]
            require(isinstance(name, str) and name in EXPECTED_TESTS and package_start == 1,
                    "unexpected Go test identity")
            if action == "run":
                require(run[name] == 0 and passed[name] == 0, "duplicate/reordered Go test run")
                run[name] += 1
            elif action == "pass":
                require(run[name] == 1 and passed[name] == 0, "Go test pass without unique run")
                require(all(passed[child] == 1 for child in EXPECTED_TESTS if child.startswith(name + "/")),
                        "parent passed before required child")
                passed[name] += 1
            else:
                require(action == "output" and run[name] == 1 and passed[name] == 0,
                        "Go output outside running test")
        elif action == "start":
            package_start += 1
            require(package_start == 1 and not run, "duplicate/reordered package start")
        elif action == "pass":
            require(package_start == 1 and set(run) == set(passed) == EXPECTED_TESTS and
                    all(run[name] == passed[name] == 1 for name in EXPECTED_TESTS), "incomplete fixed Go inventory")
            package_pass += 1
        else:
            require(action == "output" and package_start == 1, "invalid package event")
    require(package_start == package_pass == 1 and len(run) == 12 and len(passed) == 12,
            "missing complete package/12-test execution")
    return {"package": PACKAGE, "parents": list(PARENTS), "mutations": list(MUTATIONS),
            "run_once": sorted(run), "passed_once": sorted(passed), "package_pass": True, "skipped": 0}


def verify_reference(generated, canonical, docs):
    require(len(FRONTMATTER) == 119 and docs.startswith(FRONTMATTER), "Docs frontmatter bytes differ")
    require(generated == canonical == docs[len(FRONTMATTER):], "generated/source/Docs reference bytes differ")
    marker = b"## Compiler macros\n"
    require(generated.count(marker) == 1, "missing/duplicate macro section")
    native, macros = generated.split(marker)
    pattern = rb"^### `([^`\r\n]+)`$"
    native_names = re.findall(pattern, native, re.MULTILINE)
    macro_names = re.findall(pattern, macros, re.MULTILINE)
    require(len(native_names) == 505 and len(macro_names) == 15 and
            len(set(native_names + macro_names)) == 520, "reference heading inventory differs")
    require(b"**Total Actions:** 505  \n" in native and b"**Compiler Macros:** 15\n" in macros,
            "reference count headers differ")
    return {"native_actions": 505, "compiler_macros": 15, "headings": 520,
            "frontmatter_bytes": 119, "complete_byte_equality": True,
            "reference_sha256": hashlib.sha256(generated).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--docs-sha", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    require(os.name == "posix", "this CI acquisition requires owned POSIX process groups")
    require(re.fullmatch(r"[0-9a-f]{40}", args.docs_sha), "Docs source must be a full immutable SHA")
    require(smoke.PINNED_CHERRI_COMMIT == COMPILER_SHA, "compiler pin changed without generator contract review")
    docs, cache = Path(__file__).resolve().parents[1], args.cache.absolute()
    output = args.output_dir.parent.resolve(strict=True) / args.output_dir.name
    require(not output.exists() and not output.is_symlink(), "evidence destination already exists; preserved")
    require(all(root != output and root not in output.parents for root in (docs, cache.resolve(strict=True))),
            "evidence destination must be outside both source/cache trees")
    output.mkdir(mode=0o700)
    processes = Processes(output)
    report = {"schema": "cherri.docs-generated-reference-ci/v1", "passed": False,
              "compiler_source": COMPILER_SHA, "docs_source": args.docs_sha, "started_utc": stamp(),
              "commands": {"generation": "NOT_RUN", "check": "NOT_RUN", "go_controls": "NOT_RUN"},
              "processes": processes.rows, "formal_acceptance_granted": False, "apple_runtime_proved": False,
              "scope": "Actual pinned CLI generation, unchanged --check and fixed Go controls; no publication or full179 claim."}
    report_path = output / "generation-report.json"
    processes.write(report_path, report)
    before = None
    source = cache / "src"

    def snapshot(phase):
        state = {"cache": cache_state(processes, phase, cache),
                 "compiler": source_state(processes, phase, "compiler", source, COMPILER_SHA, COMPILER_FILES),
                 "docs": source_state(processes, phase, "docs", docs, args.docs_sha, DOCS_FILES)}
        origin = processes.metadata(phase + "-docs-origin", ["git", "remote", "get-url", "origin"], docs).decode().strip()
        require(origin in (DOCS_ORIGIN, DOCS_ORIGIN + ".git"), "Docs origin differs")
        state["docs"]["origin"] = origin
        processes.write(output / (phase + "-source-identities.json"), state)
        return state

    def interrupted(_signum, _frame):
        raise InterruptedError("CI interrupted; owned process cleanup required")

    old_handler = signal.signal(signal.SIGTERM, interrupted)
    try:
        before = snapshot("before")
        report["before"] = before
        target = output / "actions-reference.generated.md"
        row, _, _ = processes.run("generate", ["go", "run", "-p=2", "./tools/language-docs", str(target)], source, 180)
        report["commands"]["generation"] = row
        generated, report["generated"] = read_original(target, MAX_REFERENCE)
        row, _, _ = processes.run("check", ["go", "run", "-p=2", "./tools/language-docs", "--check", str(target)], source, 180)
        report["commands"]["check"] = row
        checked, checked_witness = read_original(target, MAX_REFERENCE)
        require(checked == generated and checked_witness == report["generated"], "--check changed its owned target")
        row, raw, _ = processes.run("go-controls", ["go", "test", "-p=2", "-count=1", "-json", "-timeout=60s",
                                    "./tools/language-docs", "-run", TEST_PATTERN], source, 90)
        report["commands"]["go_controls"] = row
        report["go_events"] = verify_go_events(raw, row)
        final_generated, final_witness = read_original(target, MAX_REFERENCE)
        require(final_generated == generated and final_witness == report["generated"],
                "generated target changed during Go controls")
        canonical, _ = read_original(source / "docs/language-v2/actions-reference.md", MAX_REFERENCE)
        docs_reference, _ = read_original(docs / "fork-language/actions.md", MAX_REFERENCE)
        report["reference"] = verify_reference(generated, canonical, docs_reference)
    except BaseException as error:
        report["error"] = type(error).__name__ + ": " + str(error)
    finally:
        # Failed/timed-out processes remain actual executions in the summary.
        # A process that raised before returning is never relabeled NOT_RUN.
        for field, label in (("generation", "generate"), ("check", "check"), ("go_controls", "go-controls")):
            recorded = [row for row in processes.rows if row["label"] == label]
            if recorded:
                report["commands"][field] = recorded[0]
        if before is not None:
            try:
                after = snapshot("after")
                report["after"] = after
                require(before == after, "cache/binary/receipt/compiler/Docs source changed during generation")
                report["sources_unchanged"] = True
            except BaseException as error:
                report["postflight_error"] = type(error).__name__ + ": " + str(error)
        report["passed"] = ("error" not in report and "postflight_error" not in report and
                            report.get("sources_unchanged") is True and "go_events" in report and "reference" in report)
        report["finished_utc"] = stamp()
        processes.write(report_path, report)
        signal.signal(signal.SIGTERM, old_handler)
    print(json.dumps({"passed": report["passed"], "evidence": str(report_path),
                      "formal_acceptance_granted": False}), flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, ValueError) as error:
        print("FATAL: " + str(error), file=sys.stderr)
        raise SystemExit(1)
