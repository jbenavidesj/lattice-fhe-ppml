# Paper 1 — benchmark protocol

No headline performance result is asserted by this protocol.

## Comparisons
Compare the same mathematical operation and input distribution across:
1. a simple auditable reference (canonical remainder or schoolbook negacyclic multiplication);
2. the optimized candidate (AsymRed or NTT/RNS path);
3. where appropriate, a recognized implementation with matching semantics and parameters.

Do not compare different ring dimensions, modulus sizes, security levels, operation counts, or compiler settings as if equivalent.

## Environment and procedure
Record CPU model/microarchitecture, cores, memory, OS/kernel, Rust compiler, target triple, optimization flags, dependency lockfile, source revision, command line, thread settings, and thermal/frequency conditions where available.

Use release builds. Perform multiple independent sessions. Report median and dispersion/confidence intervals, sample counts, and raw results. Separate setup/key generation from steady-state evaluation.

## Required groups
- AsymRed versus canonical remainder, same valid input range.
- Modular add/subtract/multiply.
- Forward/inverse negacyclic NTT.
- Schoolbook versus NTT polynomial multiplication.
- RNS basis conversion and CRT reconstruction.
- BFV encryption/decryption/multiplication/relinearization only after full-pipeline correctness tests.

## Reporting rules
- CI is for build and correctness gates, not headline performance.
- A debug-mode timing is not publishable benchmark evidence.
- A microbenchmark improvement is not an end-to-end BFV improvement.
- Do not claim 34% or any other speedup without repeated release measurements and statistical reporting.

## Current implementation status
A Rust arithmetic prototype and Python parameter/AsymRed/polynomial checks are now checked into this branch. The CI workflow compiles/tests the Rust crate and executes Python audits. The benchmark executable is intentionally exploratory; no performance claim is supported until a dedicated release benchmark campaign is run.
