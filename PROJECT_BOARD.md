# Project Board

This is a living working-memory document for this repository.
It is intentionally lightweight. Humans and coding agents should update it when useful discoveries, ideas, plans, optimizations, problems, or follow-up work arise during normal development.
Do not turn this into a duplicate issue tracker or a dump of temporary thoughts.

## Inbox

Quick captures that still need classification.

## Ideas & Opportunities

Potential improvements, features, optimizations, or architectural ideas.

## Discoveries & Tips

- 2026-11-23: A new compiler source needs fresh immutable pins in both snippet and generated-reference consumers. The current six generator/reference input files are byte-identical to the accepted D14/S79 input set, so preserve the reference body and let the unchanged generator/check/cache/snippet/site gates validate the newly selected source. D14 remains its original S79 publication; D15 candidate and main/Pages evidence must identify the new compiler and Docs commits. Preserve the D10 archive exclusion and immutable historical link; no old artifact or success is relabelled.

- 2026-11-23: Jekyll copied the historical D10 proof ZIP into each site artifact. Its retained older site ZIP contains further ZIPs, producing a depth-four public archive chain beyond the unchanged CI04 depth-three bound. The candidate site configuration excludes only that D10 ZIP; the archive stays byte-identical in Git and the D10 note links to its immutable D13 repository copy. Preserve complete historical artifacts and validate the new candidate/publication; do not hide nested archives from intake or relax the bound.

- 2026-11-21: Exact D9 source f93bfd0db1fd2b99fc2b9eaacf48a2310ab236b6 passed all 12 actual cache controls (124.625s), all 39 snippets (36 runnable/3 diagnostic,17.859s), and 18 fixed ownership/restore witnesses under the unchanged 180s stage limits. Source and binaries stayed exact/clean. The original 11/12 timeout remains preserved. [The component proof](docs/ai-team/d9-candidate-20261121.md) binds original build/generation/cache/snippet evidence; this proof-only descendant does not change the tested source pin or promote Docs main/Pages/final consumers.

- 2026-11-21: The first S3/D9 local cache gate reached 11 completed controls but timed out at the unchanged 180-second limit while creating the last ordinary checkout, before the wrong-binary assertion and before all 39 snippets. Original raw output, partial checkout and timeout are retained. The draft test fixture now leases one real, fully checked ordinary source checkout exclusively into each case's independent cache; binaries and receipts remain separate. Exact owned source mutations are restored before full pristine checks and return, with acquire/release witnesses and fail-closed state-leak detection. This source change still needs review and an actual bounded replay; it does not turn the original timeout into a PASS.

- 2026-11-21: D9 draft binds the immutable documentation compiler pin to candidate 9c8daf721aa241127df8d1e3f91bbadf90110e73. A clean ordinary clone produced compiler and migrator binaries with this exact VCS revision and vcs.modified=false. Fresh canonical generation, the complete reference check, and four contract tests with eight actual drift controls passed; the 505 native and 15 macro signatures reproduce the existing reference body byte-for-byte (SHA256 8f8a953a14fd65c9bfe6024ea065524d76a8f0549bd1d2e45502cda00dd4d0be), so Jekyll frontmatter and reference bytes remain unchanged. The first 180-second compiler build timeout is retained separately; the authorized second attempt used the same flags and deadline. This draft still requires fresh cache/snippet gates, exact-commit CI, publication and consumer evidence. It does not establish Apple runtime or final project acceptance.

- 2026-11-19: The fork repository had no enabled Pages site and still carried upstream's CNAME, homepage examples, playground links, and default search. The fork deployment uses its own GitHub project URL; active navigation/search are restricted to the current fork guide. Historical routes remain explicit reference links. Verify actual rendered links at the configured base URL and run negative controls on the built search artifact before publishing.

- 2026-11-19: A cold GitHub runner exceeded the former universal 180-second subprocess limit while building the pinned Go compiler (run 44453561234); examples had not started. Only Go build now receives a 600-second deadline, with two build workers and a 20-minute job ceiling. Other commands and each example retain 180 seconds. Validate this change on a cold CI runner before treating the docs job as passed.

