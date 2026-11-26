#!/usr/bin/env python3
"""Exercise the exact reference contract with a real canonical reference.

CHERRI_REFERENCE_FIXTURE selects an existing compiler-produced/reference file
during a staged update. The default is the repository's committed reference.
These are in-memory reference controls, not a generated or published site.
"""
import hashlib
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
