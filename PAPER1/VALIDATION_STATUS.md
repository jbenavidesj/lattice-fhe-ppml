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


## CI correction: MITM planted-secret assertion

CI run #376 exposed a Python `TypeError` in the new MITM audit: the generated planted secret was a list, while survivor candidates are stored as tuples, so `secret in mitm` attempted to hash an unhashable list. The assertion now checks `tuple(secret) in mitm`. The earlier candidate-set comparison remains an exact set equality assertion. MITM timing values are provisional pending a clean rerun; run #376 is not passing.


## MITM CI confirmation and evaluation-key join limitation

CI run #382 on commit `5a29436360206f37a35cb09cfa9928160416833c` completed successfully. Both jobs passed: all Python arithmetic/noise and toy-search audits, 32 Rust unit tests, formatting, Clippy, and benchmark-target compilation. This confirms the code at that commit; it does not constitute a benchmark measurement or a security assessment.

The current MITM implementation joins on selected coordinates of the public-key linear residual, enumerating the bounded error values only on those coordinates, then verifies the complete public-key and evaluation-key equations. The exact candidate-set equality check against exhaustive enumeration passed all 90 deterministic toy trials. Its timings remain exploratory.

A direct split of the evaluation-key equation is not separable. For (s=u+X^{N/2}v) in (R_Q=\mathbb Z_Q[X]/(X^N+1)), the square is
`u^2 + 2X^{N/2}uv + X^Nv^2` modulo (X^N+1), with the final term reducing to `-v^2`. The cross term couples both halves. Consequently, simply adding independent per-half evaluation-key hashes would be mathematically incorrect unless the cross term is explicitly represented. The current prototype correctly applies evaluation-key equations only after candidate joins; it does not yet gain list-pruning from those equations.

Next algorithmic work must either (a) derive an exact join key that accounts for the cross term and bounded errors, or (b) retain the public-key MITM filter and quantify whether additional safe partial constraints can be applied after a pair is joined. No improved attack or production-scale speedup is claimed.


## Staged MITM diagnostics and CI #391

Commit `417d8c33af9fb2336a2dfb53f91fbcbee73cbc48` adds per-stage instrumentation to `scripts/toy_evalkey_mitm.py`. CI run #391 (`43342603988`) completed successfully: Python arithmetic audits passed, and the Rust job passed unit tests, formatting, Clippy, and benchmark-target compilation.

Across 30 deterministic trials per degree, the MITM candidate set matched exhaustive enumeration in all 90 trials. The median exhaustive/MITM times were 0.000219/0.000166 s (N=4), 0.002845/0.000683 s (N=6), and 0.036167/0.003381 s (N=8). Median joined-pair counts were 16/150/1356; median candidates passing the complete public-key residual were 3.5/7.5/11; and final survivors were 1 at each degree. Sequential evaluation-key checks rejected a median 2.5/6.5/10 candidates at the first level, so later levels required only one check per trial median.

This demonstrates early rejection of downstream verification work in these toy samples, not reduction of the MITM join output or list size. The observed timing ratios (1.32x/4.17x/10.70x) are exploratory CI measurements, not formal benchmarks and not evidence of scalability or a production-parameter attack. The detailed table and interpretation are in `PAPER1/TOY_MITM_PROTOTYPE.md`.


## Adaptive MITM selector: parameterized audit and held-out evaluation

The selector cost proxy is now parameterized by q, eta, candidate coordinate counts, and a relative pair-cost weight lambda. The script scripts/audit_mitm_selector.py checks the formula and admissible choices over q={11,17,31,97}, eta={0,1,2,3} where q>2eta, and even N={4,6,8,10,12}. This is a formula/parameter audit, not empirical performance validation across those parameter sets.

Added scripts/audit_mitm_selector_holdout.py, which freezes the existing lambda=4 selector and evaluates it on a disjoint deterministic seed (0xC0FFEE), using the current toy q=11, eta=2 generator and N={4,6,8}. For each held-out instance, it compares k=1,2,3,4 on the same data, checks exact candidate-set equality against exhaustive enumeration, and reports median timing regret relative to the fastest fixed k. The experiment is intentionally limited to the current toy q/eta model; it does not validate generalization across q or eta. Its CI result must be checked before quoting any numerical held-out outcome.

## Manuscript and external-review preparation

Added PAPER1/IEEE_MANUSCRIPT_PLAN.md with a conservative contribution statement, proposed structure, required figures/tables, and explicit submission blockers. Added PAPER1/INDEPENDENT_REVIEW_PACKAGE.md with separate checklists for the multiplication/noise proof, joint public/evaluation-key security model, and implementation/side-channel review.

These documents prepare independent review; they do not mean any external review has taken place. The PR description has been reconciled with the implemented functionality and remaining limitations. The PR remains draft and unmerged.

## Current publication-readiness assessment

The repository has substantial implementation and deterministic correctness evidence, but it is not yet an IEEE submission package. The held-out MITM experiment is a toy algorithm-selection diagnostic, not a cryptographic security result. Still outstanding are: verified held-out CI output; SageMath execution of the pinned unstructured-LWE proxy with careful interpretation; independent mathematical and cryptanalytic review; release-mode performance benchmarks with raw data and environment metadata; related-work/novelty comparison; and final manuscript drafting and technical editing. No concrete security level, production-readiness, arbitrary-depth correctness, or side-channel resistance is claimed.

## Held-out adaptive MITM selector result — CI #434

