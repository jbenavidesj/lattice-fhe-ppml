# An Experimental RNS-BFV Implementation with Exact Integer-Lift Multiplication and Reproducible Correctness Audits

**Manuscript status:** working draft for internal development; not submission-ready. The abstract and novelty claims must be revisited after related-work analysis, independent review, SageMath estimation, and release benchmarking.

## Abstract (provisional)

This work presents an experimental implementation and correctness study of a leveled Ring-LWE-based BFV prototype using a four-lane residue number system (RNS) representation at polynomial degree N=8192. The multiplication reference path lifts ciphertext components to centered integers, computes negacyclic tensor products through an auxiliary NTT/CRT basis, and retains the integer quotient information required for coefficientwise BFV scale-and-round. Deterministic audits check arithmetic identities, auxiliary reconstruction range, and a conservative noise bound for one multiplication followed by relinearization. The public evaluation-key format is analyzed as a structured collection of related-secret equations involving (s,s^2), for which no concrete security estimate is claimed. Small-degree exhaustive and meet-in-the-middle experiments are included only as algorithmic diagnostics. The implementation is an experimental correctness prototype: it does not establish a concrete Ring-LWE security level, arbitrary multiplicative depth, side-channel resistance, or production performance.

## 1. Introduction

Fully homomorphic encryption requires arithmetic over polynomial rings together with careful control of ciphertext noise. Implementations based on BFV commonly combine number-theoretic transforms, residue number systems, gadget decomposition, and relinearization. The interaction between integer representatives, quotient information, and scale-and-round is particularly important in multiplication: reducing an intermediate tensor product modulo the ciphertext modulus before scaling can discard information needed by the intended BFV operation.

This paper studies an experimental leveled RNS-BFV implementation and emphasizes auditable correctness rather than a premature performance or security claim. Its central engineering choice is an exact integer-lift multiplication reference path: centered ciphertext components are multiplied over the integer negacyclic ring using an auxiliary NTT/CRT basis whose product range is checked before reconstruction and scale-and-round.

The paper also records a structured security issue in the evaluation-key transcript. The published relations have the form b_j+a_j s=B^j s^2+e_j (mod Q). These are not simply additional independent ordinary RLWE samples: the target s^2 is related to the same secret s. We therefore keep the security assessment separate from the implementation correctness evidence.

### Contributions and scope

The defensible contributions investigated here are:

1. An experimental four-lane RNS arithmetic implementation targeting N=8192, with candidate NTT parameters, CRT reconstruction, centered basis extension, and modular reduction routines.
2. An exact integer-lift BFV tensor-multiplication reference path using an auxiliary NTT/CRT basis and coefficientwise scale-and-round.
3. Executable arithmetic and noise audits, including a deterministic one-multiplication-plus-relinearization correctness bound under the specified bounded samplers.
4. An explicit joint-transcript formulation for the structured evaluation key and a careful statement of what current unstructured-LWE proxy analysis does not cover.
5. Reproducible small-parameter exhaustive and MITM candidate-search diagnostics, with exact candidate-set comparisons.

These claims describe implementation and validation work. A literature comparison is still required to establish novelty relative to existing BFV/RNS implementations.

## 2. Mathematical and cryptographic setting

Let R_Q=Z_Q[X]/(X^N+1), with N=8192 for the implementation target. The prototype uses a four-lane RNS representation of the ciphertext modulus, plaintext modulus t=65537, ternary secret coefficients, and centered-binomial error coefficients supported on [-2,2]. The relinearization gadget uses base B=2^16 and L=14 levels.

The public-key relation is b_pk+a_pk s=e_pk (mod Q), with sign convention as implemented. The evaluation-key relations are b_j+a_j s=B^j s^2+e_j (mod Q). Each a_j is sampled uniformly in the RNS representation and each error coefficient follows the specified eta=2 bounded distribution.

**Parameter table to complete:** list every RNS prime, their product Q, NTT roots, plaintext modulus, gadget base and level count, sampler distributions, and exact implementation revision. Values must be checked against the source and parameter audit before submission.

## 3. Implementation architecture