- 2026-11-19: The locked public_suffix 7.0.5 dependency requires Ruby >= 3.2 (https://rubygems.org/gems/public_suffix/versions/7.0.5). The site-build and Pages workflows now share Ruby 3.3 / Bundler 2.5.11 and install the frozen Gemfile.lock. Do not resolve new dependency versions during a release build. The feature-branch build verifies the rendered action reference and search index, and retains the built site for review.

- 2026-11-18: GitHub runner context is unavailable in jobs.<job_id>.env and is available in steps.env. Bind compiler cache paths at their consuming steps; otherwise workflow validation can fail before any job or log exists. Official context table: https://docs.github.com/en/actions/reference/workflows-and-actions/contexts#context-availability . Preserve the local snippet result separately from a GitHub workflow result.

Useful technical discoveries, undocumented behavior, shortcuts, implementation tricks, platform behavior, or reusable knowledge discovered while working.

## Experiments / Investigations

Things worth testing or researching before deciding whether to implement them.

## Open Questions

Important unresolved questions or uncertainties.

## Planned / Todo

Concrete work that is worth doing but is not part of the current task.

Use Markdown checkboxes where useful:

- [ ] Example item

## Done

- [x] 2026-11-19: Refreshed the compiler pin to 71225b71f5353a0f661722d154a8b670b52e76f6 and regenerated the complete canonical action reference from a clean ordinary compiler clone with VCS provenance. Preserved Jekyll frontmatter. The generated body has native schema fingerprint 7bfff2b8c3fddf3892e943ef45b79bbbc4cc984ad051a15099a5da0fc6fccc0b, 505 native actions and 15 separately fingerprinted macros. The resulting docs commit must pass the 37 snippet checks, 12 cache controls and the new Jekyll/search-artifact gate; the CI artifacts bind their evidence to the actual compiler/docs commits. This source update does not publish the site or establish Apple runtime acceptance.

- [x] 2026-11-18: Refreshed the immutable compiler pin to a04c6feede79358ee642a1ae27f0a0da8f995ad7 and compared the complete canonical generated action reference while preserving Jekyll frontmatter. The native schema and macro fingerprints remain unchanged. The 37 executable/diagnostic checks and 12 cache-provenance controls must bind to this exact compiler and the resulting docs commit; their run receipts are retained with the staged compiler consumer evidence. Future compiler changes require this pin/reference refresh again. This does not publish the site or prove Apple runtime.

- [x] 2026-11-18: Replaced HEAD-only docs compiler cache trust with read-only source, VCS and binary-digest validation. Controlled baseline accepted an actual old compiler and deleted an unmanaged cache file; 12 actual controls now cover both failures and exact diagnostics. Existing occupied caches are preserved; the default versioned cache path starts fresh.
- [x] 2026-11-18: Extended executable coverage from the former 14 examples to 37 checks across the active guide, migration and retained V2 pages. Corrected unsupported time-trigger and incomplete migration examples. Two deliberate errors require exact diagnostic codes and no unsigned output. The 520 generated signatures and four labelled Legacy fragments are reference-only, with signatures validated separately by the complete compiler schema contract at f3e32df.
- [ ] After future compiler changes, refresh the immutable pin and generated reference together, rerun this CI and record its exact docs/compiler tuple. Local validation does not establish site publication or Apple execution.

- [x] 2026-11-18: Regenerated the fork action reference from compiler `d00bc0b9e9a4d8c460623de3d883680b94289e04` with the existing `tools/language-docs` generator, retaining Jekyll frontmatter. The source fingerprint is `f55851491e52ec9d06e486420f83d4faef0e31292d411235c01bf104bc48045d`. Updated the snippet compiler pin to the same immutable SHA. The real fetched and rebuilt compiler passed all 14 executable snippets and the invalid-syntax negative control. This is the first P10R15 validation tuple; refresh its pin if the integrated compiler candidate changes. Generated signature declarations are reference notation, separate from the executable snippet checks.

Completed items that are still useful to retain because they document an important decision, discovery, or implementation.

Example:

- [x] Example improvement
  - Implemented: YYYY-MM-DD
  - Commit/PR: ...
  - Notes: ...

## Archive

Older completed/superseded items that still have historical value.

- [x] 2026-11-18: Refreshed the existing canonical generator reference for compiler 17ba3ca3387f204a0fd80b092624e21f311db8d4. It contains 505 native catalog entries and 15 separately fingerprinted compiler macros. Preserved site frontmatter and all reconciled main history. The exact compiler was fetched, SHA-verified and rebuilt by scripts/smoke_test_snippets.py: 14 executable snippets passed static check and unsigned compilation, and the invalid-syntax negative control was rejected. Native action fingerprint 6eb0ef0129bba916af7cfdeae85bdbb2e42245390ccaa1137670aeb46cb62cce; macro fingerprint 1fe7f7993e2473aec591341712f42c521f913974b8e84091a5c2950232230dec. This is a staged P10R15 consumer tuple; no published site or live consumer deployment is claimed.

- [x] 2026-11-21: Refreshed the active documentation compiler pin to c46902bbe6cf7d0d8a6f5acd2d776eb1f77c7262 after a clean ordinary-clone build. Fresh canonical generation and the generator check gate reproduce the complete existing committed reference byte-for-byte (SHA256 8f8a953a14fd65c9bfe6024ea065524d76a8f0549bd1d2e45502cda00dd4d0be), preserving Jekyll frontmatter and all D7 executable and explicit Legacy corrections. The compiler reports 505 canonical actions, 15 separately fingerprinted macros, and codec fingerprint eb550a69bd2e0413369d6b0c0863448c755724b4103c5e4a3617125a72ee3122. Site CI and coherent consumer acceptance are separate gates; this commit does not claim Apple runtime or final project closure.