CI run #434 (43345625418) completed successfully on commit b3a21b0330b55af39a14d7be8e945be7fbf351ca. The selector formula audit passed 80 parameter combinations. The frozen lambda=4 selector was then tested on ten disjoint-seed instances per degree (seed 0xC0FFEE, q=11, eta=2, N=4,6,8), comparing k=1,2,3,4 twice per instance against exact exhaustive candidate sets. The selector chose k=(1,2,2), matching the best fixed-k median for these held-out samples; median regret was 1.000 at each degree. Exact candidate-set comparisons passed 40/40 per degree. Full timings and caveats are in PAPER1/ADAPTIVE_MITM_HOLDOUT_RESULTS.md.

This is a narrow toy-scale held-out result, not evidence of generalization across q/eta or production degrees. Ten instances per degree and CI-host timing noise are insufficient for a broad predictive claim. CI #434 also passed Rust tests, formatting, Clippy, and benchmark-target compilation.

## Proof cross-check refinement (2026-11-13)

The current proof and IEEE manuscript draft were cross-checked against `src/rns.rs`, `src/keygen.rs`, and `scripts/audit_rns_bfv_noise.py`.

- Clarified the auxiliary CRT range argument: each negacyclic product is reconstructed independently under the single-product bound (N(Q/2)^2); the two cross products are added only after signed BigInt reconstruction. No combined cross coefficient is sent through the smaller CRT range.
- Expanded the algebraic derivation of the quotient/carry, scale-bias, mixed-error, and error-product terms in `PAPER1/RNS_BFV_MULTIPLICATION_NOISE_PROOF.md`.
- Added the centered BFV decoding-margin derivation, including the offset caused by (Q=t\Delta+r).
- Updated `PAPER1/IEEE_MANUSCRIPT_DRAFT.md` to summarize the actual numerical bounds and point to the full derivation.

The documentation commits are present on `paper1-validation-corrections`. CI runs #456 and #457 for commit `f04e5909f551904aa8ba12324bf9002864d58cb5` were observed in progress at the time of this update; they must complete successfully before claiming validation of this exact head. The latest completed full CI before these refinements was run #449 on commit `4800c0dc279c17bbfb0f7aca8a1f6e820645b1d4`, which passed both the Rust and Python audit jobs.

This cross-check is an internal consistency review, not independent mathematical peer review. The one-multiplication scope and all security limitations above remain unchanged.

## Evaluation-key transcript review refinement (2026-11-13)

The manuscript now states the exact adjacent-level transformed equations and distinguishes three separate facts: (i) the thirteen transformed coefficient polynomials are jointly uniform; (ii) their transformed errors have a banded, non-iid joint distribution; and (iii) the transformation is deterministic post-processing of the published evaluation key, not additional information-theoretic leakage.

The security note now gives the full (13\times13) tridiagonal covariance matrix for the transformed errors at each coefficient position, with diagonal (1+B^2) and adjacent off-diagonal entries (-B). It also records independence between the transformed coefficient vector and transformed error vector under the implemented independent samplers. These distributional facts do not constitute an attack, a reduction, or a concrete security estimate.

The implementation was checked against `src/keygen.rs`: each evaluation-key (a_j) is sampled independently and uniformly per RNS lane; each eta=2 error is generated as the difference of two independent two-bit population counts; and the public-key sample uses the same secret with an independent uniform (a_{pk}) and eta=2 error. The public and evaluation keys must therefore be treated as one joint transcript.

CI runs #458 and #459 completed successfully on commit `1ab591b64fb9542831a1ffe7cc1be94b9aabbc1e`, including both Python audit and Rust validation jobs. CI for the subsequent manuscript/security-note commits must still be checked against the exact latest head. Independent specialist cryptanalysis remains outstanding.

## Staged evaluation-key filtering diagnostic (2026-11-13)

Added `scripts/audit_evalkey_filtering.py` and wired it into `.github/workflows/paper1-validation.yml`. The audit exhaustively counts ternary candidates surviving (a) the public-key equation and (b) each of three successive evaluation-key levels, for (q=11), (B=3), eta=2, (N\in\{4,6,8\}), 30 deterministic instances per degree. It asserts planted-secret survival and monotone candidate counts. This measures toy incremental filtering only; it is not a production attack or a security estimate.

CI runs #468 and #469 were triggered on commit `70ab05e5b52038b59eb5edfd98c5aeba3a89943d`; at the time of this note both jobs were still running. The subsequent documentation commits are also awaiting CI. Do not quote audit results or mark the latest head validated until the exact current-head workflow runs complete successfully.

The staged-filtering Python audit completed successfully in CI run #472 on commit `9e85f82d127645021d5898ee75f558b3188c0d94`. Its 30-instance medians and unique-candidate counts are recorded in `PAPER1/EVALUATION_KEY_SECURITY_ANALYSIS.md`; the planted secret survived all stages. The run's Python audit job passed. Rust validation and CI for the subsequent result-documentation commits must still be checked on the exact latest branch head.

## Adjacent-level linear prefilter result (2026-11-13)

The new exhaustive toy audit uses (q=29), (B=3), eta=3, and (N=4,6,8), with 30 instances per degree. The transformed error support radius is 12, strictly below (q/2), so the centered-residue bound is exact. Eta=3 is intentionally a toy stress setting and differs from the implementation's eta=2 sampler; it is not a production-distribution model. The Python audit passed in CI run #496 on the q=29 script revision.

The public equation already had median one candidate at every degree. The two linear cancellation filters modestly increased the number of unique-candidate instances: N=4, 23/30 to 27/30; N=6, 27/30 to 29/30; N=8 remained 30/30. Mean survivor counts fell from 1.300 to 1.100 at N=4 and from 1.267 to 1.033 at N=6. The subsequent three quadratic evaluation-key levels yielded one candidate in every tested instance. These data do not establish a practical attack or a production-scale speedup.

CI for the latest documentation commits is still pending full Rust validation; record success only against the exact current branch head.