The implementation separates modular arithmetic, negacyclic polynomial operations, RNS/CRT conversion, key generation, encryption/decryption, and evaluation-key operations. Four RNS lanes represent the ciphertext modulus. Candidate NTT primes and roots are checked by deterministic parameter audits. CRT reconstruction and centered basis extension are implemented explicitly.

The tensor multiplication path is a correctness reference. It lifts each ciphertext component to its centered integer representative, forms the three integer negacyclic tensor components, computes their coefficients using an auxiliary NTT/CRT basis, reconstructs the exact integer coefficients, and only then applies coefficientwise t/Q scale-and-round. For each individual negacyclic product, the auxiliary basis product is checked to exceed twice the worst-case coefficient bound. The cross component is formed by two separately reconstructed exact products, whose signed BigInt coefficient vectors are added only after reconstruction; therefore no combined two-product coefficient is passed through the smaller single-product CRT bound. This design preserves the quotient information that would be lost by prematurely reducing the tensor product modulo Q.

## 4. Correctness argument for one multiplication and relinearization

For an input ciphertext, write its centered-lift decryption phase as \(x_i=\Delta M_i+E_i\), where \(M_i=m_i+tk_i\), \(Q=t\Delta+r\), and the centered-lift quotient satisfies \(\|k_i\|_\infty\le4097\). The resulting bounds are \(\|M_i\|_\infty\le268,570,625\) and \(\|E_i\|_\infty\le10,435,053\). The unrounded tensor phase is \((t/Q)x_1x_2\); expanding it separates the plaintext quotient/carry term, scale bias, mixed plaintext-error terms, and error-product term. The three coefficientwise scale-rounding residuals are bounded using \(\|s\|_1\le N\) and \(\|s^2\|_1\le N^2\). Gadget relinearization contributes at most \(L(B-1)2N=15,032,156,160\) to the coefficientwise phase error.

The executable exact-rational audit reports a total error upper bound of 91,700,891,552,753,113,897 and a centered-decoding margin of approximately \(3.2138270414\times10^{60}\) for this parameter instance. The margin accounts for the offset \(r m_{12}/Q\) induced by \(\Delta=\lfloor Q/t\rfloor\). The auxiliary CRT product is 468 bits; each individual product is reconstructed separately before the two cross products are added. The full derivation and assumptions are given in `PAPER1/RNS_BFV_MULTIPLICATION_NOISE_PROOF.md`.

This argument covers one multiplication followed by one relinearization only. It does not establish arbitrary multiplicative depth. The proof and its centered-lift quotient handling require independent mathematical review before publication.

## 5. Evaluation-key structure and security limitations

The evaluation-key transcript contains fourteen equations
\[
b_j+a_js=B^js^2+e_j\pmod Q,
\]
sharing the same secret \(s\) and related target \(s^2\). The full public transcript also includes the conventional public-key equation \(b_{pk}+a_{pk}s=e_{pk}\pmod Q\). It is therefore not justified to count the fourteen evaluation-key equations as fourteen ordinary independent RLWE samples or to estimate the public and evaluation keys separately and combine nominal security levels.

An exact adjacent-level transformation illustrates both the structure and the limitation. Setting \(y_j=b_j+a_js\), one obtains
\[
b_{j+1}-Bb_j+(a_{j+1}-Ba_j)s=e_{j+1}-Be_j\pmod Q.
\]
The transformed coefficient vector \((a_{j+1}-Ba_j)_{j=0}^{12}\) is jointly uniform over \(R_Q^{13}\), because the difference map from the fourteen independent uniform \(a_j\)'s is surjective. However, the transformed errors are correlated. For the implemented eta=2 sampler, an original coefficient has probability mass \((1,4,6,4,1)/16\) on \((-2,-1,0,1,2)\), with variance one. Before modular reduction, each transformed coefficient has support in \([-2(1+B),2(1+B)]\), variance \(1+B^2\), and adjacent covariance \(-B\); nonadjacent transformed errors are uncorrelated. Thus the transformation gives thirteen RLWE-shaped equations with a banded, non-iid error vector—not thirteen independent standard eta=2 samples. Centered modular representatives may wrap, so these unreduced support and covariance values cannot be inserted uncritically into a conventional estimator.

