# An Experimental RNS-BFV Implementation with Exact Integer-Lift Multiplication and Reproducible Correctness Audits

## Abstract

We implement and audit an experimental RNS-BFV prototype with four residue lanes at polynomial degree N=8192. For multiplication, the reference path lifts ciphertext components to centered integers, computes the negacyclic tensor products with an auxiliary NTT/CRT basis, and preserves the quotient information needed for coefficientwise BFV scale-and-round. Deterministic tests verify the arithmetic identities, the auxiliary reconstruction range, and a conservative noise bound for one multiplication followed by relinearization. We also examine the evaluation-key transcript as a structured system of related-secret equations involving s and s². The security analysis remains deliberately limited: the small-degree exhaustive and meet-in-the-middle experiments are diagnostics, not attacks on the implementation parameters, and the scalar LWE proxy does not provide a concrete Ring-LWE security estimate. The prototype does not establish arbitrary multiplicative depth, side-channel resistance, or production-level performance.

## 1. Introduction

Fully homomorphic encryption (FHE) combines arithmetic over polynomial rings with explicit control of ciphertext noise. In BFV implementations, that arithmetic is typically supported by number-theoretic transforms, residue number systems (RNS), gadget decomposition, and relinearization. Multiplication requires particular care with integer representatives: reducing the tensor product modulo the ciphertext modulus before scale-and-round can discard quotient information needed to obtain the intended result.

We study an experimental RNS-BFV implementation, with the emphasis on correctness that can be checked independently rather than on performance or security claims. The multiplication reference path uses centered integer lifts and an auxiliary NTT/CRT basis. Before reconstructing each product, the implementation verifies that the auxiliary modulus product exceeds the coefficient bound; coefficientwise scale-and-round is applied only after exact reconstruction.

The evaluation key raises a separate question. Its equations have the form b_j+a_j s=B^j s^2+e_j (mod Q), so they share the secret s and the related target s². They cannot simply be counted as independent ordinary RLWE samples. We analyze this transcript separately and do not infer a security level from the implementation tests.

### Contributions and scope

The defensible contributions investigated here are:

1. An experimental four-lane RNS arithmetic implementation targeting N=8192, with candidate NTT parameters, CRT reconstruction, centered basis extension, and modular reduction routines.
2. An exact integer-lift BFV tensor-multiplication reference path using an auxiliary NTT/CRT basis and coefficientwise scale-and-round.
3. Executable arithmetic and noise audits, including a deterministic one-multiplication-plus-relinearization correctness bound under the specified bounded samplers.
4. An explicit joint-transcript formulation for the structured evaluation key and a careful statement of what current unstructured-LWE proxy analysis does not cover.
5. Reproducible small-parameter exhaustive and MITM candidate-search diagnostics, with exact candidate-set comparisons.

These claims describe implementation and validation work, not a new BFV scheme or a new RNS multiplication algorithm. The exact integer-lift/tensor-product/scale-and-round sequence is part of the textbook BFV multiplication semantics and is already treated in prior full-RNS BFV work; our use of it as a transparent BigInt/auxiliary-CRT reference path is an implementation choice, not by itself a novelty claim. The potentially distinct contribution is limited to the particular reproducibility package: a source-linked, parameter-specific one-operation correctness audit and finite diagnostics for the implemented related-secret evaluation-key transcript. Whether that package is sufficiently novel for a research journal remains unestablished.

### Related work and novelty boundary

The arithmetic studied here is situated within the original FV construction and subsequent full-RNS implementations. Fan and Vercauteren describe the FV multiplication/relinearization framework and its noise analysis [1]. Bajard, Eynard, Hasan, and Zucca develop a full-RNS FV-like scheme, including RNS-compatible decryption and multiplication procedures that avoid multiprecision positional arithmetic and report implementation speedups [2]. Their work already establishes that full-RNS FV-like arithmetic and efficient RNS rounding are prior art; neither RNS-BFV itself nor the general goal of removing multiprecision arithmetic is claimed here as novel. Separately, Bajard, Eynard, Merkiche, and Plantard [5] study a full-RNS Babai/CVP round-off procedure for lattice-based cryptographic arithmetic and its hardware realization. That problem is distinct from the coefficientwise $t/Q$ scale-and-round operation in FV homomorphic multiplication; [5] is relevant RNS arithmetic background, not a direct prior implementation of the FV multiplication step studied here.

