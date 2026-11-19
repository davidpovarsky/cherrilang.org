#!/usr/bin/env python3
"""Verify built Jekyll artifacts against the checked-in canonical reference."""
import argparse
import ast
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit


class PageText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(site, root):
    reference = root / "fork-language/actions.md"
    source = reference.read_text(encoding="utf-8")
    permalink = re.search(r"^permalink:\s*(/\S+)\s*$", source, re.MULTILINE)
    fingerprints = re.findall(r"Fingerprint:\*\*\s*`([0-9a-f]{64})`", source, re.IGNORECASE)
    names = re.findall(r"^###\s+`([^`]+)`\s*$", source, re.MULTILINE)
    native_count = re.search(r"\*\*Total Actions:\*\*\s*(\d+)", source)
    if not permalink or not fingerprints or not names or not native_count:
        raise RuntimeError("Generated action reference has incomplete metadata")
    if len(names) < int(native_count.group(1)):
        raise RuntimeError("Generated action reference lost declared native signatures")

    route = permalink.group(1).rstrip("/")
    target = site / route.lstrip("/")
    candidates = (target, Path(str(target) + ".html"), target / "index.html")
    pages = [path for path in candidates if path.is_file()]
    if len(pages) != 1 or not (site / "index.html").is_file():
        raise RuntimeError("Built site is missing a unique action-reference page or home page")
    action_page = pages[0]
    parser = PageText()
    parser.feed(action_page.read_text(encoding="utf-8"))
    page_text = " ".join(parser.parts)

    search_path = site / "assets/js/search-data.json"
    search = json.loads(search_path.read_text(encoding="utf-8"))
    if not isinstance(search, dict) or not search:
        raise RuntimeError("Jekyll search index is empty or malformed")
    action_rows = []
    for row in search.values():
        if not isinstance(row, dict):
            raise RuntimeError("Jekyll search index contains a non-object entry")
        if urlsplit(str(row.get("relUrl", ""))).path.rstrip("/") == route:
            action_rows.append(row)
    if not action_rows:
        raise RuntimeError("Action reference is absent from Jekyll search")
    search_text = " ".join(
        str(row.get(field, "")) for row in action_rows for field in ("title", "content")
    )
    for label, text in (("rendered action page", page_text), ("search index", search_text)):
        missing_fingerprints = [value for value in fingerprints if value not in text]
        missing_names = [name for name in names if name not in text]
        if missing_fingerprints or missing_names:
            raise RuntimeError(
                f"{label} lost canonical metadata: fingerprints={missing_fingerprints}, "
                f"signatures={missing_names[:10]}"
            )

    module = ast.parse((root / "scripts/smoke_test_snippets.py").read_text(encoding="utf-8"))
    compiler_commit = None
    for node in module.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "PINNED_CHERRI_COMMIT"
            for target in node.targets
        ):
            compiler_commit = ast.literal_eval(node.value)
    if not isinstance(compiler_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", compiler_commit):
        raise RuntimeError("Documentation compiler pin is not immutable")
    docs_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=normal"], cwd=root, text=True
    ).strip()
    if dirty:
        raise RuntimeError("Site build changed the source checkout: " + dirty)
    return {
        "formatVersion": 1,
        "docsCommit": docs_commit,
        "compilerCommit": compiler_commit,
        "sourceTreeClean": True,
        "sourceReferenceSha256": sha256(reference),
        "renderedActionPage": action_page.relative_to(site).as_posix(),
        "renderedActionPageSha256": sha256(action_page),
        "searchIndexSha256": sha256(search_path),
        "schemaFingerprints": fingerprints,
        "nativeActionCount": int(native_count.group(1)),
        "renderedReferenceSignatures": len(names),
        "searchEntries": len(search),
        "actionSearchEntries": len(action_rows),
        "sitePublished": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True, type=Path)
    parser.add_argument("--evidence-out", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    receipt = verify(args.site.resolve(), root)
    args.evidence_out.parent.mkdir(parents=True, exist_ok=True)
    args.evidence_out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
