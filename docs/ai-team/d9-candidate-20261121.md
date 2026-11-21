# D9 candidate: exact S3 build, generation and cache/snippet evidence

Tested compiler S3: 9c8daf721aa241127df8d1e3f91bbadf90110e73.
Tested documentation source D9: f93bfd0db1fd2b99fc2b9eaacf48a2310ab236b6.
This report is a proof-only descendant. The candidate docs pin remains the exact
tested source above; this proof commit has a separate evidence identity.

## Actual component results

On 21 November 2026 at 22:12:45–22:15:22 UTC, the fixed source completed all
12 cache controls in 124.625 seconds and all 39 smoke examples in 17.859 seconds.
Both stages retained their original 180-second budgets. The examples comprise
36 runnable checks and 3 exact expected diagnostics. All 18 fixed source-lease
witnesses reconciled: six independent case caches used one genuine ordinary
checkout exclusively, verified pristine identity before/after, and returned
the same tracked/index/flag/go.mod state. Both same-byte replacement controls
rejected changed file identity without modifying the replacement. Compiler and
wrong-revision binary hashes remained unchanged; source and docs stayed clean.
No compiler build was performed in this cache/snippet run.

The earlier S3 build used a genuine ordinary clone, exact VCS revision and
vcs.modified=false. Actual compiler SHA256:
cd38fbc67d27531a616d11194dab148f0dfca6f0451d055894215ec5216f6761.
Actual migrator SHA256:
cf64c9821b5715b17c6659defe492fa05dd73872363a47d5e355efcf3f423ae5.
Fresh generation/check and four contract parents with eight causal drift
controls passed. The complete 505 native plus 15 separately fingerprinted macro
signatures reproduce the unchanged reference body SHA256
8f8a953a14fd65c9bfe6024ea065524d76a8f0549bd1d2e45502cda00dd4d0be.
The first compiler build's 180-second timeout remains separate from the
authorized successful second attempt with the same flags and deadline.

## Original failure and scoped repair

The original D9 cache attempt at 902086e reached 11 completed tests and timed out
at 180 seconds while preparing its last ordinary checkout. The wrong-binary
assertion had not completed and all 39 smoke examples were unstarted. Its full
raw output, owned-process termination and read-only partial-checkout diagnosis
are retained. The failure has not been relabeled as a successful run.

The repair leases one ordinary source checkout exclusively. It retains fresh
per-case binaries/receipts/output, full pristine checks, exact known
compensation and independent wrong-binary/fault-cause controls. File and parent
directory identities prevent compensating a replaced same-byte object.
No production cache validator, contract or budget was relaxed.

## Reviewable originals and remaining gates

The [145-member original evidence archive](evidence/20261121-d9-candidate/originals.zip)
and [source/member bindings](evidence/20261121-d9-candidate/bindings.json)
retain original build attempts, generation, cache timeout, successful 12/39 run,
all subprocess stdout/stderr, source versions and complete snippet receipts.
Only executable binaries remain host-local; their original build/VCS identity
and byte hashes are included. Archive SHA256:
6b0d3a8f35534f87753d99b2514bbf028c59f6d20463369bd51fe3d489239b22.

Successful 12/39 process receipt SHA256:
3253cda6455b0105a5de077a60f3483c30dcaf652b1c50207dd838f628208634.
Cache stderr SHA256:
6336ab130a5b7a17cc5f8f5a933cf21d6e334ad677cd4ae5d7fea590e848b37f.
Cache 18-witness stdout SHA256:
34134f154059e8991f6d1aa0534a24c56cd687db0b829c15d4834f664ed05c8c.
Complete 39-snippet receipt SHA256:
87f05aa6221ecb11c07bdf390246f7483bbbfc42b82126ec2a0b51a357ce307e.
Original failed cache receipt SHA256:
192c61a845ad111b1cbd805bd9cb57aea41f40c987534487301c3821fd9c8db5.

This is component candidate evidence. Docs main remains D8. Exact-source CI,
Pages/live-byte publication, installed consumers and the joined documentation
requirements remain separate gates. It establishes neither Apple runtime
success nor final 179 requirement closure.