The algorithmic boundary is important. Textbook BFV multiplication forms the degree-two tensor product over integer representatives and then applies coefficientwise scale-and-round; this underlying lift/multiply/scale structure is not introduced by the present implementation [1]. BEHZ adapts the required conversions and rounding to RNS using integer arithmetic and auxiliary/redundant moduli, while HPS uses CRT basis-extension and scaling procedures with floating-point approximations, explicit precision analysis, and bounded effects on noise [2], [8]. Al Badawi et al. provide a direct implementation comparison of BEHZ and HPS on CPU and GPU, including multiplicative-depth and throughput measurements [7]. Consequently, the present auxiliary NTT/CRT plus BigInt route must be described narrowly: it reconstructs centered integer products exactly as a correctness-reference implementation, rather than proposing a new solution to RNS scale-and-round or outperforming BEHZ/HPS. The single-session measurements are not comparable to their optimized CPU/GPU results and support no competitiveness claim.

| Aspect | BEHZ | HPS | Present prototype |
|---|---|---|---|
| BFV multiplication and scaling | Full-RNS procedure | Full-RNS procedure | Exact integer-lift reference path |
| Conversion / rounding | Integer arithmetic with auxiliary/redundant moduli | CRT basis extension/scaling with floating-point approximations and precision analysis | Auxiliary NTT/CRT reconstruction followed by BigInt scale-and-round |
| Published implementation comparison | Compared with HPS in [7] | Compared with BEHZ in [7] | No equivalent comparative benchmark |
| Claim made here | Prior art | Prior art | Auditable reference path only; no performance or algorithmic-superiority claim |

The remaining candidate contribution is therefore the source-linked, parameter-specific correctness audit and the finite diagnostics of the implemented related-secret evaluation-key transcript. The former is a concrete instance-specific validation result, not a new general BFV noise theorem; the latter is a diagnostic characterization, not a demonstrated attack or security reduction. A sufficiently distinct methodological contribution beyond the prior full-RNS BFV literature has not yet been established.

For security context, the current community guidance is the 2024 *Security Guidelines for Implementing Homomorphic Encryption*, published in IACR Communications in Cryptology in 2025 [6]. The preliminary scalar proxy uses the general LWE-estimation framework discussed by Albrecht, Player, and Scott [3]. The 2018 Homomorphic Encryption Standard [4] is used only as historical community guidance for parameter context; HomomorphicEncryption.org explicitly describes it as a security-guidelines document, not a formal standard. Neither [3] nor [4] validates this prototype's parameters or its related-target evaluation-key transcript; they are methodological and parameter-context references only. In particular, an ordinary unstructured-LWE proxy cannot be substituted for a joint analysis of the implemented public/evaluation-key distribution.

## 2. Mathematical and cryptographic setting

Following the FV/BFV setting [1], let R_Q=Z_Q[X]/(X^N+1), with N=8192 for the implementation target. The prototype uses a four-lane RNS representation of the ciphertext modulus, plaintext modulus t=65537, ternary secret coefficients, and centered-binomial error coefficients supported on [-2,2]. The relinearization gadget uses base B=2^16 and L=14 levels. These are the implementation's audited candidate parameters, not a parameter set endorsed by [4] or a claimed security target.

The public-key relation is b_pk+a_pk s=e_pk (mod Q), with sign convention as implemented. The evaluation-key relations are b_j+a_j s=B^j s^2+e_j (mod Q). Each a_j is sampled uniformly in the RNS representation and each error coefficient follows the specified eta=2 bounded distribution.

**Concrete parameter instance.** The four coefficient moduli and primitive negacyclic roots are:

| Lane | Modulus q_i | Negacyclic root psi_i (order 2N) |
|---:|---:|---:|
| 1 | 36028797002170369 | 22505317672356688 |
| 2 | 36028796951838721 | 29410112198941026 |
| 3 | 18014398508400641 | 9354911369072846 |
| 4 | 18014398507892737 | 12617745759101472 |

