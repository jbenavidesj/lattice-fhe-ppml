# Paper 1 — validation status

**Status: research prototype; not submission-ready.** This ledger distinguishes the small-ring BFV demonstration from the N=8192 RNS arithmetic candidate and from a complete cryptographic implementation.

## Selected architecture
- Core target: leveled RNS-BFV.
- Refresh/bootstrapping remains a separate experimental extension, not a required core feature.
- Arithmetic foundation: modular operations, AsymRed candidate, schoolbook negacyclic multiplication, twisted negacyclic NTT, four-lane RNS operations, exact coefficient-wise CRT reconstruction, centered basis extension, exact BigInt BFV t/Q scale-and-round, and an unrelinearized three-component RNS tensor-multiplication reference. Experimental RNS public-key generation, encryption, decryption, homomorphic addition, and a multiply-then-relinearize API have now been added; the end-to-end integration test is being validated by CI.
- A separate tiny-ring BFV model now exercises key generation, public-key encryption, decryption, homomorphic addition, unrelinearized tensor multiplication over centered integer lifts, with scale-and-round residual bounded coefficientwise by 1/2, and toy gadget relinearization. It is not integrated with the N=8192 RNS basis.

## Reproducible checks in the repository
- Parameter audit: deterministic Miller–Rabin checks for the four 64-bit q candidates, q_i congruence, exact 2N root order, pairwise coprimality, Q bit length, and log2(Delta).
- AsymRed: Python arbitrary-precision differential test and Rust tests, with the two-fold range bound checked at runtime.
- Polynomial arithmetic: Rust schoolbook negacyclic reference tests and a deterministic Python small-ring reference test.
- NTT: Rust round-trip tests at N=8192 for all four candidate moduli and a small-ring NTT-vs-schoolbook product test.
- Toy BFV: fixed-vector and deterministic multi-seed tests for encrypt/decrypt and addition at N=8, q=65537, t=17; tensor multiplication and relinearization tests at N=8, q=1099511627873, t=17, using centered ciphertext-component lifts and integer tensor products before scale-and-round. An exact-rational worst-case bound for one multiplication plus relinearization, including input noise and lift/quotient terms, is checked by `scripts/audit_toy_bfv_noise.py`. Relinearization is tested with gadget bases 2, 4, and 16. A conservative toy-only key-switch error bound is documented in `PAPER1/BFV_TOY_SPEC.md`.

Consult the latest GitHub Actions run for its actual state; do not infer a pass from the existence of a workflow.

## Not established
- Production-secure RNS evaluation-key generation with a validated security level. An experimental OS-CSPRNG-backed sampler now constructs keys with an explicit ternary secret and eta=2 centered-binomial errors; exhaustive coefficientwise phase checks are in the current test suite. The implementation is not security-reviewed and no RLWE estimate is available.
- A fully validated RNS-BFV implementation over the N=8192 four-lane candidates. Public-key encryption/decryption and addition are now wired through the experimental RNS key-generation module; multiply/relinearize is wired as an API but still needs an end-to-end plaintext-product test, full noise proof, and independent review.
- Complete end-to-end RNS BFV key-switch correctness with an integrated encryption/decryption pipeline and full multiplication noise proof; the isolated key-switch algebra and conditional error bound are tested, but full BFV integration is absent.
- Production-grade gadget decomposition/relinearization and key switching, modulus switching, or bootstrapping.
- A proof of correctness for arbitrary multiplicative depth or for the N=8192 RNS parameter candidates.
- RLWE security estimate or 128-bit security.
- Cryptographically secure randomness or a production-grade error sampler in the toy model. The experimental RNS key generator uses OS entropy but is not a production-security claim.
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


## Security, zeroization, and RNS noise proof gate

See PAPER1/SECURITY_AND_NOISE_REVIEW.md for the exact candidate distributions, security-estimation protocol, zeroization scope, side-channel threat model, conditional key-switch theorem, and missing obligations for a full RNS-BFV multiplication proof.

- Secret-key wrapper now overwrites the RNS coefficient buffers on drop using zeroize; the accessor is crate-private and a direct zeroization test was added.
- The generated-key phase test reconstructs all 8192 coefficients for every gadget digit, rather than sampling six positions.
- The implemented eta=2 error has coefficient support [-2,2], so E1 <= 2N = 16384. With L=14 and B=2^16, the conditional key-switch contribution bound is 15,032,156,160.
- No ring-aware RLWE estimator has been run. The generic LWE estimator is not treated as a substitute for a ring-aware security estimate.
- No constant-time or side-channel audit has been performed.
- The full RNS BFV multiplication/decryption noise proof remains open because the RNS key generator is not yet integrated with a complete encryption/decryption pipeline and fixed lift/rounding semantics.


## RNS-BFV integration work (experimental; CI validation pending)
- Added public-key generation from the OS-CSPRNG-backed ternary secret: b = -a*s + e (mod Q), with eta=2 centered-binomial error.
- Added coefficient-encoded plaintext embedding using Delta=floor(Q/t), RNS public-key encryption, exact-CRT decryption/decoding, and homomorphic addition.
- Added a multiply-then-relinearize API using the existing modular RNS tensor product, exact centered t/Q scale-and-round reference, and evaluation-key digits.
- Added an N=8192 integration test for encryption/decryption of sparse plaintexts and homomorphic addition. The test is not counted as passed until the CI run for the exact head commit completes successfully.
- Not yet validated: RNS multiplication followed by decryption/relinearization against an independent plaintext-ring oracle; complete RNS multiplication noise theorem; security estimate and side-channel audit.


## Integrated RNS-BFV path

See `PAPER1/RNS_BFV_INTEGRATION.md` for the equations, current API path, conditional encryption-error bound, multiply/relinearize sequence, and remaining proof/security gates.

- Public-key generation, encryption, decryption, and homomorphic addition are implemented in `src/keygen.rs`.
- The public-key encryption phase error for the specified bounded samplers is at most 32770 in coefficient infinity norm, before decoding.
- A multiply-plus-relinearize API is wired to the exact-CRT tensor scale-and-round reference and the existing evaluation-key key-switch implementation.
- An independent sparse plaintext-ring product comparison has been added to the N=8192 integration test. The tensor phase and multiply/relinearize path passed Rust unit tests in CI run 266; Clippy then identified one iterator-style warning, now corrected in a later commit. The complete workflow for the latest head remains pending.