This transformation is deterministic post-processing of the public evaluation key: it provides an alternative cryptanalytic representation, not additional information-theoretic leakage. Neither the original related-target system nor the transformed correlated-error system has been shown to yield a practical attack or a security reduction. The exact model and caveats are detailed in PAPER1/EVALUATION_KEY_SECURITY_ANALYSIS.md.

The pinned lattice-estimator diagnostic has not yet been executed in a SageMath environment. Even if executed, the current unstructured-LWE proxy would not cover the structured evaluation-key samples or prove Ring-LWE security. No concrete bit-security claim is made.

## 6. Implementation validation

The validation suite includes Rust unit and integration tests, formatting, Clippy, benchmark-target compilation, and deterministic Python audits. The audits cover candidate parameters, AsymRed, negacyclic arithmetic, toy and N=8192 noise bounds, ternary-square parity, split-secret square identities, exhaustive toy evaluation-key candidate search, and MITM candidate-set equality.

A new staged-filtering audit records ternary candidate counts after the public-key equation and each successive evaluation-key level for toy instances. In 30 deterministic instances per degree, median survivor counts (public equation, then levels 1–3) were 4/1/1/1 for N=4, 8/1/1/1 for N=6, and 12.5/1/1/1 for N=8; the planted secret survived every stage. This shows strong incremental filtering in this tiny exhaustive setting, but the search still enumerates all 3^N candidates. The experiment uses q=11, B=3, and only three levels, so it is not an attack-complexity estimate for the implementation parameters or evidence of production insecurity. A further audit tests a safe linear prefilter obtained by subtracting B times one evaluation-key equation from the next, cancelling the shared s^2 term. Its transformed error support is bounded by eta(1+B), so the filter can be applied before candidate-square computation without rejecting the planted secret. The refined experiment uses q=29, B=3, eta=3, and N in {4,6,8}, giving a centered transformed-error support radius of 12 below q/2. Eta=3 is a deliberate toy stress setting, distinct from the implementation's eta=2 error sampler, chosen to retain some false candidates after the public-key filter; it is not a production-parameter experiment. In 30 instances per degree, the mean candidate counts after the public equation and the two cancellation filters were 1.300/1.167/1.100 for N=4, 1.267/1.100/1.033 for N=6, and 1/1/1 for N=8. The median was already one after the public equation at every degree; the linear filters therefore provided only modest incremental filtering in a few ambiguous instances. The three quadratic levels yielded a unique candidate in all tested instances. This remains a tiny exhaustive diagnostic, not a practical attack or a production security estimate.

The CI workflow runs Rust unit tests, formatting, Clippy, benchmark-target compilation, and the Python arithmetic audits. The last fully completed validation before the present proof-documentation refinements passed on commit 4800c0dc279c17bbfb0f7aca8a1f6e820645b1d4, including the N=8192 noise audit, adaptive-selector parameter-grid audit, and held-out selector experiment. CI for the current proof refinements is running; its result must be recorded against the exact final manuscript commit before this section is frozen.

## 7. Toy meet-in-the-middle diagnostics

The toy MITM experiment splits an even-degree ternary candidate into two halves and hashes right-half public-key contributions on selected coefficient coordinates. It enumerates bounded error patterns on those coordinates, then verifies the full public-key and evaluation-key residuals. For N=4,6,8, the candidate set matched exhaustive enumeration in all 90 original deterministic trials.

The evaluation-key residual under the split contains the cross term 2 X^(N/2) u v. This term couples the halves, so independent half-list evaluation-key hashes are not valid unless the cross term is represented exactly. The current MITM method therefore uses the public-key relation for joining and applies evaluation-key constraints after each pair is retrieved. It does not claim production-parameter key recovery or security impact.

The adaptive coordinate selector uses a heuristic cost proxy. A frozen lambda=4 selector was tested on ten held-out toy instances per degree at q=11 and eta=2, using seed 0xC0FFEE. It selected k=(1,2,2) for N=(4,6,8), matching the fastest fixed-k median in this sample; median regret was 1.000 at each degree. This is a small-sample toy result, not evidence of generalization across q, eta, or production dimensions.