Their product is the 218-bit ciphertext modulus
\[
Q=421249165630599354127590185589164472945208468246547404789529362433,
\]
with \(\Delta=\lfloor Q/65537\rfloor\) and plaintext modulus \(t=65537\). The parameter audit checks primality, pairwise coprimality, \(q_i\equiv1\pmod{2N}\), and exact order \(2N=16384\) of each \(\psi_i\). The gadget base and level count are \(B=2^{16}\) and \(L=14\). Secret coefficients are sampled independently and uniformly from \(\{-1,0,1\}\). Public-key and evaluation-key error coefficients follow the implemented centered-binomial \(\eta=2\) law: the difference of two independent \(\operatorname{Binomial}(2,1/2)\) variables, with support \([-2,2]\), variance one, and probability masses \((1,4,6,4,1)/16\) on \((-2,-1,0,1,2)\). The implementation revision and parameter-audit script are retained in the repository history and validation workflow. These are computational candidates, not a security parameter selection. Values must be checked against the source and parameter audit before submission.

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
The transformed coefficient vector \((a_{j+1}-Ba_j)_{j=0}^{12}\) is jointly uniform over \(R_Q^{13}\), since the difference map from fourteen independent uniform masks is surjective. The transformed errors, however, are correlated. Under the implemented eta=2 sampler, each original error coefficient has mass \((1,4,6,4,1)/16\) on \((-2,-1,0,1,2)\) and variance one. Before modular reduction, each adjacent-difference error has support \([-2(1+B),2(1+B)]\), variance \(1+B^2\), and covariance \(-B\) with its neighbor; nonadjacent differences are uncorrelated. The result is a system of thirteen RLWE-shaped equations with correlated, non-identically distributed errors, not thirteen independent standard eta=2 samples. For the configured 218-bit modulus Q, this support lies strictly inside the centered interval, so no centered-lift wrap occurs for these adjacent differences. This parameter-specific fact does not justify treating the errors as independent or using an ordinary-LWE estimator for the joint transcript.

This transformation is deterministic post-processing of the public evaluation key: it provides an alternative cryptanalytic representation, not additional information-theoretic leakage. Neither the original related-target system nor the transformed correlated-error system has been shown to yield a practical attack or a security reduction. The exact model and caveats are detailed in PAPER1/EVALUATION_KEY_SECURITY_ANALYSIS.md.

The joint transcript is generated from one shared ternary secret, one ordinary public-key sample, fourteen independent uniform evaluation-key masks, and independent eta=2 errors, with every evaluation-key target equal to the same negacyclic square \(s^2\). The exact joint distribution, adjacent-level covariance calculation, attack-family applicability review, and publication boundary are documented in `PAPER1/EVALUATION_KEY_SECURITY_ANALYSIS.md`. The adjacent cancellation yields thirteen jointly uniform masks but correlated errors: each unreduced coefficient has support radius 131,074, variance 4,294,967,297, and adjacent covariance -65,536. These derived equations are not independent standard RLWE samples. For all thirteen adjacent-cancellation equations, the coefficient-level error vector is \(z=De\), with exact covariance \(DD^T\) tridiagonal, diagonal \(B^2+1\), and adjacent entries \(-B\). The matrix is strictly diagonally dominant with margin \((B-1)^2\), hence positive definite. The exact joint characteristic function is \(\prod_{k=0}^{13}\cos^4((D^Tt)_k/2)\), retaining the discrete eta=2 law rather than a Gaussian approximation. A reproducible audit is provided in `scripts/audit_evalkey_joint_error_covariance.py`; this characterizes the error dependence but is not an attack or security estimate. An exact one-coefficient PMF calculation for a low-variance LLL relation shows why variance alone is insufficient: relative to the adjacent relation, its variance is lower (1,915,654,407 versus 4,294,967,297) and its central 99% quantile is narrower (111,528 versus 131,073), but its support radius is larger (271,334 versus 131,074) and its central 99.9% quantile is wider (140,667 versus 131,074). The exact calculation is documented in `PAPER1/EVALUATION_KEY_SECURITY_ANALYSIS.md`; it remains a marginal error-distribution comparison, not an attack result.  An exhaustive toy-ring candidate-filter experiment further shows that replacing the original equations by adjacent target-cancelled equations with the corresponding wider error bound can retain extra ternary candidates: in 2 of 20 trials at \(N=2,q=257,L=2,B=4\), the transformed filter retained two or three candidates while the original filter retained one. In 10 trials at \(N=8,q=65537,L=14\), both filters retained only the planted candidate. These toy counts are not evidence of a real-parameter attack or security; they illustrate possible information loss from target cancellation. The experiment is reproducible in `scripts/audit_evalkey_toy_secret_filtering.py`. Primal/dual, multi-sample, related-target, ring-specific, and algebraic/hybrid attacks are relevant research directions, but no complete-transcript attack cost or security reduction has been established.

