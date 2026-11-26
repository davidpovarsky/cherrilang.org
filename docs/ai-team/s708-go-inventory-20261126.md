# S708 documentation Go event contract

The compiler source is [708ed78eda1cad0f1f453559afce100edc59b8a9](https://github.com/davidpovarsky/cherri/commit/708ed78eda1cad0f1f453559afce100edc59b8a9). Its original four documentation test parents now emit fourteen named test identities. The ten children of `TestP15D01CheckGateProducesAndRejectsFaults` include the source-authored `scoped_dialect` and `scoped_void_result` controls.

The original [Docs run 45745574747](https://github.com/davidpovarsky/cherrilang.org/actions/runs/45745574747) remains failed. On Docs source `c51812c39719d26828f9e672c92ca72dc84f7a29`, the original generator, `--check`, and all fourteen Go identities succeeded, but the Docs receipt verifier rejected the two new identities because its fixed inventory still contained twelve. The snippet/cache job steps and the complete Jekyll/search job succeeded independently.

This repair adds exactly those two source-witnessed identities and requires a complete fourteen-test execution. It retains all twelve historical identities, all four selected parents, the original Go command and time limits, unique run/pass requirements, timestamp and package checks, and child-before-parent ordering. It does not accept arbitrary extra events or learn expected identities from a passing stream.

The actual original process JSON and JSONL are committed as fixtures. Five focused Python methods validate that stream and eight causal changes: each new child is independently removed, renamed to a foreign identity, duplicated, or moved after its parent's terminal. The unmodified new tests failed against the old twelve-identity admission, then all five methods and eight fault cases passed after the verifier repair. The first GREEN wrapper receipt remains `UNEXPECTED_RESULT` because its own footer check accidentally searched for literal backslash characters; the process itself exited zero and printed the exact five successful method names and `OK`. An independent receipt checks those original bytes without rerunning the suite.

| Original | SHA-256 |
| --- | --- |
| Compiler `tools/language-docs/p15_contract_test.go` | `ea5a3ca1228f144af51aa0f4aa4cc8a86f8cf4eb58951a80db8ea3aa1648c7e3` |
| Actual Go JSONL | `96bd2bac51ece5f7d18793038e23bb1da12500894315339f5b98307e885b82ae` |
| Actual Go process receipt | `34be61664c09971b43229c64c1ca7a70ebf01ee19a070bc87b6b014d4147fe59` |
| Original failed CI acquisition | `ef360be701f8f3ade3392fa9ea5e733c5d8609dd85cc3a7991d648bf1b5c15a2` |
| Focused RED receipt | `66e9ca8f52090ac353829340bfb52af11a2434cc05fab9480a87c7872719a295` |
| Preserved GREEN wrapper receipt | `1aaad15290da55cd8eb49ac2dec629675f1b003f547ba3b016fd2d40d98910ed` |
| Independent component intake | `2375cf4397d3e5e09fe946bfd506e4ca5047fd0fd9bad722e8995629c6ab2fbd` |

Originals are under `/mnt/development/projects/evidence/cherri-p10r15-consumer-final-alignment-20261126/docs-S708-ci-acquisition-01` and the adjacent `docs-fixed14-*` directories. The newly pinned documentation still requires a full successful CI run at its corrected source before final promotion. No Apple runtime, live installation, main publication, or full179 acceptance is granted by this component.
