# Paper 1 — validation status

**Status: research prototype; not submission-ready.** This ledger distinguishes the small-ring BFV demonstration from the N=8192 RNS arithmetic candidate and from a complete cryptographic implementation.

## Selected architecture
- Core target: leveled RNS-BFV.
- Refresh/bootstrapping remains a separate experimental extension, not a required core feature.
- Arithmetic foundation: modular operations, AsymRed candidate, schoolbook negacyclic multiplication, twisted negacyclic NTT, four-lane RNS operations, exact coefficient-wise CRT reconstruction, and centered basis extension.
- A separate tiny-ring BFV model now exercises key generation, public-key encryption, decryption, and homomorphic addition for fixed deterministic test vectors. It is not integrated with the N=8192 RNS basis.

## Reproducible checks in the repository
- Parameter audit: deterministic Miller–Rabin checks for the four 64-bit q candidates, q_i congruence, exact 2N root order, pairwise coprimality, Q bit length, and log2(Delta).
- AsymRed: Python arbitrary-precision differential test and Rust tests, with the two-fold range bound checked at runtime.
- Polynomial arithmetic: Rust schoolbook negacyclic reference tests and a deterministic Python small-ring reference test.
- NTT: Rust round-trip tests at N=8192 for all four candidate moduli and a small-ring NTT-vs-schoolbook product test.
- Toy BFV: unit tests for fixed-seed encrypt/decrypt and homomorphic addition at N=8, q=65537, t=17. The exact equations and limitations are in `PAPER1/BFV_TOY_SPEC.md`.

Consult the latest GitHub Actions run for its actual state; do not infer a pass from the existence of a workflow.

## Not established
- Full BFV implementation over the N=8192 four-lane RNS parameter candidates.
- Production-grade gadget decomposition/relinearization and key switching, modulus switching, or bootstrapping.
- A complete proof of the BFV noise bound for the implemented parameter set.
- RLWE security estimate or 128-bit security.
- Cryptographically secure randomness or a production-grade error sampler in the toy model.
- Constant-time behavior or side-channel resistance.
- Any headline performance improvement, including 34% or the earlier 4.12 ms versus 2.71 ms figures.

AsymRed is exact modular reduction; it does not intrinsically reduce cryptographic noise. The toy BFV module uses deterministic test-only sampling and must never be used to protect real data.

## Important benchmark caution
The Criterion executable is an exploratory microbenchmark. It is compiled in CI but no release benchmark campaign, raw timing dataset, confidence intervals, CPU/compiler metadata, or end-to-end BFV measurement has been published. Debug-mode timing is not publishable evidence. No speedup claim is supported.

## Remaining gates before IEEE submission
1. Expand toy BFV multiplication and relinearization tests across seeds, gadget bases, and boundary plaintexts; prove conservative noise bounds for the exact sampling models.
2. Replace the toy gadget/key-switch construction with a production-oriented design and formally bound its key-switch error.
3. Port the verified multiplication/relinearization pipeline to N=8192 RNS and test against independent references.
4. Specify secure randomness and error samplers; run a current lattice estimator with recorded version and cost model.
5. Benchmark release builds on documented hardware with repeated samples and raw data.
6. Review constant-time behavior, side-channel exposure, and independent reproducibility.

Until those gates are passed, describe this as an arithmetic/RNS prototype plus a separate tiny-ring BFV correctness model—not as a validated new FHE scheme.