A bounded `LWE.estimate.rough()` diagnostic has now been executed under SageMath 10.10 using the pinned lattice-estimator revision, ADPS16 reduction-cost model, and GSA shape assumption. For the scalar unstructured-LWE proxy, the minimum among the reported attacks is \(\log_2(\mathrm{rop})=93.732\) for the candidate (uSVP and dual-hybrid tie). This is a preliminary heuristic screening output only: it is not a Ring-LWE estimate, security lower bound, or concrete security level, and it does not model the structured evaluation-key samples targeting \(s^2\). The candidate/reference comparison also changes both modulus and error distribution. Full run output and limitations are recorded in `PAPER1/SECURITY_ESTIMATION_RESULTS.md`; the joint public/evaluation-key transcript still requires dedicated cryptanalysis and independent review. No concrete scheme-level bit-security claim is made.

## 6. Implementation validation

The validation suite combines Rust unit and integration tests, formatting, Clippy, benchmark-target compilation, and deterministic Python/SageMath audits. It checks the configured RNS parameters and NTT roots, modular and negacyclic arithmetic, exact auxiliary-CRT reconstruction, the one-multiplication noise bound, evaluation-key transcript identities, and exact agreement between toy exhaustive-search and MITM candidate sets.

The implementation-level tests include encryption/decryption and addition round trips, coefficientwise evaluation-key relation checks, and an N=8192 multiply/relinearize integration test against an independently computed sparse plaintext-ring product. The deterministic noise audit verifies the stated one-multiplication-plus-relinearization bound and strict decoding margin. The SageMath workflow also runs the bounded scalar unstructured-LWE proxy and exact toy transcript diagnostics; these do not constitute a Ring-LWE security estimate or production-scale attack.

Small-domain candidate-filtering and MITM experiments are retained as reproducibility diagnostics, not as evidence of production security or insecurity. Their parameter choices, sample counts, candidate-set comparisons, and limitations are documented in the appendices and accompanying audit scripts. The validation workflow is configured to run Python arithmetic and toy audits, Rust tests and static checks, and pinned SageMath diagnostics. Passing automated checks establishes reproducibility of those configured checks only; it is not independent mathematical or cryptanalytic review.

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

A first Criterion release-mode baseline was collected in a dedicated
continuous-integration workflow. The runner was a virtualized Azure Linux VM
with an AMD EPYC 9V74 host, four visible vCPUs, approximately 16 GiB RAM,
x86_64, Linux kernel 7.0.0-1017-azure, rustc/cargo 1.100.0 and LLVM 23.1.5.
Raw Criterion outputs and environment metadata are retained as supplementary
reproducibility artifacts.

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

This work provides an auditable experimental RNS-BFV implementation and deterministic correctness checks, with particular attention to exact integer-lift multiplication and the structured evaluation-key transcript. The evidence supports a bounded one-operation correctness statement and reproducible toy diagnostics, not a concrete security level or production-readiness claim. The internal editorial and citation pass is complete for the narrowed claims. The manuscript is not yet cleared for journal submission: independent mathematical review and specialist cryptanalytic review remain external requirements, and the distinct methodological contribution beyond BEHZ/HPS remains a question for a target journal's novelty threshold. The pinned scalar unstructured-LWE proxy is reported only as a limited diagnostic, not a scheme-level security estimate.

## Appendix A. Exact joint candidate constraints for the evaluation-key transcript

A further exhaustive toy audit compares the original evaluation-key residual constraints with an exact recurrence using the adjacent target-cancelled equations. The first original evaluation-key equation fixes the initial error vector e_0; each transformed residual z_j=e_{j+1}-Be_j then determines the next error vector exactly through e_{j+1}=z_j+Be_j (mod q). Requiring every reconstructed coefficient to remain in the eta=2 support [-2,2] is therefore equivalent to checking all original evaluation-key residuals, provided centered representatives are unambiguous. This preserves the shared-error dependence and avoids replacing the joint support by the wider coordinatewise box [-2(B+1),2(B+1)].

