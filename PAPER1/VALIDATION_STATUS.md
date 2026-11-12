# Paper 1 — validation status

**Status: research prototype; not submission-ready.** This ledger distinguishes the small-ring BFV demonstration from the N=8192 RNS arithmetic candidate and from a complete cryptographic implementation.

## Selected architecture
- Core target: leveled RNS-BFV.
- Refresh/bootstrapping remains a separate experimental extension, not a required core feature.
- Arithmetic foundation: modular operations, AsymRed candidate, schoolbook negacyclic multiplication, twisted negacyclic NTT, four-lane RNS operations, exact coefficient-wise CRT reconstruction, centered basis extension, exact BigInt BFV t/Q scale-and-round, and an unrelinearized three-component RNS tensor-multiplication reference.
- A separate tiny-ring BFV model now exercises key generation, public-key encryption, decryption, homomorphic addition, unrelinearized tensor multiplication over centered integer lifts, with scale-and-round residual bounded coefficientwise by 1/2, and toy gadget relinearization. It is not integrated with the N=8192 RNS basis.

## Reproducible checks in the repository
- Parameter audit: deterministic Miller–Rabin checks for the four 64-bit q candidates, q_i congruence, exact 2N root order, pairwise coprimality, Q bit length, and log2(Delta).
- AsymRed: Python arbitrary-precision differential test and Rust tests, with the two-fold range bound checked at runtime.
- Polynomial arithmetic: Rust schoolbook negacyclic reference tests and a deterministic Python small-ring reference test.
- NTT: Rust round-trip tests at N=8192 for all four candidate moduli and a small-ring NTT-vs-schoolbook product test.
- Toy BFV: fixed-vector and deterministic multi-seed tests for encrypt/decrypt and addition at N=8, q=65537, t=17; tensor multiplication and relinearization tests at N=8, q=1099511627873, t=17, using centered ciphertext-component lifts and integer tensor products before scale-and-round. An exact-rational worst-case bound for one multiplication plus relinearization, including input noise and lift/quotient terms, is checked by `scripts/audit_toy_bfv_noise.py`. Relinearization is tested with gadget bases 2, 4, and 16. A conservative toy-only key-switch error bound is documented in `PAPER1/BFV_TOY_SPEC.md`.

Consult the latest GitHub Actions run for its actual state; do not infer a pass from the existence of a workflow.

## Not established
- A production RNS evaluation-key generator with secure uniform sampling and a specified error distribution. A deterministic sparse test fixture constructs nonzero-error RNS evaluation-key digits and checks the exact phase delta for a nontrivial secret. It also checks the observed centered coefficient infinity norm against the conditional bound L(B-1) max_j ||e_j||_1. This is a correctness fixture only, not a cryptographic sampler. CI run 178 for code commit b2a7e58 reports Python audits, Rust formatting, unit tests, and Clippy successful; benchmark-target compilation is still in progress.
- Full BFV implementation over the N=8192 four-lane RNS parameter candidates; current RNS tensor multiplication is a correctness-oriented BigInt reference map and has no integrated key switching/relinearization.
- Generalized end-to-end RNS key-switch correctness beyond the deterministic sparse fixture; the fixture now checks the observed centered coefficient infinity norm against the conditional bound L(B-1) max_j ||e_j||_1, but no production key generator or sampler exists.
- Production-grade gadget decomposition/relinearization and key switching, modulus switching, or bootstrapping.
- A proof of correctness for arbitrary multiplicative depth or for the N=8192 RNS parameter candidates.
- RLWE security estimate or 128-bit security.
- Cryptographically secure randomness or a production-grade error sampler in the toy model.
- Constant-time behavior or side-channel resistance.
- Any headline performance improvement, including 34% or the earlier 4.12 ms versus 2.71 ms figures.

AsymRed is exact modular reduction; it does not intrinsically reduce cryptographic noise. The toy BFV module uses deterministic test-only sampling and must never be used to protect real data.

## Important benchmark caution
The Criterion executable is an exploratory microbenchmark. It is compiled in CI but no release benchmark campaign, raw timing dataset, confidence intervals, CPU/compiler metadata, or end-to-end BFV measurement has been published. Debug-mode timing is not publishable evidence. No speedup claim is supported.

## Remaining gates before IEEE submission
1. Expand toy BFV multiplication and relinearization tests to exhaustive/boundary plaintexts and independent implementations; preserve the exact one-multiplication proof assumptions.
2. Replace the toy gadget/key-switch construction with a production-oriented design and formally bound its key-switch error.
3. Replace the current exact-CRT scale-and-round reference with a fast, proven RNS scale-and-round algorithm; add independent end-to-end RNS BFV multiplication vectors and a complete RNS noise proof.
4. Specify secure randomness and error samplers; run a current lattice estimator with recorded version and cost model.
5. Benchmark release builds on documented hardware with repeated samples and raw data.
6. Review constant-time behavior, side-channel exposure, and independent reproducibility.

Until those gates are passed, describe this as an arithmetic/RNS prototype plus a separate tiny-ring BFV correctness model—not as a validated new FHE scheme.


- Experimental CSPRNG-backed key generation added in `src/keygen.rs` using `getrandom 0.2.15`; includes unbiased per-lane uniform sampling, ternary secret sampling, eta=2 centered-binomial errors, and gadget evaluation-key construction.
- Tests added for sampler output ranges/supports, signed CRT-lane encoding, and sampled phase-relation coefficients of generated evaluation keys. These tests must pass CI before being considered validated.
- Still outstanding: exhaustive relation checks, zeroization, side-channel review, RLWE security estimation, independent cryptographic review, and the complete BFV noise/decryption proof.
