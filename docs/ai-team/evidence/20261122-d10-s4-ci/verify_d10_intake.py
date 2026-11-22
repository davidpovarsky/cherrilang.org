import ast, collections, hashlib, json, pathlib, re, zipfile
root = pathlib.Path(__file__).resolve().parent
source = "03431e9114211c1093b330d5fbaec3a4855ee867"
compiler = "b791ce0616d1821cebfc57909a6bc50a195ca68c"
def sha(data): return hashlib.sha256(data).hexdigest()
source_blobs = {"smoke_test_snippets.source.py":"ce7e47ed5dc5ba40a28894d675b5fc9c41de98c8", "test_smoke_test_snippets.source.py":"72b56c2730d95681cda353a955cc6b1060bbf469", "docs-smoke-test.source.yml":"a8925fe8150dad1e7ccad617803b01f49ce4db9e"}
for name, expected_blob in source_blobs.items():
    raw = (root/name).read_bytes()
    assert hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest() == expected_blob
e = json.loads((root/"cherri-docs-evidence.json").read_bytes())
assert e["compilerCommit"] == compiler and e["passed"] is True
executed = [r for r in e["records"] if r["executed"]]
assert len(executed) == e["executed"] == 39
assert all(r["passed"] is True for r in executed)
kinds = dict(collections.Counter(r["classification"] for r in executed))
assert kinds == {"runnable":36,"diagnostic":3}
assert len(e["records"]) == 563 and e["referenceOnly"] == 524
assert len({(r["file"],r["block"]) for r in e["records"]}) == 563
for r in executed:
    assert len(r["sourceSha256"]) == 64
    if r["classification"] == "runnable":
        assert r["checkExit"] == r["compileExit"] == 0
        assert len(r["unsignedSha256"]) == 64
    else:
        assert r["checkExit"] != 0 and r["compileExit"] != 0
        assert r["expectedErrors"] == r["actualErrors"]
log = (root/"smoke-job-original.log").read_text(encoding="utf-8")
tree = ast.parse((root/"test_smoke_test_snippets.source.py").read_text())
expected = sorted(n.name for c in tree.body if isinstance(c,ast.ClassDef) and c.name=="SmokeProductionTests" for n in c.body if isinstance(n,ast.FunctionDef) and n.name.startswith("test_"))
actual = re.findall(r"(test_\w+) \(__main__\.SmokeProductionTests\.\w+\) \.\.\. ok",log)
assert len(expected) == len(actual) == 12 and sorted(actual) == expected
assert "Ran 12 tests in 37.553s" in log
witnesses = [json.loads(line.split("CACHE_SOURCE_WITNESS ",1)[1]) for line in log.splitlines() if "CACHE_SOURCE_WITNESS " in line]
assert len(witnesses) == 18
leases = collections.defaultdict(dict)
for w in witnesses:
    if w["event"] in ("acquire","release"):
        assert w["event"] not in leases[w["case"]]
        leases[w["case"]][w["event"]] = w
        st=w["sourceState"]
        assert st["revision"] == compiler and st["status"] == ""
        assert st["origin"] == "https://github.com/davidpovarsky/cherri.git"
        if w["event"] == "acquire": assert w["binarySha256"] == e["binarySha256"]
assert len(leases) == 6
for pair in leases.values():
    assert set(pair) == {"acquire","release"}
    assert pair["acquire"]["sourceState"] == pair["release"]["sourceState"]
site = json.loads((root/"cherri-docs-site-evidence.json").read_bytes())
controls = json.loads((root/"cherri-docs-site-controls.json").read_bytes())
for v in (site,controls):
    assert v["docsCommit"] == source and v["compilerCommit"] == compiler
assert site["sourceTreeClean"] and not site["sitePublished"]
assert site["sourceReferenceSha256"] == "d1a5dfe3762109caeb7ddf8e1beaba5f17de4b5231de342ce99fa039d76090cd"
assert site["nativeActionCount"] == 505 and site["renderedReferenceSignatures"] == 520
assert site["searchEntries"] == 50 and site["actionSearchEntries"] == 21
assert site["verifiedLocalLinks"] == 87 and site["historicalSearchEntries"] == 0
assert (controls["passed"],controls["failed"],controls["skipped"]) == (6,0,0)
assert controls["artifactsRestoredExactly"] is True
assert len(controls["controls"]) == len({c["name"] for c in controls["controls"]}) == 6
assert all(c["rejected"] is True and c["diagnostic"] for c in controls["controls"])
with zipfile.ZipFile(root/"d10-docs-built-site.zip") as z:
    assert len(z.namelist()) == 94 and len(set(z.namelist())) == 94
    assert sha(z.read("cherri-docs-site/"+site["renderedActionPage"])) == site["renderedActionPageSha256"]
    assert sha(z.read("cherri-docs-site/assets/js/search-data.json")) == site["searchIndexSha256"]
result = {"schema":"cherri.d10-independent-ci-intake/v1","status":"PASS","workflowRun":44967399674,"attempt":1,"docsSource":source,"compilerSource":compiler,"binarySha256":e["binarySha256"],"snippets":{"executed":39,"runnable":36,"diagnostic":3,"referenceOnlyUnexecuted":524},"cacheControls":{"actualPassed":12,"names":expected,"elapsedSeconds":37.553,"sourceWitnesses":18,"cleanMatchedAcquireReleasePairs":6},"site":{"nativeActions":505,"referenceSignatures":520,"searchEntries":50,"actionSearchEntries":21,"verifiedLocalLinks":87,"corruptionControlsPassed":6,"artifactsRestoredExactly":True,"sitePublished":False},"originalFiles":{p.name:{"bytes":p.stat().st_size,"sha256":sha(p.read_bytes())} for p in sorted(root.iterdir()) if p.is_file() and p.name not in ("independent-review.json","verify_d10_intake.py")},"scope":"Actual GitHub CI snippet compilation/cache controls and built-site verification only. No Apple runtime, published Pages, S4 generation replay, final consumer promotion or full179 acceptance credit."}
(root/"independent-review.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(result,ensure_ascii=False))
