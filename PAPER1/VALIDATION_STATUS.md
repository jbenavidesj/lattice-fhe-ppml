# Paper 1 — validation status

**Status: experimental RNS-BFV research prototype; not submission-ready.**

The selected architecture remains leveled RNS-BFV as the core, with refresh/bootstrapping kept as a separate future extension.

## Implemented

- Four-lane RNS arithmetic for N=8192, candidate NTT primes and roots, exact CRT reconstruction, centered basis extension, and AsymRed modular reduction.
- Exact integer-lift BFV tensor multiplication: ciphertext components are lifted to centered integers, integer negacyclic products are computed with a nine-prime auxiliary NTT/CRT basis, and only then is coefficientwise t/Q scale-and-round applied. This preserves the integer product quotient required by the BFV multiplication convention.
- Experimental OS-CSPRNG-backed ternary secret and eta=2 centered-binomial error samplers; unbiased per-lane uniform R_Q sampling.
- RNS public-key generation, encryption, decryption, and homomorphic addition.
- Evaluation-key generation, exhaustive coefficientwise phase-relation tests, gadget decomposition, and relinearization.
- Multiply-then-relinearize RNS-BFV API and an N=8192 integration test comparing the decrypted result with an independent sparse negacyclic plaintext-ring product.
- Secret-key wrapper zeroization on drop. This does not erase all possible temporary copies and is not a side-channel audit.

## Mathematical validation

- The public-key encryption phase error has deterministic coefficient bound E0 = 4N+2 = 32770 for the specified bounded samplers.
- The conditional key-switch contribution bound is 15,032,156,160 for eta=2, N=8192, B=2^16, and L=14.
- A deterministic one-multiplication-plus-relinearization noise derivation is documented in `PAPER1/RNS_BFV_MULTIPLICATION_NOISE_PROOF.md`.
- The exact-rational audit script `scripts/audit_rns_bfv_noise.py` computes a total error upper bound of 91,700,891,552,753,113,897 and compares it with a decoding margin of approximately 3.2138270414e60.
- The nine-prime auxiliary NTT/CRT product is 468 bits and is checked to exceed twice the worst-case integer tensor coefficient bound (N(Q/2)^2).
- The proof covers one multiplication and one relinearization only. It does not establish arbitrary multiplicative depth.

## Reproducible validation

CI run 272 on code commit `47ee02f2e87a7dd7ab4fd7731ed5583e78d63ddb` completed successfully:
- 32 Rust unit tests passed, including encryption/decryption, addition, tensor-phase decryption, and multiply/relinearize comparison against the sparse plaintext oracle.
- Rust formatting passed.
- Clippy passed with warnings denied.
- Benchmark target compilation passed.
- Python arithmetic audits passed, including the auxiliary NTT prime/root and CRT-range audit.

CI run 288 on code commit `92542f5ca42a761445512e59db4bacf26e851eaa` completed successfully with the new exact-rational RNS-BFV noise audit included. Both CI jobs passed: all 32 Rust unit tests, formatting, Clippy, benchmark-target compilation, and all Python arithmetic/noise audits.

## Structured evaluation-key security model

`PAPER1/EVALUATION_KEY_SECURITY_ANALYSIS.md` now formulates the 14 evaluation-key equations as a joint related-secret observation of `(s, s^2)`. This is not a standard rank-two RLWE distribution because the public second coordinate is the known scalar `B^j`, and the secret coordinates are dependent. The note specifies the joint-transcript and algebraic-attack questions still requiring specialist analysis. It establishes no attack, reduction, or security level.

CI run 319 on commit `c8547a9db15b2b40c44f4f81c8bd824fb3912dcc` completed successfully: Python arithmetic/noise audits passed; Rust tests, formatting, Clippy, and benchmark-target compilation passed.

## Not established

- A concrete RLWE security estimate or 128-bit security claim. A pinned unstructured-LWE diagnostic script and protocol are prepared in `scripts/estimate_lwe_proxy.py` and `PAPER1/SECURITY_ESTIMATION_PROTOCOL.md`, but the estimator has not been executed because this runtime has no SageMath installation; no security number is reported.
- Independent cryptographic review or a proof against ring-structure attacks.
- Constant-time behavior, side-channel resistance, or comprehensive memory-remanence protection.
- Arbitrary multiplicative depth, modulus switching, or bootstrapping.
- A production-optimized RNS tensor multiplication and scale-and-round implementation; the current exact auxiliary NTT/CRT and BigInt path is a correctness reference.
- Release benchmark measurements, raw timing datasets, confidence intervals, documented hardware/compiler metadata, or any speedup claim. Criterion targets now include four-lane N=8192 RNS NTT multiplication and exact-reference BFV tensor multiplication; see `PAPER1/BENCHMARK_PROTOCOL.md`.
- IEEE submission readiness.

AsymRed is exact modular reduction; it does not intrinsically reduce cryptographic noise. The tiny-ring BFV module uses deterministic test-only sampling and must never protect real data.

## Remaining gates

