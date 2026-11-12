# Paper 1 — validation status

**Status: research prototype; not submission-ready.** This ledger distinguishes checks actually executed in the repository from missing cryptographic evidence.

## Selected architecture
- Core: leveled RNS-BFV.
- Refresh/bootstrapping remains a separate experimental extension, not a required core feature.
- Arithmetic prototype: modular operations, AsymRed candidate, schoolbook negacyclic multiplication, twisted negacyclic NTT, four-lane RNS operations, and exact coefficient-wise CRT reconstruction.
- Candidate optimizations are not, by themselves, evidence of speed or security improvements.

## Reproducible checks now in the repository
The branch includes a Rust crate and Python audit scripts. The latest GitHub Actions run should be consulted for its final state; do not infer a pass from the existence of a workflow.

- Parameter audit: deterministic Miller–Rabin checks for the four 64-bit q candidates, q_i congruence, exact 2N root order, pairwise coprimality, Q bit length, and log2(Delta).
- AsymRed: Python arbitrary-precision differential test and Rust tests, with the two-fold range bound checked at runtime.
- Polynomial arithmetic: Rust schoolbook negacyclic reference tests and a deterministic Python small-ring reference test.
- NTT: Rust round-trip tests at N=8192 for all four candidate moduli and a small-ring NTT-vs-schoolbook product test.

## Not established
- Full BFV key generation, encryption, decryption, ciphertext multiplication, scale-and-round, gadget decomposition, relinearization, modulus switching, and end-to-end correctness.
- A complete proof of the BFV noise bound for the implemented parameter set.
- RLWE security estimate or 128-bit security.
- Constant-time behavior or side-channel resistance.
- Validated bootstrapping/refresh.
- Any headline performance improvement, including 34% or the earlier 4.12 ms versus 2.71 ms figures.

AsymRed is exact modular reduction; it does not intrinsically reduce cryptographic noise.

## Important benchmark caution
The executable in `benches/arithmetic.rs` is an exploratory microbenchmark. A timing observed during debug test execution is not a release benchmark and must not be quoted. Run it in release mode on documented hardware, across repeated sessions, and compare distributions before making any performance statement. The CI runner is for correctness/build gates, not a headline speed claim.

## Remaining gates before IEEE submission
1. Complete and test the BFV encryption/evaluation/decryption pipeline.
2. Prove scale-and-round, key-switching/relinearization correctness, and a conservative noise bound for exact parameters.
3. Specify secret/error distributions and samplers; run a current lattice estimator with recorded version and cost model.
4. Benchmark release builds on documented hardware with repeated samples and raw data.
5. Review constant-time behavior and side-channel exposure.
6. Add independent review and a complete paper/reproducibility package.

Until then, present this as an arithmetic prototype supporting a candidate RNS-BFV design, not as a validated new FHE scheme.