In exhaustive tests over all ternary secrets, the original and exact-joint filters produced identical candidate sets in 40 trials at N=2, q=23, B=4, L=2, and in 10 trials at N=5, q=65537, B=16, L=6. The coarse transformed box admitted no additional candidates in either configuration in this run. This result is specific to these generated toy transcripts and does not establish that the coarse relaxation is always lossless; a separate earlier toy experiment with different parameters observed additional survivors. The exact recurrence and original checks both retained only the planted secret in these trials. These are tiny exhaustive consistency tests, not scalable recovery experiments or evidence of security at the implementation parameters. The script is scripts/audit_evalkey_joint_candidate_filter.py.




## Appendix B. Toy meet-in-the-middle validation and scope

The exact toy meet-in-the-middle (MITM) routine was cross-checked against exhaustive candidate enumeration on 30 generated instances for each of N=4, 6, and 8; all tested coordinate counts produced identical candidate sets. For q=11, B=3, three evaluation levels, and eta=2, the selected MITM configuration had median runtimes of 0.000249 s, 0.001518 s, and 0.010250 s, compared with exhaustive medians of 0.000322 s, 0.004129 s, and 0.052275 s, respectively. These correspond to measured toy ratios of 1.29x, 2.72x, and 5.10x in that environment. They are small-instance microbenchmarks only, not asymptotic speedups or evidence of an attack on the production N=8192 parameters.

The frozen selector passed its 80-case parameter-grid audit. On a held-out q=11, eta=2 set (10 instances per N in {4,6,8}), it matched the fastest tested coordinate count in each dimension with exact candidate-set agreement. A further held-out grid over q in {17,31}, eta in {1,2}, and N in {4,6,8} passed all 12 cells, with 64 exact comparisons per cell and measured median regret 1.000. These results are finite toy-grid checks and do not imply optimality outside the tested configurations. The split-secret square/evaluation residual identity also passed 6,000 toy checks, validating an algebraic implementation identity rather than adding an independent cryptographic constraint.

Accordingly, the MITM work should be presented as a reproducible toy algorithm cross-check and selector study. It does not establish scalable secret recovery, a production attack, or a concrete security estimate for the ring-based scheme.


## Appendix C. MITM resource scaling

The current MITM implementation materializes two half-secret tables, each containing exactly 3^(N/2) ternary assignments. Increasing the number of selected coordinates in the bounded-error join can reduce the heuristic expected number of joined pairs, but does not reduce this exponential table term. For the Paper 1 modulus (218 bits), eta=2, and N=8192, a uniform-residue heuristic selects k=61 to bring the expected join count below one; nevertheless, each half-table has 3^4096 entries (log2 count approximately 6492.0). The corresponding payload-only storage projection is approximately 2^6510.8 bytes, before data-structure overhead. These are analytical resource projections, not measured attack costs. The expected-join heuristic assumes independent uniform residues and is not a rigorous bound in the structured negacyclic setting. The present MITM is therefore a toy validation method, not a plausible production-scale recovery attack in its current form.


A dimension sweep for the Paper 1 modulus and eta=2 gives the following base-2 resource exponents (the payload column counts coefficient residues only, excluding Python object and hash-table overhead):

| N | k* | log2(half-table entries) | log2(probe work) | log2(payload bytes) |
|---:|---:|---:|---:|---:|
| 8 | 1 | 6.3 | 8.7 | 15.1 |
| 16 | 1 | 12.7 | 15.0 | 22.5 |
| 32 | 1 | 25.4 | 27.7 | 36.2 |
| 64 | 1 | 50.7 | 53.0 | 62.5 |
| 128 | 1 | 101.4 | 103.8 | 114.2 |
| 256 | 2 | 202.9 | 207.5 | 216.7 |
| 512 | 4 | 405.8 | 415.0 | 420.6 |
| 1024 | 8 | 811.5 | 830.1 | 827.3 |
| 8192 | 61 | 6492.0 | 6633.6 | 6510.8 |



## Appendix D. Information content of the ternary square

An exhaustive toy audit measures the fibers of the map s -> s^2 in the negacyclic ring for ternary secrets at N in {2,4,6,8}. At minimum, the map is globally sign-invariant: s and -s produce the same square. Thus even an exact, noiseless disclosure of s^2 cannot uniquely identify a nonzero ternary secret without additional information. The experiment also measures any further collisions in these small rings. This is not a model of the complete evaluation-key transcript, where s^2 is mixed with secret-dependent linear terms and noise, and it does not establish a practical attack or a security bound.


