#!/usr/bin/env python3
"""Corrupt and restore actual built Jekyll artifacts; never synthesize a passing site."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import verify_site_artifacts as verifier


def inventory(site):
    return {p.relative_to(site).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in site.rglob("*") if p.is_file()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True, type=Path)
    parser.add_argument("--baseurl", default="/cherrilang.org")
    parser.add_argument("--source-root", type=Path,
                        default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--evidence-out", required=True, type=Path)
    args = parser.parse_args()
    site = args.site.resolve()
    root = args.source_root.resolve()
    baseline = verifier.verify(site, root, args.baseurl)
    before = inventory(site)
    records = []
    def rejected(name, path, mutate, expected):
        original = path.read_bytes()
        try:
            changed = mutate(original)
            if changed == original:
                raise RuntimeError("Mutation did not change the actual artifact: " + name)
            path.write_bytes(changed)
            try:
                verifier.verify(site, root, args.baseurl)
            except RuntimeError as error:
                if expected not in str(error):
                    raise RuntimeError("Wrong rejection for " + name + ": " + str(error)) from error
                records.append({"name":name, "rejected":True, "diagnostic":str(error)})
            else:
                raise RuntimeError("Damaged built artifact was accepted: " + name)
        finally:
            path.write_bytes(original)
    search = site / "assets/js/search-data.json"
    def legacy(raw):
        data = json.loads(raw)
        data["synthetic-historical-control"] = {
            "title":"Historical control", "content":"Legacy syntax",
            "relUrl":"/language/raw-actions",
            "url":args.baseurl + "/language/raw-actions"}
        return json.dumps(data).encode()
    def wrong_base(raw):
        data = json.loads(raw)
        key = next(iter(data))
        data[key]["url"] = data[key]["relUrl"]
        return json.dumps(data).encode()
    rejected("historical-route-in-default-search", search, legacy,
             "Default search includes a historical route")
    rejected("search-result-without-project-base", search, wrong_base,
             "Search result URL does not match its project-base route")
    rejected("client-search-request-without-project-base", site / "assets/js/just-the-docs.js",
             lambda raw: raw.replace((args.baseurl + "/assets/js/search-data.json").encode(),
                                     b"/assets/js/search-data.json"),
             "Search client does not load and use the verified project URLs")
    rejected("missing-home-authoring-entry", site / "index.html",
             lambda raw: raw.replace(b'id="start-authoring"',b'id="removed-authoring-control"'),
             "Home page lacks its unique current-guide entry point")
    rejected("missing-home-image", site / "index.html",
             lambda raw: raw.replace(b"/assets/cherri_icon.png",b"/assets/missing-control.png"),
             "Built site is missing a unique page")
    action = site / baseline["renderedActionPage"]
    fingerprint = baseline["schemaFingerprints"][0].encode()
    rejected("damaged-canonical-action-fingerprint", action,
             lambda raw: raw.replace(fingerprint,b"0"*64),
             "rendered action page lost canonical metadata")
    if inventory(site) != before:
        raise RuntimeError("Negative controls did not restore the exact built artifacts")
    restored = verifier.verify(site, root, args.baseurl)
    if restored != baseline:
        raise RuntimeError("Restored site receipt differs from its verified baseline")
    receipt = {"formatVersion":1,"docsCommit":baseline["docsCommit"],
               "compilerCommit":baseline["compilerCommit"],"passed":len(records),
               "failed":0,"skipped":0,"artifactsRestoredExactly":True,"controls":records}
    args.evidence_out.write_bytes((json.dumps(receipt,indent=2)+"\n").encode())
    print(json.dumps(receipt,indent=2))


if __name__ == "__main__":
    main()
