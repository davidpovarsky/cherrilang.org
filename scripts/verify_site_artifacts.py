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
from urllib.parse import unquote, urljoin, urlsplit


class PageText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.links = []
        self.resources = []
        self.start_links = []
        self.navigation_links = []
        self.in_navigation = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "nav":
            self.in_navigation += 1
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])
            if self.in_navigation:
                self.navigation_links.append(attrs["href"])
            if attrs.get("id") == "start-authoring":
                self.start_links.append(attrs["href"])
        if tag in ("img", "script") and attrs.get("src"):
            self.resources.append(attrs["src"])
        if tag == "link" and attrs.get("href"):
            self.resources.append(attrs["href"])

    def handle_endtag(self, tag):
        if tag == "nav":
            self.in_navigation = max(0, self.in_navigation - 1)

    def handle_data(self, data):
        self.parts.append(data)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def built_page(site, route):
    target = site / route.lstrip("/")
    candidates = (target, Path(str(target) + ".html"), target / "index.html")
    pages = [path for path in candidates if path.is_file()]
    if len(pages) != 1:
        raise RuntimeError("Built site is missing a unique page: " + route)
    return pages[0]


def inspect_page(path):
    parser = PageText()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def verify_current_entry_points(site, root, search, baseurl):
    config = (root / "_config.yml").read_text(encoding="utf-8")
    configured = re.search(r'^baseurl:\s*["\']?([^"\'\n]*)["\']?\s*$', config, re.MULTILINE)
    if not configured or configured.group(1).rstrip("/") != baseurl:
        raise RuntimeError("Built base URL differs from the fork configuration")
    origin = "https://davidpovarsky.github.io"
    if not re.search(r'^url:\s*["\']?' + re.escape(origin) + r'["\']?\s*$', config, re.MULTILINE):
        raise RuntimeError("Fork publication origin differs from its configuration")
    if (root / "CNAME").exists() or (site / "CNAME").exists():
        raise RuntimeError("Fork publication must not carry the upstream custom domain")

    routes = {"/"}
    for source in (root / "fork-language").glob("*.md"):
        match = re.search(r"^permalink:\s*(/\S+)\s*$", source.read_text(encoding="utf-8"), re.MULTILINE)
        if not match:
            raise RuntimeError("Current documentation page has no stable route: " + source.name)
        routes.add(match.group(1))
    active_paths = {(baseurl + route).rstrip("/") for route in routes}
    relative_paths = {route.rstrip("/") for route in routes}
    client = (site / "assets/js/just-the-docs.js").read_text(encoding="utf-8")
    request = "request.open('GET', '" + baseurl + "/assets/js/search-data.json', true)"
    if request not in client or "resultLink.setAttribute('href', doc.url)" not in client:
        raise RuntimeError("Search client does not load and use the verified project URLs")
    indexed_paths = set()
    for row in search.values():
        if not isinstance(row, dict):
            raise RuntimeError("Jekyll search index contains a non-object entry")
        relative = urlsplit(str(row.get("relUrl", "")))
        path = unquote(relative.path).rstrip("/")
        if relative.scheme or relative.netloc or path not in relative_paths:
            raise RuntimeError("Default search includes a historical route: " + path)
        target = urlsplit(str(row.get("url", "")))
        if (target.scheme or target.netloc or target.path != baseurl + relative.path
                or target.query != relative.query or target.fragment != relative.fragment):
            raise RuntimeError("Search result URL does not match its project-base route")
        indexed_paths.add(unquote(target.path).rstrip("/"))
    if indexed_paths != active_paths:
        raise RuntimeError("Default search omits a current documentation route")

    checked_links = 0
    for route in sorted(routes):
        page = built_page(site, route)
        parsed = inspect_page(page)
        if route == "/":
            expected_start = baseurl + "/fork-language/guide"
            if parsed.start_links != [expected_start]:
                raise RuntimeError("Home page lacks its unique current-guide entry point")
            if "https://github.com/davidpovarsky/cherri" not in parsed.links:
                raise RuntimeError("Home page does not identify the fork source")
        elif not any(link.startswith("https://github.com/davidpovarsky/cherrilang.org/tree/main/")
                     for link in parsed.links):
            raise RuntimeError("Current page edit link does not identify the fork repository")
        for link in parsed.navigation_links:
            target = urlsplit(urljoin(origin + baseurl + route, link))
            if target.netloc == urlsplit(origin).netloc and unquote(target.path).rstrip("/") not in active_paths:
                raise RuntimeError("Default navigation recommends a historical route: " + target.path)
        for link in parsed.links + parsed.resources:
            if not link or link.startswith("#") or urlsplit(link).scheme in ("mailto", "data", "javascript"):
                continue
            target = urlsplit(urljoin(origin + baseurl + route, link))
            if target.netloc != urlsplit(origin).netloc:
                continue
            path = unquote(target.path)
            if not path.startswith(baseurl + "/"):
                raise RuntimeError("Current page contains a link outside the project base URL: " + path)
            local = path[len(baseurl):]
            candidate = site / local.lstrip("/")
            if not candidate.is_file():
                built_page(site, local)
            checked_links += 1
    archive = inspect_page(built_page(site, "/language/"))
    if "Reference archive." not in " ".join(archive.parts):
        raise RuntimeError("Historical page is missing the current-guide notice")
    return {"baseUrl": baseurl, "publicationOrigin": origin,
            "currentSearchRoutes": sorted(indexed_paths),
            "verifiedLocalLinks": checked_links, "historicalSearchEntries": 0}


def verify(site, root, baseurl="/cherrilang.org"):
    baseurl = baseurl.rstrip("/")
    if not baseurl.startswith("/") or "?" in baseurl or "#" in baseurl or ".." in baseurl:
        raise RuntimeError("Expected a project-site base URL")
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
    action_page = built_page(site, route)
    parser = inspect_page(action_page)
    page_text = " ".join(parser.parts)

    search_path = site / "assets/js/search-data.json"
    search = json.loads(search_path.read_text(encoding="utf-8"))
    if not isinstance(search, dict) or not search:
        raise RuntimeError("Jekyll search index is empty or malformed")
    entry_points = verify_current_entry_points(site, root, search, baseurl)
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
        "formatVersion": 2,
        **entry_points,
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
    parser.add_argument("--baseurl", default="/cherrilang.org")
    parser.add_argument("--evidence-out", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    receipt = verify(args.site.resolve(), root, args.baseurl)
    args.evidence_out.parent.mkdir(parents=True, exist_ok=True)
    args.evidence_out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
