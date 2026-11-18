# Project Board

This is a living working-memory document for this repository.
It is intentionally lightweight. Humans and coding agents should update it when useful discoveries, ideas, plans, optimizations, problems, or follow-up work arise during normal development.
Do not turn this into a duplicate issue tracker or a dump of temporary thoughts.

## Inbox

Quick captures that still need classification.

## Ideas & Opportunities

Potential improvements, features, optimizations, or architectural ideas.

## Discoveries & Tips

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
