#!/usr/bin/env python3
"""Exercise the exact reference contract with a real canonical reference.

CHERRI_REFERENCE_FIXTURE selects an existing compiler-produced/reference file
during a staged update. The default is the repository's committed reference.
These are in-memory reference controls, not a generated or published site.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import unittest

sys.dont_write_bytecode = True
import verify_generated_reference as verifier

ROOT = Path(__file__).resolve().parents[1]
MACROS = (
    "cache", "debugAssert", "debugClearLogs", "debugExport", "debugExportTrace",
    "debugFinish", "debugLog", "debugLogPrevious", "debugShowLogs",
    "debugStartTimer", "debugStopTimer", "debugTrace", "debugTraceEvent",
    "measure", "paginate", "require",
)


class GeneratedReferenceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = Path(os.environ.get("CHERRI_REFERENCE_FIXTURE",
                                       ROOT / "fork-language/actions.md"))
        cls.before = cls.path.read_bytes()
        cls.reference = cls.before
        if cls.reference.startswith(verifier.FRONTMATTER):
            cls.reference = cls.reference[len(verifier.FRONTMATTER):]
        cls.native, cls.macros = cls.reference.split(b"## Compiler macros\n")
        names = re.findall(rb"^### " + bytes([96]) + rb"([^" + bytes([96]) +
                           rb"\r\n]+)" + bytes([96]) + rb"$",
                           cls.macros, re.MULTILINE)
        if names != [name.encode() for name in MACROS]:
            raise RuntimeError("actual fixture does not have the selected canonical16 macro inventory")

    @classmethod
    def tearDownClass(cls):
        if cls.path.read_bytes() != cls.before:
            raise RuntimeError("reference controls changed the actual fixture")

    def consistent(self, data):
        return verifier.verify_reference(data, data, verifier.FRONTMATTER + data)

    def rejected(self, data, diagnostic):
        self.assertNotEqual(data, self.reference, "fault did not change reference")
        with self.assertRaisesRegex(RuntimeError, re.escape(diagnostic)):
            self.consistent(data)

    def test_actual_reference_is_accepted(self):
        result = self.consistent(self.reference)
        self.assertEqual(result["native_actions"], 505)
        self.assertEqual(result["compiler_macros"], 16)
        self.assertEqual(result["headings"], 521)
        self.assertEqual(result["reference_sha256"],
                         hashlib.sha256(self.reference).hexdigest())
        self.assertTrue(result["complete_byte_equality"])

    def test_exact_macro_identities_and_order(self):
        tick = bytes([96])
        heading = lambda name: b"### " + tick + name + tick + b"\n"
        chunks = re.split(rb"(?=^### )", self.macros, flags=re.MULTILINE)
        self.assertEqual(len(chunks), 17)
        changed = (
            ("foreign", self.macros.replace(heading(b"cache"), heading(b"foreignMacro"), 1)),
            ("duplicate", self.macros.replace(heading(b"cache"), heading(b"require"), 1)),
            ("missing", b"".join([chunks[0]] + chunks[2:])),
            ("reordered", b"".join(chunks[:1] + [chunks[2], chunks[1]] + chunks[3:])),
        )
        for name, tail in changed:
            with self.subTest(name=name):
                self.rejected(self.native + b"## Compiler macros\n" + tail,
                              "reference heading inventory differs")

    def test_native_inventory_stays_exact(self):
        chunks = re.split(rb"(?=^### )", self.native, flags=re.MULTILINE)
        self.assertEqual(len(chunks), 506)
        for name, native in (
                ("missing", b"".join(chunks[:1] + chunks[2:])),
                ("duplicate", self.native + chunks[1])):
            with self.subTest(name=name):
                self.rejected(native + b"## Compiler macros\n" + self.macros,
                              "reference heading inventory differs")

    def test_section_and_count_metadata(self):
        for name, changed, diagnostic in (
            ("duplicate_section", self.reference + b"\n## Compiler macros\n",
             "missing/duplicate macro section"),
            ("old_macro_count", self.reference.replace(b"**Compiler Macros:** 16\n",
                                                       b"**Compiler Macros:** 15\n", 1),
             "reference count headers differ"),
            ("wrong_native_count", self.reference.replace(b"**Total Actions:** 505  \n",
                                                          b"**Total Actions:** 504  \n", 1),
             "reference count headers differ"),
        ):
            with self.subTest(name=name):
                self.rejected(changed, diagnostic)

    def test_complete_three_way_bytes_are_required(self):
        for name, canonical, docs in (
            ("compiler_source", self.reference + b"\nchanged\n",
             verifier.FRONTMATTER + self.reference),
            ("docs_source", self.reference,
             verifier.FRONTMATTER + self.reference + b"\nchanged\n"),
        ):
            with self.subTest(name=name):
                with self.assertRaisesRegex(RuntimeError,
                                            "generated/source/Docs reference bytes differ"):
                    verifier.verify_reference(self.reference, canonical, docs)

    def test_original_frontmatter_is_required(self):
        changed = verifier.FRONTMATTER.replace(b"Actions Reference", b"Changed Reference")
        with self.assertRaisesRegex(RuntimeError, "Docs frontmatter bytes differ"):
            verifier.verify_reference(self.reference, self.reference, changed + self.reference)


class GeneratedGoInventoryTests(unittest.TestCase):
    """Consume the actual S708 process stream; never derive admission from output."""
    SOURCE = "708ed78eda1cad0f1f453559afce100edc59b8a9"
    PACKAGE = "github.com/electrikmilk/cherri/tools/language-docs"
    PARENT = "TestP15D01CheckGateProducesAndRejectsFaults"
    SCOPED = ("scoped_dialect", "scoped_void_result")
    ORIGINAL_CHILDREN = (
        "optional_primary", "typed_default", "callable_identity", "wire_key",
        "return_type", "macro_identity", "missing_category", "extra_section",
    )

    @classmethod
    def setUpClass(cls):
        fixture = ROOT / "scripts/fixtures"
        cls.raw_path = fixture / "generated-reference-s708-go-controls.jsonl"
        cls.process_path = fixture / "generated-reference-s708-go-process.json"
        cls.raw = cls.raw_path.read_bytes()
        cls.process_raw = cls.process_path.read_bytes()
        if hashlib.sha256(cls.raw).hexdigest() != "96bd2bac51ece5f7d18793038e23bb1da12500894315339f5b98307e885b82ae":
            raise RuntimeError("original S708 Go stream changed")
        if hashlib.sha256(cls.process_raw).hexdigest() != "34be61664c09971b43229c64c1ca7a70ebf01ee19a070bc87b6b014d4147fe59":
            raise RuntimeError("original S708 process receipt changed")
        cls.process = json.loads(cls.process_raw)
        cls.events = [json.loads(line) for line in cls.raw.splitlines()]

    @classmethod
    def tearDownClass(cls):
        if cls.raw_path.read_bytes() != cls.raw or cls.process_path.read_bytes() != cls.process_raw:
            raise RuntimeError("inventory controls changed original fixture bytes")

    def encode(self, events):
        return b"".join(json.dumps(event, separators=(",", ":")).encode() + b"\n"
                        for event in events)

    def child(self, name):
        return self.PARENT + "/" + name

    def test_actual_fourteen_source_bound_identities(self):
        self.assertEqual(verifier.COMPILER_SHA, self.SOURCE)
        result = verifier.verify_go_events(self.raw, self.process)
        original = {
            "TestGeneratedReferenceIncludesSeparateMacroContracts",
            "TestP15D01PrimaryParameterContract",
            "TestP15D01AllGeneratedSignaturesAndCategories",
            self.PARENT,
        } | {self.child(name) for name in self.ORIGINAL_CHILDREN}
        self.assertEqual(len(original), 12)
        expected = original | {self.child(name) for name in self.SCOPED}
        self.assertEqual(set(result["run_once"]), expected)
        self.assertEqual(set(result["passed_once"]), expected)
        self.assertEqual(len(expected), 14)
        self.assertTrue(result["package_pass"])
        self.assertEqual(result["skipped"], 0)

    def test_missing_scoped_child_rejected(self):
        for name in self.SCOPED:
            with self.subTest(name=name):
                events = [event for event in self.events if event.get("Test") != self.child(name)]
                with self.assertRaisesRegex(RuntimeError, "parent passed before required child"):
                    verifier.verify_go_events(self.encode(events), self.process)

    def test_foreign_scoped_child_rejected(self):
        for name in self.SCOPED:
            with self.subTest(name=name):
                events = [dict(event, Test=self.child("foreign_" + name))
                          if event.get("Test") == self.child(name) else dict(event)
                          for event in self.events]
                with self.assertRaisesRegex(RuntimeError, "unexpected Go test identity"):
                    verifier.verify_go_events(self.encode(events), self.process)

    def test_duplicate_scoped_run_rejected(self):
        for name in self.SCOPED:
            with self.subTest(name=name):
                events = [dict(event) for event in self.events]
                index = next(index for index, event in enumerate(events)
                             if event.get("Test") == self.child(name) and event["Action"] == "run")
                events.insert(index + 1, dict(events[index]))
                with self.assertRaisesRegex(RuntimeError, "duplicate/reordered Go test run"):
                    verifier.verify_go_events(self.encode(events), self.process)

    def test_parent_cannot_pass_before_scoped_child(self):
        for name in self.SCOPED:
            with self.subTest(name=name):
                events = [dict(event) for event in self.events]
                terminal = next(index for index, event in enumerate(events)
                                if event.get("Test") == self.PARENT and event["Action"] == "pass")
                parent_event = events.pop(terminal)
                child_terminal = next(index for index, event in enumerate(events)
                                      if event.get("Test") == self.child(name) and event["Action"] == "pass")
                events.insert(child_terminal, parent_event)
                with self.assertRaisesRegex(RuntimeError, "parent passed before required child"):
                    verifier.verify_go_events(self.encode(events), self.process)


if __name__ == "__main__":
    unittest.main(verbosity=2)
