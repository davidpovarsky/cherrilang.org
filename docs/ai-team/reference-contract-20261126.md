# Exact canonical reference inventory — 26 November 2026

The documentation verifier still required 15 compiler macros even though the actual committed compiler reference contains 16. The original verifier rejected the unmodified 505-action/16-macro reference. The repair preserves the full generated/compiler-source/Docs byte comparison and exact Jekyll frontmatter; it requires the ordered identities of all 16 macros, 505 native headings, 521 unique headings and the matching count headers.

## Actual qualification

The original RED process ran six Python test methods against the real committed compiler reference (SHA-256 0ceeff870174737de0d0bad90c3f26a1a09ab8d0bae2454893d132ee8c7acda7). It retained one healthy-case error and three diagnostic-stage failures. Its receipt is abaafae8cf98f80c18a3ffd1c6e243d0745b941f5ed566645f8f9d75f19b5d01. This fixture is an existing generated file; the run did not regenerate it or establish current generator freshness.

The repaired verifier passed all six methods using exactly the same test bytes. The tests cover the healthy reference and 12 causal mutations: foreign, duplicate, missing and reordered macros; missing and duplicated native headings; duplicate macro section; old macro count; wrong native count; compiler-reference byte drift; Docs-reference byte drift; and frontmatter drift. GREEN receipt: d19cd595dce34e534afec129a71e71de1fccb49fecff269f60e58031f38ef34f. Test SHA-256: 4faf6ddd441b05824e72d0cd2e2332ed3569610f4f7c8a9036dc2fb62255e128.

The published verifier differs from the qualified verifier only by adding this test file to the source-file inventory. Independent AST comparison verified that every other Python node is unchanged. Intake 48ada5b8571d9e1329fe1c906aa18fa1383c676e3855d3f1853fe337aba695a4 binds the six original passing method events, the fixture, the test source, both original runs and the exact published source. No successful run was repeated for the intake.

The fixed CI step executes the same Python controls after the canonical generator gate. The existing Go selection is unchanged. Source publication 5c83558695bfd8ebe3c3ece253f1eefd267f4418 joins the local implementation commit and an authorized GitHub workflow update as two parents; its tree is byte-identical to the tested implementation plus the fixed source inventory and workflow step. The initial OAuth workflow-scope push failure is retained. A normal non-force push then succeeded after the workflow update was published through the existing GitHub connection.

## Original evidence

[Original archive](evidence/reference-contract-20261126/originals.zip) and [member manifest](evidence/reference-contract-20261126/manifest.json) retain the RED/GREEN streams, test and verifier snapshots, actual reference fixture, publication failure/success and independent intake. Every member is SHA-256 bound to the original Oracle file. The archive contains public project material only.

## Remaining release gates

This component proves the reference validator. It does not advance the immutable compiler/reference pins, regenerate the reference, rerun the already qualified 46 CLI examples, publish the site, activate consumers or establish native runtime acceptance. The actual canonical generator and its --check must run on the selected compiler source; the resulting canonical Markdown must then be committed before the one final compiler/migrator pair is built. The Docs pin and generated body will bind that exact source, and the Skill/consumer pin will bind both source and Docs. Full pinned cache/snippet/site CI and original release gates remain required for the new tuple.