## Appendix E. Stagewise information from public and evaluation-key equations

A new exhaustive toy experiment filters all ternary candidates first by the public-key equation and then sequentially by each of fourteen original evaluation-key equations, using the exact centered-binomial eta=2 residual support at every stage. It records mean and maximum survivor counts and checks that the planted secret survives. The tested dimensions are N=2, 4, and 6 only. The transcript generator uses independent uniform a-vectors and independent centered-binomial errors as an explicit toy model. These counts describe information accumulation in that synthetic model; they are not a production attack, a proof of independence in the actual key-generation procedure, or a security estimate.


## Appendix F. Controlled comparison of public and evaluation-key information

A controlled exhaustive experiment compares four filters on identical synthetic transcripts: public key alone, evaluation keys alone, their conjunction, and public key plus the exactly transformed evaluation-key system. The transformed system retains one anchor residual and all adjacent differences, with the original joint CBD_eta2 support reconstructed exactly. Since this triangular transformation is invertible, it must produce exactly the same candidate set as the original evaluation equations; it is not an independent source of information. The measured survivor counts isolate the marginal filtering contribution of the public and evaluation-key equations and their conjunction for N=2,3,4,5. The transcript generator is synthetic, and the results are not a production attack or a concrete security estimate.


For the q=23 small-ring stress-test, the independently reproduced preliminary survivor counts were: N=2 (40 trials), public-only mean 1.900 with 27/40 unique, evaluation-only mean 1.000 with 40/40 unique, and joint mean 1.000; N=3 (30 trials), public-only mean 1.300 with 23/30 unique and evaluation-only and joint unique in all trials; N=4 (30 trials), public-only mean 1.133 with 26/30 unique; N=5 (20 trials), public-only mean 1.050 with 19/20 unique; N=6 (10 trials), public-only mean 1.400 with 8/10 unique. Evaluation-only and joint filters had one survivor in all trials at N=3,4,5,6. These are tiny-modulus synthetic results and must not be extrapolated to the actual q or N=8192.

The four-way toy transcript generator follows the source-level distributions and equation conventions in src/keygen.rs: uniform ternary coefficients, independent uniform a-polynomials, and independent eta=2 centered-binomial errors. The implementation's error sampler (Binomial(2,1/2)-Binomial(2,1/2)) has the same law as the experiment's Binomial(4,1/2)-2 sampler. Only q=23 and N<=6 are toy substitutions; the production parameters remain a 218-bit aggregate Q and N=8192. The exhaustive counts therefore establish finite-instance filtering behavior only, not a scalable attack or a production security conclusion.

## Appendix G. Exact error distributions of target-cancelling combinations

We additionally examine integer vectors (w) satisfying (sum_j w_j B^j=0pmod Q), which cancel the common (s^2) target in a public linear combination of evaluation-key equations. Rather than ranking such relations only by a worst-case error bound, an exact dynamic-programming audit computes the one-coefficient probability mass function of (sum_j w_j e_j) under the implemented eta=2 centered-binomial law. We compare the adjacent-level relation with the Pareto frontier of the displayed LLL-reduced modular-kernel basis rows, using support radius, variance, central quantiles, and tail probabilities. These derived equations remain correlated linear combinations of the same original errors; marginal error improvements are not independent samples and do not by themselves constitute a distinguisher or key-recovery attack. The reported numerical findings below remain marginal-distribution and covariance diagnostics, not independent samples or a cryptanalytic result.


An exact SageMath audit computes one-coefficient error PMFs for the adjacent target-cancellation relation and the finite Pareto frontier among the displayed LLL basis rows. The adjacent relation has variance 4,294,967,297 and support radius 131,074. Two LLL rows reduce variance to 2,019,592,708 and 1,915,654,407, with 99% central quantiles 113,202 and 111,528, respectively, but their support radii increase to 216,808 and 271,334 and their extreme tails are nonzero. For example, the probability of absolute error exceeding 131,074 is 0.00242896662991 and 0.00227246486711 for these rows, versus zero for the adjacent relation. Neither LLL row dominates the adjacent relation at all tail thresholds.

