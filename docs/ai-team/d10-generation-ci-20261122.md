# D10: actual S4 generation and original CI intake

The missing S4 documentation generation stage now has an actual successful execution and an independent reconciliation of its original evidence. This records the documentation candidate only. It does not promote Docs main or Pages, update installed consumer pins, grant Apple runtime credit, or complete the 179-requirement acceptance.

## Immutable execution

- Repository: `davidpovarsky/cherrilang.org`.
- Tested Docs source: `151111f7f67ed4980b243065fbd606a5902f734b`, parent `03431e9114211c1093b330d5fbaec3a4855ee867`.
- Compiler source: `b791ce0616d1821cebfc57909a6bc50a195ca68c`.
- Branch: `agent/cherri-p10r15-docs-d10-generation-ci-20261122`.
- [Original workflow run 44971464321](https://github.com/davidpovarsky/cherrilang.org/actions/runs/44971464321), attempt 1, automatically triggered by the source push. Created 2026-11-22 01:26:21 UTC; terminal SUCCESS 01:27:51 UTC.
- [Smoke/cache/generation job 137051965733](https://github.com/davidpovarsky/cherrilang.org/actions/runs/44971464321/job/137051965733) and [site job 137051965496](https://github.com/davidpovarsky/cherrilang.org/actions/runs/44971464321/job/137051965496) both succeeded.

The source delta is exactly two files: the new bounded `scripts/verify_generated_reference.py` and its explicit workflow stage/artifact upload. The original compiler pin, documentation content, snippet/cache controls, and site controls remain in the tested source. The acquisition invoked no local rerun or Windows job.

## Actual generation, check and fixed Go controls

| Actual operation | Result | Elapsed | Original bound |
| --- | --- | ---: | ---: |
| `go run -p=2 ./tools/language-docs <owned-output>` | PASS | 5.894063 s | 180 s |
| The same real CLI with `--check <owned-output>` | PASS | 0.064162 s | 180 s |
| Fixed generator Go controls, `-count=1 -json -timeout=60s` | PASS | 2.172201 s | 90 s supervisor, 60 s Go |

The generation report covers 01:27:36.081682–01:27:44.538540 UTC. Original stdout, stderr and terminal process receipts are retained for all 33 subprocesses, including source/cache observations. Every subprocess exited zero within its original bound, reported complete owned-group cleanup, and required no signal. The report, individual receipts and original CI `DOCS_GENERATOR_END` lines agree exactly.

The independent intake parsed all 52 original Go JSON events. Exactly these four parents and eight named corruption subtests ran and passed once, with one package start/terminal, no failures, skips, unexpected tests or missing terminals:

- `TestGeneratedReferenceIncludesSeparateMacroContracts`
- `TestP15D01PrimaryParameterContract`
- `TestP15D01AllGeneratedSignaturesAndCategories`
- `TestP15D01CheckGateProducesAndRejectsFaults`, including `optional_primary`, `typed_default`, `callable_identity`, `wire_key`, `return_type`, `macro_identity`, `missing_category`, and `extra_section`.

The immutable Go source independently fixes this inventory. Its check-gate parent builds the actual generator, produces a healthy reference, and requires each actual modified reference to be rejected without changing the caller's bytes. It does not substitute a test-computed reference for the original CLI output.

Original Go stream: 11,569 bytes, SHA256 `6bfe1f690eddaeaccf339dc4374f52da45fd1d85df180ed3c0a9f12126ce4490`.

## Complete reference and source identity

The complete fresh 243,289-byte generated reference equals both the canonical file at compiler S4 and the Docs action-reference body after its exact 119-byte frontmatter. This is full byte equality, including all 505 native action sections and 15 separately identified compiler macro sections, for 520 unique headings. Reference SHA256:

`8f8a953a14fd65c9bfe6024ea065524d76a8f0549bd1d2e45502cda00dd4d0be`

Before and after snapshots are identical. Original clean-status outputs include tracked, untracked and ignored state. The independent intake reconstructed the full stage/flag streams from the immutable GitHub trees and matched all 6,313 compiler and 101 Docs tracked entries. Eleven direct generation witnesses were also compared byte-for-byte with their immutable Git blobs, including both references, generator implementation/tests, module files, workflow and cache scripts.

The actual Linux compiler is 25,512,283 bytes, SHA256 `65042016b5c973d71a7409b844482d73d26e5dd6327f945f851915e5facdebc6`. Original `go version -m` outputs bind `vcs.revision` to S4 and `vcs.modified=false`. Binary hash, inode/size/mtime witness, cache receipt bytes, source indexes and source identities are unchanged across generation. This identifies the Linux binary used in this run; it is not a claim that a separately built Windows binary has the same bytes.

Generation report SHA256: `4bd995f371149962920e537f0cbfc600f4c5560452e7b273690df15554974798`.

## Other actual checks in the same run

The new run also retains 39 executed examples: 36 successful structured checks plus unsigned native-plist compilations, and three exact diagnostic/compile rejections. All 563 recorded source-block hashes were independently reconciled to immutable Docs bytes. The other 524 blocks are explicitly reference-only and were not executed.

All 12 real cache/provenance controls passed in 28.798 seconds. Eighteen original ownership/source witnesses contain six clean matching acquire/release pairs. Both same-byte replacement controls rejected the substituted file identity. These receipts bind the same S4 and actual Linux binary; the negative cases and their independent cache/output locations remain intact.

The actual built site contains 520 reference signatures, 50 search entries including 21 action entries, and 87 verified local links. All six site/search corruption controls rejected their faults and restored exact artifact bytes. Rendered action-page and search-index bytes match their receipt hashes. The built-site receipt explicitly says `sitePublished=false`.

## Original artifacts and reproducible intake

Every original ZIP was matched to the authenticated GitHub artifact API size, digest, run and source. All 200 members were extracted and independently rehashed.

| Original artifact | Bytes / members | SHA256 |
| --- | --- | --- |
| `14733458610`, `docs-generator-evidence` | 582,250 / 105 | `60d19f25bc050d51740636a9d1c97100aaadd77137e3af72fada705d2b087b07` |
| `14733852372`, `docs-snippet-evidence` | 25,791 / 1 | `df107d3e2a7bc9368b924ecaaad6f48be21e7f3956eb354c26d645cc7c19aa51` |
| `14733304387`, `docs-built-site` | 7,305,846 / 94 | `026c73d8568718ebcc2de8f56d95fac6eb07ca9097b67405f8ddc6093e89834c` |

Original decoded job-log hashes:

- Smoke/cache/generation, 52,244 bytes: `d2d1f90058fae3d2c826530e87cc3aa583923b2de7de5850f6670a84abace79e`.
- Site, 27,285 bytes: `eecc2627d1e65cb4a5fa54b6d5c19051e1136874f16dd889fe990b6f5d86e4a9`.

The proposed evidence archive is [d10-s4-generation-originals-20261122.zip](https://github.com/davidpovarsky/cherrilang.org/blob/841999480a4112ea0b2112d92c060a436a37ddf1/docs/ai-team/evidence/20261122-d10-s4-generation/d10-s4-generation-originals-20261122.zip), 8,820,169 bytes, SHA256 `f94f7ed148617d0b2e1eb5523a23378c0743940df054ae03b742891ac49020b9`. Its manifest binds 63 files plus the manifest itself; all 200 original artifact members remain inside the three unchanged original ZIPs. It includes original API/source carriers, decoded logs, source bytes, member inventories, the independent verifier, and its first successful process/stdout/stderr originals. Temporary download URLs are not part of the publication packet.

The first independent intake completed successfully in 0.315 seconds. Intake result SHA256: `4311210100db090fdab4591ca087e738f09936f3b2df0eb454281f8db7b6f9c7`. Verifier source SHA256: `97b2ae65910b022f144f703b09229eb90bdc48534c62fb033e3ad00b2d88fb1b`.

After unpacking the proof archive, `python3 restore_artifact_members.py` restores only the byte-verified original artifact members; `python3 verify_original_intake.py` reconciles the retained evidence. Neither command invokes a compiler, provider, Windows host or GitHub workflow.

## Publication disposition

This is a prepared evidence-only publication, based on the tested source `151111f7f67ed4980b243065fbd606a5902f734b`. Its proposed separate branch is `audit/cherri-p10r15-docs-d10-generation-proof-20261122`. The proof descendant must remain distinct from the tested source. Root review and publication reconciliation are still required. No source/pin/Docs main/Pages mutation has been performed by this intake, and no project or requirement completion is granted.


## Independent root review after the original draft

Root independently reviewed the complete verifier, repeated the originals-only intake, and fetched fresh GitHub jobs, artifacts, logs and commit/tree identities. All three artifact digests and both decoded job logs match. The compiler and Docs commits independently bind trees `cdd6e1606a75cd312f24ee060a92ce84ba863a1b` and `45b1ee0b29647016f1f4f5cc529b2b3be3c7b0f2`. An additional check verified nanosecond ordering and finite elapsed values for all 52 Go events. The repeated result is identical apart from its audit timestamp; there were no new test executions.

The original archive and first intake remain unchanged. The separate root result is `root-independent-intake.json`, SHA256 `206cd38afbe93218a4d51b36f23a76170f6db0403701b9aaf81e4c7044459806`; fresh independent readback is `root-readback-evidence.json`, SHA256 `1ae57cc50416f67e7408204da8b0fbd93f6036ba22a8b3001cfe487919ae4ceb`. Root approved an evidence-only commit on the new audit branch, based exactly on tested source151111f. Source/generation gates are unchanged; Docs main, Pages, final consumers and formal acceptance remain separate.