1. Obtain an independent review of the one-multiplication derivation, especially centered-lift quotient handling and the decoding-margin argument.
2. Obtain independent review of `PAPER1/EVALUATION_KEY_SECURITY_ANALYSIS.md`, especially joint public-key/evaluation-key attacks and algebraic exploitation of s^2; the existing unstructured-LWE proxy omits these samples.
3. Execute the pinned lattice-estimator diagnostic in a SageMath environment; assess ring-LWE assumptions and structural attacks.
4. Replace the correctness-reference multiplication with an optimized, proven RNS implementation only after differential validation against the exact reference.
5. Run release benchmarks with repeated samples, raw output, and complete hardware/compiler metadata.
6. Review secret-dependent control flow, memory access, temporary copies, and side-channel exposure.

Until these gates are passed, describe the work as an experimental RNS-BFV prototype with a one-multiplication correctness argument—not as a production-secure or fully validated new FHE scheme.


## Adjacent-level cancellation analysis

The evaluation-key security note now derives the exact adjacent-level identity `y_(j+1)-B*y_j = e_(j+1)-B*e_j`, where `y_j=b_j+a_j*s`. The transformed coefficient vector is jointly uniform, but the transformed errors are correlated: coefficientwise variance `1+B^2`, adjacent covariance `-B`, and support `[-2(1+B), 2(1+B)]`. This is an algebraic reformulation of the existing public transcript, not additional leakage or a demonstrated attack. The error law is not iid, so a conventional independent-sample RLWE estimator cannot be applied without further justification.


## Ternary-square parity audit and interpretation

`scripts/verify_ternary_square_parity.py` checks the exact negacyclic-square identity modulo 2 for deterministic random ternary inputs at several even toy degrees. The CI run on commit `e5709b1123ebec73d457b2f7d5943dc9cbfcbe37` (run #339) completed successfully: both Python arithmetic audits and Rust tests/formatting/Clippy/benchmark compilation passed. The analysis note now explicitly explains why this identity is not directly observable from public residues modulo odd Q and why the unknown `a_j*s` term prevents treating it as a direct parity leak. No parity distinguisher or key-recovery algorithm has been demonstrated.


## Toy exhaustive related-key candidate experiment

Added `scripts/toy_evalkey_exhaustive_search.py` and `PAPER1/TOY_EVALUATION_KEY_EXPERIMENT.md`. A local deterministic run (seed `0xBF2`, 30 trials per degree) over toy rings `Z_11[X]/(X^N+1)` with `N=4,6,8`, base 3, three evaluation-key levels, and eta=2 errors yielded median surviving ternary candidates of 3.5/7.5/11 using only the public-key sample, versus 1/1/1 when the evaluation-key samples were also imposed. The planted secret remained among the candidates in every trial. These are deliberately tiny exhaustive-search results, not a production-parameter attack, security estimate, or extrapolation to N=8192. The script is now included in the Python CI job; CI for the latest workflow edit is pending and has not yet been claimed as passing.


## Exhaustive-search complexity assessment

The toy experiment's exhaustive candidate search costs `3^N` ternary candidates and, with the current direct negacyclic multiplication, worst-case arithmetic work `O(3^N * L * N^2)`. The report now tabulates candidate-space growth through N=8192 and includes exploratory local timings through N=12. These timings are not formal benchmarks. The central conclusion is that candidate-set reduction in tiny instances does not imply an efficient attack; no extrapolation to production parameters is justified.

CI run #360 on commit `e354af6fe7a06956c4b466a06079ae60e4149d77` completed successfully, including the toy exhaustive-search script in the Python audit job.


## Meet-in-the-middle feasibility assessment

The toy experiment report now explains the noisy modular join required by a split-secret meet-in-the-middle method. The two lists each have size `3^(N/2)`, but a valid join must accommodate a centered error box of up to `5^N` vectors for eta=2; naive error enumeration erases the apparent gain. The report also gives a clearly labeled random-residual heuristic for expected false candidates under q=11: approximately 3.46, 6.43, and 11.96 at N=4,6,8 for one public sample. This is a sanity-check heuristic only; independence is not proven. No MITM attack is implemented or claimed.


## Toy meet-in-the-middle prototype

Added `scripts/toy_evalkey_mitm.py` and `PAPER1/TOY_MITM_PROTOTYPE.md`. The prototype splits an even-degree ternary candidate into two halves, hashes right-half contributions on two selected coordinates, probes the 5^2 possible eta=2 centered errors on those coordinates, and verifies full public and evaluation-key residuals. In 30 deterministic trials at each N=4,6,8, its candidate set exactly matched exhaustive enumeration in all 90 trials. Median observed times were 0.000211/0.000854/0.004212 s for MITM versus 0.000240/0.003516/0.049400 s for exhaustive enumeration (single-machine exploratory measurements only). This is a toy algorithmic result; the lists still scale as 3^(N/2), selected-coordinate filtering and full residual checks are required, and no production-parameter attack is claimed. The new script is included in CI; latest CI result is pending verification.