A separate cross-parameter robustness audit retained lambda=4 without refitting and
tested q in {17,31}, eta in {1,2}, and N in {4,6,8}, with eight fresh instances
per cell and two timing repeats per fixed k. In all twelve cells, the selected k
matched the lowest observed fixed-k median; median regret was 1.000 in every cell.
Each cell made 64 exact candidate-set comparisons against exhaustive enumeration.
The selected k values were (1,2,2) for q=17 at both eta values, (1,2,2) for
q=31, eta=1, and (1,1,2) for q=31, eta=2, in increasing N order. This is
limited evidence of robustness over these small toy settings only; it does not
establish predictive performance at larger dimensions or production parameters.

## 8. Performance evaluation

A first Criterion release-mode baseline was collected in a dedicated GitHub Actions
workflow on commit be820f044647e8e2444d5e415503172bb1498a6f (run #3).
The runner was a virtualized Azure Linux VM with an AMD EPYC 9V74 host,
four visible vCPUs, approximately 16 GiB RAM, x86_64, Linux kernel
7.0.0-1017-azure, rustc/cargo 1.100.0 and LLVM 23.1.5. Raw Criterion
outputs and environment metadata were retained in workflow artifact
paper1-release-benchmarks-be820f044647e8e2444d5e415503172bb1498a6f.

| Operation | Estimate | 95% within-run CI |
|---|---:|---:|
| Four-lane RNS negacyclic NTT multiplication, N=8192 | 6.948 ms | 6.938–6.969 ms |
| Exact-reference BFV tensor multiplication, N=8192 | 415.90 ms | 415.06–416.73 ms |
| BFV encryption | 22.460 ms | 22.449–22.470 ms |
| BFV decryption | 54.348 ms | 54.314–54.418 ms |
| BFV addition | 163.37 us | 163.02–163.88 us |
| BFV multiply plus relinearization | 685.83 ms | 685.48–686.20 ms |
| Relinearization-key generation | 375.69 ms | 375.42–376.04 ms |

For the same 20,000 modular-reduction inputs, AsymRed measured 170.20 us
(169.85–170.67 us), while the u128 % q baseline measured 38.52 us
(38.285–38.840 us). AsymRed was therefore approximately 4.42 times slower
in this microbenchmark; no speedup is claimed.

These results are a single virtualized-CI session. Criterion's intervals
describe within-run sampling uncertainty and do not capture variation across
independent sessions, machines, CPU frequency, or co-tenancy. The exact
auxiliary NTT/CRT plus BigInt multiplication is a correctness-reference path,
so its cost is not representative of a future optimized implementation.
These measurements provide a reproducible baseline only, not evidence of
production performance or competitiveness. A publishable comparison still
requires independent sessions, preferably bare-metal measurements, additional
primitive-level baselines, and a recognized BFV implementation with matching
semantics and parameters.

## 9. Limitations and responsible claims

- No concrete Ring-LWE security level or 128-bit security claim.
- No independent cryptanalytic review of the joint public/evaluation-key transcript.
- No arbitrary multiplicative-depth proof, modulus switching, or bootstrapping.
- No production-optimized BFV multiplication or multi-session comparative benchmark evaluation; only a single CI release baseline is available.
- No constant-time, side-channel-resistance, or comprehensive memory-remanence claim.
- No production-parameter attack demonstrated by the toy exhaustive/MITM experiments.
- No independent review of the multiplication/noise proof completed yet.

## 10. Conclusion

This work provides an auditable experimental RNS-BFV implementation and a set of deterministic correctness checks, with particular attention to exact integer-lift multiplication and the structured evaluation-key transcript. The current evidence supports a bounded correctness statement and reproducible toy diagnostics, not a concrete security level or production-readiness claim. Independent mathematical and cryptanalytic review, estimator execution with careful scope, multi-session comparative benchmarking, and a related-work comparison remain necessary before submission.

## References

**To complete:** add primary BFV, RNS/NTT, lattice-estimator, and homomorphic-encryption-standard references. Verify bibliographic metadata and ensure every claim is supported by an appropriate primary source.