The covariance between derived errors from weight vectors \((w,v)\) is exactly \(w\cdot v\), since the original independent eta=2 errors have unit variance. The six selected Pareto rows therefore remain correlated; the covariance between the two non-adjacent LLL Pareto rows is 213,075,963 (correlation approximately 0.10833). These are marginal distribution and covariance results, not independent extra samples, a distinguisher, a key-recovery attack, or a concrete security estimate. The finite Pareto comparison is restricted to the adjacent baseline and displayed LLL basis rows.


An exact joint candidate-filter audit enumerated all ternary secrets in toy negacyclic rings and compared the original evaluation-key residual constraints with the transformed anchor-plus-differences representation. The transformation retains the first residual `e_0` and all adjacent differences `z_j = e_(j+1) - B*e_j (mod q)`; recursively reconstructing `e_(j+1) = z_j + B*e_j (mod q)` and checking every reconstructed residual against the original support yields exactly the original candidate set. This was confirmed in all trials at `N=2,q=23` (40 trials), `N=2,q=257` (40), `N=5,q=65,537` (10), and `N=8,q=65,537` (3), with `B=4` for the first two and `B=16` for the latter two. The public-key residual constraint was included.

The coarse marginal relaxation `|z_j| <= 2(B+1)` admitted no extra candidates in those joint-filter trials. However, a separate evaluation-key-only stress test at `N=2,q=257,B=4` admitted three extra candidates in two of 20 trials (maximum three survivors), demonstrating that the widened marginal bounds can lose filtering power when the public-key constraint is absent. These exhaustive tests cover at most `3^8=6,561` candidates and are not a scalable key-recovery attack or a production security result.


A stagewise exhaustive audit tested (N=2), (B=2), six evaluation-key levels, eta=2 errors, and 200 synthetic transcripts at each of (q=17) and (q=19), enumerating all nine ternary secrets per transcript. The mean number of candidates after the public-key equation alone was 1.685 and 1.630, respectively. After the public-key equation and all six exact evaluation-key residual constraints, the mean survivor count was 1.000 in both cases. The exact anchor-plus-adjacent-differences filter matched the original residual filter at every stage and in every trial.

The marginal relaxation $|z_j|\le 2(B+1)$ admitted extra candidates: in the joint public-plus-evaluation filter, 7/200 trials at (q=17) and 2/200 at (q=19) had at least one extra candidate. The corresponding evaluation-only counts were 51/200 and 35/200. These deliberately low-modulus, two-coefficient exhaustive tests illustrate complementary filtering and information loss from marginal bounds; they are not scalable key-recovery attacks, production-parameter evidence, or security estimates.


The reporting rerun found that the public-key equation alone left multiple ternary candidates in 75/200 trials at (q=17) and 66/200 at (q=19). Adding the first evaluation-key level made the joint filter unique in 187/200 and 192/200 trials, respectively; adding the second made it unique in all 200 trials for both moduli. Evaluation-key-only filtering reached uniqueness in all trials by the third stage at (q=17) and the second at (q=19). Every trial retained at least one candidate. These are finite, low-modulus exhaustive-search observations only.


The dimension-growth exhaustive audit tested (N=3,4), $q\in\{17,19\}$, (B=2), six evaluation-key levels, and 100 seeded transcripts per setting. The ternary candidate spaces contained 27 and 81 secrets. The public-key equation alone left multiple candidates in 48/100, 36/100, 26/100, and 16/100 trials for ((N,q)=(3,17),(3,19),(4,17),(4,19)), respectively. After the first evaluation-key equation, the joint public-plus-evaluation filter was unique in 96/100, 94/100, 98/100, and 100/100 trials; after the second, the counts were 98/100, 99/100, 100/100, and 100/100. All four settings were unique in every trial by the third evaluation-key equation. The exact transformed filter matched the original residual filter at every stage. These are small-modulus exhaustive toy results only; in particular, public-key-only filtering already yielded uniqueness in many trials, and no production-dimension recovery or security claim follows.


## Appendix H. Extended conditional toy audits

The following exhaustive experiments extend the conditional candidate-filtering diagnostics across dimensions. In every setting, the candidate space is the full ternary space for the stated small (N), with toy moduli and bounded errors; these are not production-parameter attacks.

