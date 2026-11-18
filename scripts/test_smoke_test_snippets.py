#!/usr/bin/env python3
"""Real cache and snippet controls for smoke_test_snippets; no fake compiler."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
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
        cls.work = tempfile.TemporaryDirectory(prefix="cherri_docs_controls_")
        cls.root = Path(cls.work.name)
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

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def setUp(self):
        self.case = Path(tempfile.mkdtemp(dir=self.root, prefix="case-"))
        self.cache = self.case / "cache"
        self.env = unittest.mock.patch.dict(os.environ, {"CHERRI_SMOKE_CACHE_DIR":str(self.cache)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def populated_cache(self):
        self.cache.mkdir()
        repo = self.cache/"src"
        smoke.command(["git","clone","--shared","--no-checkout",str(self.good/"src"),str(repo)])
        smoke.command(["git","config","core.autocrlf","false"],cwd=repo)
        smoke.command(["git","remote","set-url","origin",smoke.PINNED_CHERRI_REPO],cwd=repo)
        smoke.command(["git","checkout","--detach",smoke.PINNED_CHERRI_COMMIT],cwd=repo)
        binary = self.cache/self.binary.name
        shutil.copy2(self.binary,binary)
        shutil.copy2(self.good/smoke.CACHE_RECEIPT,self.cache/smoke.CACHE_RECEIPT)
        smoke.inspect_cache(self.cache)
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
        source.write_bytes(source.read_bytes()+b"\n")
        before=smoke.digest(source)
        with self.assertRaisesRegex(RuntimeError,"local/ignored changes"):
            smoke.ensure_pinned_cherri_binary()
        self.assertEqual(smoke.digest(source),before)

    def test_untracked_source_rejected_and_preserved(self):
        self.populated_cache()
        source=self.cache/"src/docs-cache-local.go"
        source.write_text("package main\n",encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError,"local/ignored changes"):
            smoke.ensure_pinned_cherri_binary()
        self.assertEqual(source.read_text(encoding="utf-8"),"package main\n")

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
