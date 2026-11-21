#!/usr/bin/env python3
"""Real cache and snippet controls for smoke_test_snippets; no fake compiler."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("smoke", Path(__file__).with_name("smoke_test_snippets.py"))
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


class SmokeProductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The fixture owns this directory. Failed lease/pristine checks retain it
        # for diagnosis; successful suites clean only their own directory.
        cls.root = Path(tempfile.mkdtemp(prefix="cherri_docs_controls_"))
        cls.source_pool = cls.root / "source-pool"
        cls.source_lease = None
        cls.source_events = []
        supplied = os.environ.get("CHERRI_SMOKE_TEST_CACHE")
        if supplied:
            cls.good = Path(supplied)
            cls.binary = smoke.inspect_cache(cls.good)[0]
        else:
            cls.good = cls.root / "fresh-cache"
            with unittest.mock.patch.dict(os.environ, {"CHERRI_SMOKE_CACHE_DIR":str(cls.good)}):
                cls.binary = Path(smoke.ensure_pinned_cherri_binary())
        supplied_wrong = os.environ.get("CHERRI_SMOKE_TEST_WRONG_BINARY")
        if supplied_wrong:
            cls.wrong = Path(supplied_wrong)
        else:
            repo = cls.root / "different-commit"
            smoke.command(["git","clone","--shared","--no-checkout",str(cls.good/"src"),str(repo)])
            smoke.command(["git","config","core.autocrlf","false"],cwd=repo)
            smoke.command(["git","checkout","--detach",smoke.PINNED_CHERRI_COMMIT],cwd=repo)
            (repo/"docs-test-revision.txt").write_text("Synthetic cache provenance control.\n",encoding="utf-8")
            smoke.command(["git","add","docs-test-revision.txt"],cwd=repo)
            smoke.command(["git","-c","user.name=Cherri Cache Test","-c","user.email=cache-test@example.invalid",
                           "commit","-m","test fixture: intentionally different compiler revision"],cwd=repo)
            cls.wrong = cls.root / "wrong-cherri"
            smoke.command(["go","build","-buildvcs=true","-trimpath","-o",str(cls.wrong),"."],cwd=repo)
        actual = smoke.command(["go","version","-m",str(cls.wrong)]).stdout
        assert "vcs.revision="+smoke.PINNED_CHERRI_COMMIT not in actual
        # One genuine ordinary checkout, never a linked worktree, is leased
        # exclusively into each case's separate cache. Only source is reused:
        # binaries, receipts, corruption and other output stay case-local.
        smoke.command(["git","clone","--shared","--no-checkout",str(cls.good/"src"),str(cls.source_pool)])
        smoke.command(["git","config","core.autocrlf","false"],cwd=cls.source_pool)
        smoke.command(["git","remote","set-url","origin",smoke.PINNED_CHERRI_REPO],cwd=cls.source_pool)
        smoke.command(["git","checkout","--detach",smoke.PINNED_CHERRI_COMMIT],cwd=cls.source_pool)
        cls.pristine_source_state = cls.read_source_state(cls.source_pool)

    @staticmethod
    def read_source_state(repo):
        if not repo.is_dir() or not (repo/".git").is_dir():
            raise AssertionError("fixture requires an ordinary Git checkout")
        if any(not smoke.real_path(p) for p in (repo,repo/".git")):
            raise AssertionError("fixture source must not be a link or junction")
        def git(*args):
            return smoke.command(["git","--no-replace-objects",*args],cwd=repo).stdout
        if Path(git("rev-parse","--show-toplevel").strip()).resolve() != repo.resolve():
            raise AssertionError("fixture source top-level identity changed")
        if git("rev-parse","--git-dir").strip() != ".git":
            raise AssertionError("fixture source is not an ordinary checkout")
        state = {
            "revision":git("rev-parse","HEAD").strip(),
            "origin":git("remote","get-url","origin").strip(),
            "status":git("status","--porcelain=v1","--untracked-files=all","--ignored=matching"),
            "autocrlf":git("config","--get","core.autocrlf").strip(),
            "trackedStageSha256":hashlib.sha256(git("ls-files","--stage").encode()).hexdigest(),
            "trackedFlagsSha256":hashlib.sha256(git("ls-files","-v").encode()).hexdigest(),
            "goModSha256":smoke.digest(repo/"go.mod"),
        }
        if state["revision"] != smoke.PINNED_CHERRI_COMMIT or state["origin"] != smoke.PINNED_CHERRI_REPO:
            raise AssertionError("fixture source identity changed")
        if state["status"] or state["autocrlf"] != "false":
            raise AssertionError("fixture source is not fully pristine")
        return state

    @classmethod
    def tearDownClass(cls):
        acquired = [e["case"] for e in cls.source_events if e["event"] == "acquire"]
        released = [e["case"] for e in cls.source_events if e["event"] == "release"]
        if cls.source_lease is not None or acquired != released or len(set(acquired)) != len(acquired):
            raise AssertionError(f"source lease contamination; owned fixture retained at {cls.root}")
        if cls.read_source_state(cls.source_pool) != cls.pristine_source_state:
            raise AssertionError(f"source state leaked between cases; owned fixture retained at {cls.root}")
        # Match TemporaryDirectory's Windows read-only-file cleanup, restricted
        # to this successfully verified fixture tree.
        def remove_readonly(function, path, error):
            if not isinstance(error[1], PermissionError):
                raise error[1]
            candidate = Path(path)
            if cls.root not in candidate.parents or candidate.is_symlink():
                raise error[1]
            os.chmod(candidate, stat.S_IREAD | stat.S_IWRITE)
            function(path)
        shutil.rmtree(cls.root, onerror=remove_readonly)

    def source_witness(self, event, **fields):
        row = {"event":event, "case":self._testMethodName, "cache":str(self.cache), **fields}
        type(self).source_events.append(row)
        print("CACHE_SOURCE_WITNESS " + json.dumps(row, sort_keys=True), flush=True)

    def release_source(self):
        cls = type(self)
        self.assertEqual(cls.source_lease, self.case, "source lease belongs to a different case")
        repo = self.cache/"src"
        state = self.read_source_state(repo)
        self.assertEqual(state, cls.pristine_source_state, "source mutation leaked from this case")
        self.assertFalse(cls.source_pool.exists(), "source pool unexpectedly occupied")
        repo.rename(cls.source_pool)
        self.assertEqual(self.read_source_state(cls.source_pool), cls.pristine_source_state)
        cls.source_lease = None
        self.source_witness("release", sourceState=state)

    def owned_file_identity(self, path):
        repo = self.cache/"src"
        self.assertEqual(path.parent, repo)
        self.assertEqual(type(self).source_lease, self.case)
        self.assertTrue(all(smoke.real_path(p) for p in (self.case,self.cache,repo,path)),
                        "fixture file identity became a link/junction; preserve it")
        parent = repo.lstat()
        self.assertTrue(stat.S_ISDIR(parent.st_mode))
        self.assertEqual((parent.st_dev,parent.st_ino), self.leased_source_identity)
        actual = path.lstat()
        self.assertTrue(stat.S_ISREG(actual.st_mode) and actual.st_ino != 0 and actual.st_nlink == 1,
                        "fixture file identity is not one owned regular file; preserve it")
        return actual.st_dev,actual.st_ino

    def restore_owned_source_file(self, path, original, mutation, identity):
        self.assertEqual(self.owned_file_identity(path), identity,
                         "fixture file identity changed; preserve the replacement")
        # Opening without truncation and checking the descriptor prevents a
        # substituted same-byte file from being overwritten by compensation.
        with path.open("r+b") as stream:
            actual = os.fstat(stream.fileno())
            self.assertEqual((actual.st_dev,actual.st_ino), identity, "fixture descriptor identity changed")
            self.assertEqual(stream.read(), mutation, "fixture mutation changed unexpectedly; preserve it")
            self.assertEqual(self.owned_file_identity(path), identity, "fixture file identity changed")
            stream.seek(0)
            stream.write(original)
            stream.truncate()
        self.assertEqual(self.owned_file_identity(path), identity)
        self.assertEqual(path.read_bytes(), original)
        self.source_witness("restore-owned-file", path=path.name,
                            mutationSha256=hashlib.sha256(mutation).hexdigest(),
                            restoredSha256=hashlib.sha256(original).hexdigest())

    def remove_owned_source_file(self, path, mutation, identity):
        self.assertEqual(self.owned_file_identity(path), identity,
                         "fixture file identity changed; preserve the replacement")
        self.assertEqual(path.read_bytes(), mutation, "fixture mutation changed unexpectedly; preserve it")
        self.assertEqual(self.owned_file_identity(path), identity)
        path.unlink()
        self.assertFalse(path.exists())
        self.source_witness("remove-owned-file", path=path.name,
                            mutationSha256=hashlib.sha256(mutation).hexdigest())

    def assert_same_byte_replacement_rejected(self, path, mutation, operation, *args):
        original_identity = self.owned_file_identity(path)
        held = self.case/(path.name+".held-original")
        self.assertFalse(held.exists())
        path.rename(held)
        replacement_identity = None
        try:
            path.write_bytes(mutation)
            replacement_identity = self.owned_file_identity(path)
            self.assertNotEqual(replacement_identity, original_identity)
            with self.assertRaisesRegex(AssertionError,"identity"):
                operation(path,*args)
            self.assertEqual(path.read_bytes(),mutation)
            self.assertEqual(self.owned_file_identity(path),replacement_identity)
            self.assertEqual(held.read_bytes(),mutation)
            self.source_witness("same-byte-replacement-rejected", path=path.name)
        finally:
            # Remove only the exact new regular file this control created.
            if replacement_identity is not None:
                self.remove_owned_source_file(path,mutation,replacement_identity)
            self.assertFalse(path.exists(), "unexpected replacement retained")
            held.rename(path)
        self.assertEqual(self.owned_file_identity(path),original_identity)

    def setUp(self):
        self.assertIsNone(type(self).source_lease, "prior case did not restore its owned source")
        self.case = Path(tempfile.mkdtemp(dir=self.root, prefix="case-"))
        self.cache = self.case / "cache"
        self.env = unittest.mock.patch.dict(os.environ, {"CHERRI_SMOKE_CACHE_DIR":str(self.cache)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def populated_cache(self):
        cls = type(self)
        self.assertIsNone(cls.source_lease)
        self.assertEqual(self.read_source_state(cls.source_pool), cls.pristine_source_state)
        self.cache.mkdir()
        repo = self.cache/"src"
        cls.source_pool.rename(repo)
        cls.source_lease = self.case
        source_info = repo.lstat()
        self.leased_source_identity = (source_info.st_dev,source_info.st_ino)
        self.addCleanup(self.release_source)
        state = self.read_source_state(repo)
        self.assertEqual(state, cls.pristine_source_state)
        binary = self.cache/self.binary.name
        shutil.copy2(self.binary,binary)
        shutil.copy2(self.good/smoke.CACHE_RECEIPT,self.cache/smoke.CACHE_RECEIPT)
        smoke.inspect_cache(self.cache)
        self.source_witness("acquire", sourceState=state, binarySha256=smoke.digest(binary))
        return binary

    def test_valid_cache_reuses_verified_binary_without_rebuild(self):
        binary = self.populated_cache()
        before = binary.stat().st_mtime_ns
        original = smoke.command
        def offline(args, **kwargs):
            self.assertFalse(args[0]=="git" and "fetch" in args)
            self.assertFalse(args[0]=="go" and "build" in args)
            return original(args, **kwargs)
        with unittest.mock.patch.object(smoke,"command",side_effect=offline):
            self.assertEqual(smoke.ensure_pinned_cherri_binary(),str(binary))
        self.assertEqual(binary.stat().st_mtime_ns,before)

    def test_wrong_real_binary_rejected_even_with_matching_digest_receipt(self):
        binary = self.populated_cache()
        shutil.copy2(self.wrong,binary)
        receipt = json.loads((self.cache/smoke.CACHE_RECEIPT).read_text(encoding="utf-8"))
        receipt["binarySha256"] = smoke.digest(binary)
        (self.cache/smoke.CACHE_RECEIPT).write_text(json.dumps(receipt),encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError,"binary VCS revision"):
            smoke.ensure_pinned_cherri_binary()
        self.assertEqual(smoke.digest(binary),smoke.digest(self.wrong))

    def test_corrupt_binary_digest_rejected_and_bytes_preserved(self):
        binary = self.populated_cache()
        with binary.open("ab") as stream:stream.write(b"synthetic-corruption")
        before=smoke.digest(binary)
        with self.assertRaises(RuntimeError):
            smoke.ensure_pinned_cherri_binary()
        self.assertEqual(smoke.digest(binary),before)

    def test_dirty_tracked_source_rejected_and_preserved(self):
        self.populated_cache()
        source=self.cache/"src/go.mod"
        identity=self.owned_file_identity(source)
        original=source.read_bytes()
        mutation=original+b"\n"
        source.write_bytes(mutation)
        self.addCleanup(self.restore_owned_source_file,source,original,mutation,identity)
        before=smoke.digest(source)
        with self.assertRaisesRegex(RuntimeError,"local/ignored changes"):
            smoke.ensure_pinned_cherri_binary()
        self.assertEqual(smoke.digest(source),before)
        with self.assertRaisesRegex(AssertionError,"not fully pristine"):
            self.read_source_state(self.cache/"src")
        self.assert_same_byte_replacement_rejected(source,mutation,
            self.restore_owned_source_file,original,mutation,identity)

    def test_untracked_source_rejected_and_preserved(self):
        self.populated_cache()
        source=self.cache/"src/docs-cache-local.go"
        self.assertFalse(source.exists(), "untracked control must own its new file")
        mutation=b"package main\n"
        source.write_bytes(mutation)
        identity=self.owned_file_identity(source)
        self.addCleanup(self.remove_owned_source_file,source,mutation,identity)
        with self.assertRaisesRegex(RuntimeError,"local/ignored changes"):
            smoke.ensure_pinned_cherri_binary()
        self.assertEqual(source.read_text(encoding="utf-8"),"package main\n")
        with self.assertRaisesRegex(AssertionError,"not fully pristine"):
            self.read_source_state(self.cache/"src")
        self.assert_same_byte_replacement_rejected(source,mutation,
            self.remove_owned_source_file,mutation,identity)

    def test_missing_receipt_does_not_rebuild_or_delete_binary(self):
        binary=self.populated_cache()
        (self.cache/smoke.CACHE_RECEIPT).unlink()
        before=smoke.digest(binary)
        with self.assertRaisesRegex(RuntimeError,"receipt is missing"):
            smoke.ensure_pinned_cherri_binary()
        self.assertEqual(smoke.digest(binary),before)

    def test_unmanaged_directory_is_not_deleted_or_modified(self):
        self.cache.mkdir()
        sentinel=self.cache/"must-preserve.txt"
        sentinel.write_bytes(b"caller-owned data\n")
        with self.assertRaisesRegex(RuntimeError,"incomplete or unmanaged"):
            smoke.ensure_pinned_cherri_binary()
        self.assertEqual(list(self.cache.iterdir()),[sentinel])
        self.assertEqual(sentinel.read_bytes(),b"caller-owned data\n")

    def test_occupied_empty_directory_is_not_used(self):
        self.cache.mkdir()
        with self.assertRaisesRegex(RuntimeError,"incomplete or unmanaged"):
            smoke.ensure_pinned_cherri_binary()
        self.assertEqual(list(self.cache.iterdir()),[])

    def test_failed_fetch_cleans_only_the_owned_stage(self):
        with unittest.mock.patch.object(smoke,"PINNED_CHERRI_REPO",str(self.case/"missing-repository")):
            with self.assertRaises(subprocess.CalledProcessError):
                smoke.ensure_pinned_cherri_binary()
        self.assertFalse(self.cache.exists())
        self.assertEqual(list(self.case.iterdir()),[])

    def test_actual_valid_check_and_native_plist(self):
        ok,detail,receipt=smoke.check_example(str(self.binary),'let message = text("Docs control")\nshow(message)')
        self.assertTrue(ok,detail)
        self.assertEqual(receipt["actualErrors"],[])
        self.assertGreater(receipt["actionCount"],0)
        self.assertEqual(len(receipt["unsignedSha256"]),64)

    def test_exact_invalid_diagnostic_and_no_output(self):
        ok,detail,receipt=smoke.check_example(str(self.binary),'let count = 0\ncount = 1',["E_ASSIGN_IMMUTABLE"])
        self.assertTrue(ok,detail)
        self.assertEqual(receipt["actualErrors"],["E_ASSIGN_IMMUTABLE"])
        self.assertNotEqual(receipt["compileExit"],0)
        self.assertNotIn("unsignedSha256",receipt)

    def test_wrong_expected_diagnostic_does_not_pass(self):
        ok,detail,_=smoke.check_example(str(self.binary),'let count = 0\ncount = 1',["E_UNDEFINED_SYMBOL"])
        self.assertFalse(ok)
        self.assertIn("expected exact errors",detail)


if __name__ == "__main__":
    import unittest.mock
    unittest.main(verbosity=2)