**Extended setting 1.** Parameters and trials: (N=5,6), $q\in\{17,19\}$; 50 trials per (N=5) setting and 30 per (N=6) setting; (B=2), six levels. The public-key equation was ambiguous in 18/50, 10/50, 11/30, and 8/30 trials, respectively. The joint public-plus-first-evaluation-key filter was unique in every trial; evaluation-key-only filtering reached uniqueness by the second tested level.

**Extended setting 2.** Parameters and trials: (N=2,3,4,5,6), $q\in\{17,19\}$; 960 seeded transcripts in aggregate. The public-key equation was ambiguous in 314/960 cases. Among those 314 ambiguous cases, the first evaluation-key level resolved 281, the second another 29, and the third the final four. Evaluation-key constraints did not change cases already unique from the public key.

**Extended setting 3.** Parameters and trials: (N=7,8), $q\in\{13,17\}$; 30 or 20 trials per setting; (B=2), six levels. The public-key equation was ambiguous in 28/30, 8/30, 20/20, and 4/20 trials, respectively. The first joint evaluation-key stage resolved all 60 ambiguous cases; the remaining 40 were already unique from the public-key equation.

Across these audits, every tested candidate set remained nonempty and retained the planted secret. Where the transformed anchor-plus-adjacent-differences filter was evaluated, it matched the original residual constraints exactly. The experiments enumerate at most (3^8=6{,}561) ternary candidates and use very small moduli. Their observations are conditional finite-sample results only: they do not establish scalable secret recovery, a production attack, or a concrete security estimate.

Reproducibility scripts and exact parameter grids are retained in the repository.

## References

[1] J. Fan and F. Vercauteren, “Somewhat Practical Fully Homomorphic Encryption,” IACR Cryptology ePrint Archive, Report 2012/144, 2012.

[2] J.-C. Bajard, J. Eynard, M. A. Hasan, and V. Zucca, “A Full RNS Variant of FV Like Somewhat Homomorphic Encryption Schemes,” in *Selected Areas in Cryptography — SAC 2016*, Lecture Notes in Computer Science, vol. 10532, pp. 423–442, Springer, 2017, doi: 10.1007/978-3-319-69453-5\_23.

[3] M. R. Albrecht, R. Player, and S. Scott, “On the concrete hardness of Learning with Errors,” *Journal of Mathematical Cryptology*, vol. 9, no. 3, pp. 169–203, 2015, doi: 10.1515/jmc-2015-0016.

[4] HomomorphicEncryption.org, *Homomorphic Encryption Standard*, community security-guidelines white paper adopted at the Third Standards Meeting, Toronto, Canada, Nov. 2018; IACR Cryptology ePrint Archive, Report 2019/939. This is community guidance, not a formal standard.

[5] J.-C. Bajard, J. Eynard, N. Merkiche, and T. Plantard, “RNS Arithmetic Approach in Lattice-Based Cryptography: Accelerating the ‘Rounding-off’ Core Procedure,” in *2015 IEEE 22nd Symposium on Computer Arithmetic (ARITH)*, pp. 113–120, 2015, doi: 10.1109/ARITH.2015.30.

[6] J.-P. Bossuat, R. Cammarota, I. Chillotti, B. R. Curtis, W. Dai, H. Gong, E. Hales, D. Kim, B. Kumara, C. Lee, X. Lu, C. Maple, A. Pedrouzo-Ulloa, R. Player, Y. Polyakov, L. A. Ruiz Lopez, Y. Song, and D. Yhee, “Security Guidelines for Implementing Homomorphic Encryption,” *IACR Communications in Cryptology*, vol. 1, no. 4, art. 26, 2025, doi: 10.62056/anxra69p1; ePrint 2024/463.

[7] A. Al Badawi, Y. Polyakov, K. M. M. Aung, B. Veeravalli, and K. Rohloff, “Implementation and Performance Evaluation of RNS Variants of the BFV Homomorphic Encryption Scheme,” *IEEE Transactions on Emerging Topics in Computing*, vol. 9, no. 2, pp. 941–956, 2021, doi: 10.1109/TETC.2019.2902799.

[8] S. Halevi, Y. Polyakov, and V. Shoup, “An Improved RNS Variant of the BFV Homomorphic Encryption Scheme,” *CT-RSA 2019*, LNCS, vol. 11405, pp. 83–105, 2019, doi: 10.1007/978-3-030-12612-4\_5.
