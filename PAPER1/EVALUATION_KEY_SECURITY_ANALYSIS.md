# Structured evaluation-key exposure: preliminary cryptanalytic analysis

## Status and scope

This note analyzes the public relinearization-key format implemented by `src/keygen.rs`. It is a threat-model and algebraic-structure note, **not** a security proof, attack implementation, or security estimate. No claim of IND-CPA security or a bit-security level is made.

## Exact public relation

The secret is a coefficientwise ternary polynomial
`s in R = Z_Q[X]/(X^8192+1)`. For each gadget level j, the implementation samples independent uniform `a_j in R_Q` and a centered-binomial error `e_j` with coefficient support [-2,2], and publishes `(b_j,a_j)` satisfying

```
b_j + a_j*s = B^j*s^2 + e_j  (mod Q),  B=2^16.
```

There are L=14 levels. Thus the adversary receives 14 related RLWE-like equations with:
- one common secret s;
- a common, secret-dependent target polynomial s^2;
- public, known multipliers B^j;
- independent uniform a_j;
- small bounded errors e_j.

This is not the ordinary LWE/RLWE sample model `b+a*s=e`. In particular, treating all 14 pairs as 14 ordinary RLWE samples with zero target is incorrect. The current `scripts/estimate_lwe_proxy.py` intentionally omits these samples and cannot estimate their contribution.

## Algebraic observations

1. The target is not an independent random message: it is the square of the same secret used in the linear term. This creates a related-key / auxiliary-input structure.
2. Since s is ternary, the coefficients of the integer negacyclic square s^2 have magnitude at most N, but this fact alone does not establish a useful attack or a security reduction.
3. For any j,k, public linear combinations can eliminate the formal s^2 target modulo Q, e.g.
   `B^k(b_j+a_j*s)-B^j(b_k+a_k*s)=B^k*e_j-B^j*e_k (mod Q)`.
   However, the corresponding coefficient of s is `B^k*a_j-B^j*a_k`, and the error is multiplied by large powers of B. This identity is not automatically a standard small-error RLWE sample: centered-lift sizes, modular wraparound, and the distribution of the combined error must be analyzed before treating it as an attack.
4. Multiplying each equation by B^{-j} modulo Q makes the target common, but also multiplies the small error by B^{-j} modulo Q. The centered representatives of these modular inverses are not generally small. This normalization therefore does not directly produce a standard small-error sample either.
5. Because the public key also exposes a conventional relation `b_pk+a_pk*s=e_pk`, the evaluation key must be assessed jointly with the public key, not in isolation.

## Required attack analysis

A cryptographic reviewer should investigate, at minimum:

- Joint recovery of s and/or s^2 from the public-key RLWE sample and all 14 evaluation-key equations.
- Whether the algebraic relation s^2 in the power-of-two cyclotomic ring yields exploitable polynomial constraints, including negacyclic convolution equations and the ternary coefficient restriction.
- Multi-sample, multi-target, related-message, hybrid, primal, dual, and algebraic attacks with the actual error and secret distributions.
- Whether linear combinations across gadget levels yield any useful low-noise equations after exact centered-lift analysis.
- The impact of publishing additional evaluation keys, repeated key generation under one secret, or multiple ciphertext/key-switch interfaces.
- Classical and quantum costs, attack-model assumptions, and the estimator's coverage limits.

The reviewer must work with the exact four-prime Q, N=8192, t=65537, B=2^16, L=14, ternary secret, and eta=2 centered-binomial error. Any proposed transformation must preserve the actual modular distribution; heuristic statements about "14 samples" are insufficient.

## Implementation implications

- Keep the evaluation key clearly classified as public auxiliary key material, but do not assume that "public" means harmless.
- Do not add more evaluation-key levels or publish additional related keys without re-running the security analysis.
- Do not claim that the unstructured-LWE estimator covers the evaluation key.
- The code's exhaustive coefficientwise test verifies the correctness of the key relation and small-error support. It does not test hardness.
- The secret-key wrapper's zeroization and the absence of a constant-time audit are separate implementation concerns.

## Current conclusion

The format exposes 14 structured, related RLWE-like samples with a common secret-dependent target s^2. The simple linear-combination identities above do not by themselves demonstrate a break, but they also prevent us from silently treating the samples as ordinary RLWE. Security remains unresolved pending a ring-aware, joint public-key/evaluation-key analysis and independent cryptographic review.

Until then, describe the construction as an experimental RNS-BFV prototype, not a security-validated FHE scheme.

## Joint-sample model: a more precise formulation

Write the published equation as
\(b_j=-a_js+B^js^2+e_j\pmod Q\). Equivalently, in the product ring \(R_Q^2\), it is a linear observation of the *related secret pair* \((s,s^2)\):
\[b_j=\langle(-a_j,B^j),(s,s^2)\rangle+e_j\pmod Q.\]
This is only an algebraic rewriting. It is **not** a standard rank-two RLWE instance: the second public coordinate is the known scalar polynomial \(B^j\), not an independently uniform ring element, and the two secret coordinates are algebraically dependent. Consequently, standard rank-two RLWE estimators or sample-count heuristics cannot be applied without a reduction or a justified distributional transformation.

The conventional public-key sample has a different form, \(b_{pk}=-a_{pk}s+e_{pk}\pmod Q\), with uniform \(a_{pk}\). The joint public transcript therefore contains one ordinary-looking RLWE relation plus the 14 structured related-target equations. A security analysis must treat the entire transcript as one distribution, rather than estimating the public key and evaluation key separately and adding nominal bit-security figures.

### What the current implementation establishes

- The source generates each \(a_j\) independently and uniformly in \(R_Q\), and samples each coefficient of \(e_j\) from the eta=2 centered-binomial support \([-2,2]\).
- The implementation uses \(B=2^{16}\), \(L=14\), and \(N=8192\).
- `gadget_decompose_centered` reconstructs each coefficient's centered CRT lift as a signed magnitude and emits ordinary base-\(B\) digits with the same sign. Thus each digit coefficient has magnitude at most \(B-1\), and the integer digit identity is exact for the centered lift.
- The relinearization phase error is \(\sum_j d_je_j\). For negacyclic convolution, \(\|d_je_j\|_\infty\le\|d_j\|_\infty\|e_j\|_1\), while the sampler support gives \(\|e_j\|_1\le2N\). Hence the deterministic bound \(L(B-1)2N=15,032,156,160\) is valid under the documented sampler and decomposition assumptions.

These are implementation and correctness facts, not evidence that recovering the secret is hard. The exhaustive unit test verifies the evaluation-key phase relation and CRT consistency for generated samples; it is not a cryptanalytic test.

### Concrete next cryptanalytic tasks

1. Formulate the exact joint distribution of \((a_{pk},b_{pk},(a_j,b_j)_{j=0}^{L-1})\), including the secret distribution and all error distributions.
2. Determine whether the known scalar sequence \(1,B,\ldots,B^{L-1}\) permits useful modular combinations after centered-lift analysis. Any claim of a small-error derived equation must bound the *centered representative* of every transformed error, not merely its symbolic expression.
3. Test algebraic attacks exploiting the coefficientwise ternary constraint and the relation \(s^2=s\cdot s\) in \(R_Q\). Distinguish attacks on the integer lift from attacks modulo \(Q\).
4. Evaluate whether repeated evaluation-key publication under the same secret changes the attack surface. The current generator produces one set of levels, but an API that republishes independent sets would create additional related samples.
5. Obtain an independent specialist review before assigning any concrete security level.

No attack or reduction is established by this note. Until the above work is completed, the security status remains unresolved.
## Adjacent-level cancellation: exact result

Define \(y_j=b_j+a_js=B^js^2+e_j\). For each adjacent pair of levels, subtracting \(B y_j\) from \(y_{j+1}\) cancels the target exactly:
\[
b_{j+1}-Bb_j+(a_{j+1}-Ba_j)s=e_{j+1}-Be_j\pmod Q.
\]
Thus each adjacent pair yields a derived RLWE-shaped equation with a uniform-looking coefficient \(a'_j=a_{j+1}-Ba_j\) and error \(e'_j=e_{j+1}-Be_j\). Since the original \(a_j\) are independent uniform ring elements and the adjacent-difference map has full row rank (the coefficient of \(a_{j+1}\) is 1), the vector \((a'_0,\ldots,a'_{L-2})\) is jointly uniform over \(R_Q^{L-1}\).

However, the errors are not independent across j: \(e'_j\) and \(e'_{j+1}\) both contain \(e_{j+1}\). Each coefficient of an individual derived error has absolute value at most \(2(1+B)=131,074\) before reduction modulo Q. Therefore this transformation exposes up to 13 correlated RLWE-shaped samples with a wider error distribution, not 13 independent standard eta=2 samples. The derived equations are deterministic functions of the original evaluation-key transcript and do not add information in an information-theoretic sense; they provide a useful alternative view for cryptanalysis.

**Interpretation:** the cancellation is exact and the uniformity claim concerns the joint coefficient vector only. It does not establish a practical attack. A proper estimator would need to handle the correlated error vector and its exact distribution; feeding 13 independent samples with a Gaussian error of guessed width into a conventional estimator would be an unjustified approximation. The next review should compare attacks on the original related-target transcript with attacks on this transformed correlated-error transcript.

### Coefficientwise support calculation

For eta=2 centered-binomial errors, each original coefficient lies in [-2,2]. Hence
\[|e'_{j,k}|=|e_{j+1,k}-B e_{j,k}|\le 2+2B=131,074.\]
This is a support bound on the unreduced integer expression. The actual public equation is modulo Q; centered modular representatives may wrap, so any lattice embedding or estimator must preserve the modular distribution rather than treating this support bound as a Gaussian standard deviation.
### Exact eta=2 error law and dependence

The implementation samples eta=2 as the difference of two independent Binomial(2, 1/2) variables. For one coefficient, the probability mass function on \(-2,-1,0,1,2\) is \((1,4,6,4,1)/16\), with mean zero and variance one.

For the adjacent cancellation errors \(e'_j=e_{j+1}-Be_j\), independence of the original level errors gives, coefficientwise,
\[\operatorname{Var}(e'_j)=1+B^2,\qquad \operatorname{Cov}(e'_j,e'_{j+1})=-B,\]
and \(\operatorname{Cov}(e'_j,e'_k)=0\) for \(|j-k|>1\). The adjacent correlation is \(-B/(1+B^2)\). Thus the error vector has a banded dependence structure; it is not an iid error vector. Coefficients at distinct polynomial positions remain independent under the coefficientwise sampler.

For B=65536, the individual coefficient variance is 4,294,967,297 and the standard deviation is approximately 65,536.000008. This standard deviation is descriptive, not a replacement for the exact discrete law or a proof that a Gaussian estimator is valid. The support bound remains 131,074.

For the thirteen-level transformed error vector at one fixed polynomial coefficient, the full covariance matrix is the tridiagonal matrix
\[
\Sigma=
\begin{pmatrix}
1+B^2&-B&0&\cdots&0\\
-B&1+B^2&-B&\ddots&\vdots\\
0&-B&1+B^2&\ddots&0\\
\vdots&\ddots&\ddots&\ddots&-B\\
0&\cdots&0&-B&1+B^2
\end{pmatrix}\in\mathbb Z^{13\times13}.
\]
The transformed coefficient vector is independent of this error vector because all original uniform coefficients and error samples are generated independently. Across different polynomial coefficient positions, the transformed error vectors are independent under the coefficientwise sampler. This describes the exact second moments and dependence pattern; it does not replace the discrete joint probability law needed by an attack or estimator.

### Correct interpretation of the transformed samples

The map from \((a_0,\ldots,a_{L-1})\) to \((a_1-Ba_0,\ldots,a_{L-1}-Ba_{L-2})\) is a surjective linear map over \(R_Q\): its matrix has a unit coefficient on each successive pivot. Therefore the transformed coefficient vector is jointly uniform. This does not make the errors independent, and the transformed transcript is a deterministic function of the original transcript. The transformation is a cryptanalytic viewpoint, not additional leakage beyond the published key.
## Ternary-secret structure in the square

Let \(s(X)=\sum_{i=0}^{N-1}s_iX^i\), with independent \(s_i\in\{-1,0,1\}\), and compute the negacyclic square in \(\mathbb Z[X]/(X^N+1)\). Reducing its coefficients modulo 2 removes signs and all cross-term pairs, because every off-diagonal product appears twice:
\[s(X)^2\equiv\sum_{i=0}^{N-1}s_i^2X^{2i}\equiv\sum_{i=0}^{N-1}s_iX^{2i}\pmod 2.\]
For even N, reducing exponents modulo \(X^N+1\) (which equals \(X^N-1\) over \(\mathbb F_2\)) gives
\[ [X^{2r+1}]s^2\equiv0\pmod2,\qquad [X^{2r}]s^2\equiv s_r+s_{r+N/2}\pmod2,\quad 0\le r<N/2.\]
The second identity includes **both** indices whose doubled exponents reduce to \(2r\) modulo N. In particular, the even coefficient parity reveals the XOR of the nonzero indicators of two secret coefficients, not either coefficient individually.

For N=8192 this means every odd-index coefficient of the integer negacyclic square is even, while each even-index coefficient gives the parity of the pair \((s_r,s_{r+4096})\). This is a genuine algebraic property of the target polynomial, not yet a key-recovery attack: the public evaluation-key equations expose the target only mixed with the unknown term \(-a_js\) and modular noise. A practical attack would still need to extract these parities from the joint public transcript.

### Attack relevance and caveats

- The parity statement is over the integer coefficient representation of the ternary secret and its negacyclic square. It is not automatically observable from an RNS residue without a justified centered-lift reconstruction.
- Since Q is odd, reducing a residue modulo Q and then reducing that residue modulo 2 is not a valid substitute for recovering the intended integer representative. Any proposed parity test must account for modular wraparound.
- The even-index parity relation covers only the first N/2 secret coefficients in this chosen coefficient ordering; it does not directly reveal the remaining half.
- This constraint can be used as a target in algebraic or hybrid cryptanalysis, but no complexity reduction or exploitable distinguisher is established here.

A separate exact implementation test should verify this identity on many sampled ternary secrets and on the same CRT centered-lift convention used by the evaluation-key generator before this observation is used in any attack code.
## Why the mod-2 identity is not directly visible in the public transcript

The parity identity for the integer polynomial \(s^2\) is not itself a parity leak from an RNS ciphertext or evaluation-key component. Since Q is odd, there is no well-defined ring homomorphism \(\mathbb Z/Q\mathbb Z\to\mathbb F_2\): the relation \(Q\cdot1=0\) in the source would map to \(Q\cdot1=1\) in \(\mathbb F_2\), a contradiction. Therefore taking a canonical residue modulo Q and then reducing it modulo 2 does not preserve the intended integer parity.

Even if an attacker could recover a suitable centered integer lift of \(b_j+a_js\), the lift still contains the unknown product \(a_js\) and the error term. The algebraic parity constraint applies to the hidden target \(s^2\), not directly to the published component \(b_j\).

### Current attack conclusion

The ternary-square parity identity is a valid structural constraint and is now covered by a deterministic CI audit. However, the present public transcript gives no direct route to read those parities: (i) modular reduction by odd Q does not preserve parity, (ii) the target is masked by the unknown secret-dependent product \(a_js\), and (iii) the adjacent-level cancellation removes the target rather than exposing it. No parity-based distinguisher or key-recovery algorithm has been demonstrated.

A meaningful next experiment would require an explicit attack model that jointly handles the public-key sample, all evaluation-key samples, modular centered lifts, and the ternary constraint. Until such a model exists, this parity observation should be reported as an algebraic property—not as a vulnerability or a security improvement.

## Staged candidate-filtering experiment (toy diagnostic)

A new deterministic audit, `scripts/audit_evalkey_filtering.py`, measures candidate-set sizes after the public-key equation and after each of three successive evaluation-key levels. It exhaustively enumerates ternary secrets for (N\in\{4,6,8\}), using (q=11), (B=3), eta=2, 30 instances per degree, and a fixed seed. It asserts that the planted secret survives every stage and that candidate counts are non-increasing.

The purpose is narrower than a key-recovery claim: it quantifies the incremental filtering effect of the published evaluation-key equations *conditional on* the public-key candidate set in this toy distribution. It does not estimate production attack complexity, extrapolate to (N=8192), or establish a security level. The toy modulus/base and number of levels differ from the implementation parameters, and exhaustive search itself dominates the method.

The Python CI job reported the following 30-instance results (medians; counts are after the public equation and then levels 1, 2, and 3):

| Degree | Median survivors | Mean survivors | Unique instances after public / level 1 / level 2 / level 3 |
|---|---:|---:|---:|
| N=4 | 4 / 1 / 1 / 1 | 5.10 / 1.367 / 1.067 / 1.00 | 2 / 24 / 28 / 30 of 30 |
| N=6 | 8 / 1 / 1 / 1 | 9.10 / 1.20 / 1.00 / 1.00 | 0 / 24 / 30 / 30 of 30 |
| N=8 | 12.5 / 1 / 1 / 1 | 12.90 / 1.00 / 1.00 / 1.00 | 0 / 30 / 30 / 30 of 30 |

In these toy instances the first evaluation-key level is already highly selective, and later levels remove the remaining ambiguity in some trials. This is a candidate-filtering observation under exhaustive ternary enumeration—not a practical attack: the attacker-side search still enumerates all (3^N) secrets, and the experiment uses (q=11), (B=3), only three levels, and (N\le8). The result does not quantify attack cost at the implementation parameters.

## Adjacent-level linear prefilter experiment

The exact cancellation identity gives, for adjacent levels (j,j+1),
[
(b_{j+1}-Bb_j)+(a_{j+1}-Ba_j)s=e_{j+1}-Be_jpmod Q.
]
For coefficient errors supported on ([-eta,eta]), the transformed error is supported on ([-eta(1+B),eta(1+B)]). Thus a candidate secret can be tested against this *linear* equation before computing its square. This is a safe necessary filter: every genuine secret passes, while the larger support radius deliberately avoids rejecting valid candidates.

The new `scripts/audit_evalkey_linear_prefilter.py` exhaustively measures candidate counts after the public-key relation, after each of the two adjacent-level cancellations, and then after the original three quadratic evaluation-key equations. The final measured configuration is q=29, B=3, eta=3, and N in {4,6,8}, with 30 deterministic instances per degree. The transformed support radius is 12, strictly below q/2, avoiding ambiguity in the centered-residue test. Eta=3 is deliberately a toy stress setting to retain some false candidates after the public filter; it differs from the implementation's eta=2 sampler and is not a model of the production error distribution. The Python audit passed in CI run #496.
 
| Degree | Mean survivors by stage | Unique-candidate instances by stage |
|---|---|---|
| N=4 | 1.300, 1.167, 1.100, 1.000, 1.000, 1.000 | 23, 26, 27, 30, 30, 30 / 30 |
| N=6 | 1.267, 1.100, 1.033, 1.000, 1.000, 1.000 | 27, 28, 29, 30, 30, 30 / 30 |
| N=8 | 1.000 at every stage | 30 at every stage |

The median candidate count was already one at the public-key stage for all three degrees. The linear filters improved uniqueness in a small number of ambiguous instances (four additional unique cases at N=4 and two at N=6 after both cancellations), but their median candidate count did not change. The three quadratic evaluation equations then produced a unique candidate in all 30 instances at every degree. This is measurable but modest incremental filtering, not evidence of a practical attack. It is also a very small toy sample and not an estimate for the production ring.

This is a toy diagnostic and does not imply production attack feasibility.


---

# Joint cryptanalytic assessment — four-part review

This section consolidates the next four tasks into a single explicit assessment. It is a model and attack-applicability review, not an assertion that the listed attacks have been exhaustively optimized or that the construction is secure.

## 1. Exact joint distribution of the public transcript

Let
\[
R_Q=\mathbb Z_Q[X]/(X^N+1),\quad N=8192,\quad
Q=\prod_{i=0}^{3}q_i,
\]
with the four RNS primes specified in the manuscript. Let the secret coefficients be independent uniform elements of \(\{-1,0,1\}\), let \(\chi_{2}\) denote the implemented eta=2 centered-binomial coefficient law, and let \(U(R_Q)\) denote the uniform distribution on the finite ring.

The complete key transcript considered here is
\[
T=(a_{pk},b_{pk},(a_j,b_j)_{j=0}^{13}),
\]
generated by first drawing one secret \(s\), then drawing all masks and errors independently:
\[
s\leftarrow\chi_s^N,\quad
a_{pk},a_0,\ldots,a_{13}\stackrel{\rm iid}{\leftarrow}U(R_Q),\quad
e_{pk},e_0,\ldots,e_{13}\stackrel{\rm iid}{\leftarrow}\chi_2^N,
\]
and setting
\[
b_{pk}=-a_{pk}s+e_{pk},\qquad
b_j=-a_js+B^js^2+e_j\pmod Q,
\quad B=2^{16}.
\]
Here \(s^2\) is the negacyclic square in \(R_Q\); the coefficient sampler is the exact eta=2 law with probability masses \((1,4,6,4,1)/16\) on \((-2,-1,0,1,2)\).

Equivalently, the transcript distribution is the mixture over the *single shared secret*:
\[
\Pr[T=t]=
\sum_{s\in\{-1,0,1\}^{N}}3^{-N}
\Pr[a_{pk},a_0,\ldots,a_{13}]
\Pr[e_{pk},e_0,\ldots,e_{13}]
\mathbf 1\{\text{all displayed modular equations hold for }t,s\}.
\]
The masks are uniform and the errors are independent before the equations are formed; the public outputs are not independent conditioned only on the published transcript because every equation shares \(s\), and the evaluation equations additionally share \(s^2\). This is the distribution an attack must address. It is not equivalent to 15 unrelated ordinary RLWE samples, nor to 14 independent samples with an independent second secret.

This formalization assumes one public-key sample and one set of fourteen evaluation-key levels generated under one secret, exactly as in the inspected key-generation source. It does not silently include repeated key generations, other key-switch keys, ciphertexts, or oracle access; those must be added to the threat model if the API publishes them.

## 2. Correlations and exact adjacent-level transformation

Define
\[
a'_j=a_{j+1}-Ba_j,\qquad
b'_j=b_{j+1}-Bb_j,\qquad
e'_j=e_{j+1}-Be_j,
\quad 0\le j<13.
\]
Then the target cancels exactly:
\[
b'_j+a'_js=e'_j\pmod Q.
\]
The map from the fourteen original masks to the thirteen transformed masks is surjective over \(R_Q\), since its matrix has a unit pivot in each successive column. Thus the *joint vector* \((a'_0,\ldots,a'_{12})\) is uniform over \(R_Q^{13}\). It is independent of the transformed error vector. This is a statement about the masks, not a claim that the derived equations are independent samples.

For each fixed polynomial coefficient position, the exact unreduced error law is the linear image of fourteen independent eta=2 variables:
\[
(e'_0,\ldots,e'_{12})=(e_1-Be_0,\ldots,e_{13}-Be_{12}).
\]
Consequently:
- each coordinate has support \([-2(1+B),2(1+B)]=[-131074,131074]\);
- each coordinate has variance \(1+B^2=4,294,967,297\);
- adjacent covariance is \(-B=-65,536\);
- non-adjacent covariance is zero;
- adjacent correlation is \(-B/(1+B^2)\), approximately \(-1.5258789\times10^{-5}\).

The covariance matrix is tridiagonal, but covariance alone is not the full distribution: each coordinate is a discrete convolution and neighboring coordinates share one original error variable. The modular public relation is reduced modulo Q, so any attack embedding must preserve the actual modular distribution and possible centered-representative wraparound. The support radius is not a Gaussian standard deviation and must not be passed to a conventional iid-error estimator as if it were one.

The transformation is deterministic post-processing of the published evaluation key. It supplies an alternative set of thirteen correlated-error, target-cancelled equations. It does not create new information or turn the transcript into thirteen independent eta=2 RLWE samples. In addition, the original public-key sample remains part of the joint transcript and is not eliminated by this transformation.

## 3. Applicability of attack families

The following table separates attacks that are meaningful to investigate from attacks for which the current estimator run supplies no valid result.

| Attack family | Relevance to this construction | What is currently established |
|---|---|---|
| Primal / uSVP lattice attacks | Relevant to the ordinary public-key RLWE component and potentially to a justified embedding of a transformed joint system | The Sage run estimates uSVP only for a scalar unstructured-LWE proxy; it does not estimate the ring or joint transcript |
| Dual / dual-hybrid attacks | Relevant to ordinary RLWE/LWE samples and potentially to correlated transformed equations if their exact law is modelled | The Sage run reports dual-hybrid only for the scalar proxy; no valid evaluation-key cost follows |
| Multi-sample / multi-target attacks | Relevant because many equations share one secret and related target | Sample counts cannot simply be added; no joint cost estimate has been derived |
| Related-target / auxiliary-input attacks | Directly relevant to the shared target \(s^2\) | The relation is explicit; no recovery algorithm or reduction is established |
| Algebraic / hybrid attacks using ternary coefficients and \(s^2\) | Relevant in principle because the secret is ternary and the target is its negacyclic square | A mod-2 identity for the hidden integer square is documented, but it is not directly observable from residues modulo odd Q and no distinguisher is known |
| Linear combinations across gadget levels | Directly relevant and exactly analyzable | Target cancellation and correlated-error law are derived; no practical attack cost is established |
| Ring-specific attacks | Essential to a final Ring-LWE assessment | Not evaluated by the scalar LWE proxy |
| BKW / Arora–Ge / other specialized LWE algorithms | May be relevant depending on the exact ring, sample, and noise model | Not covered by the bounded rough-profile run; applicability and cost for this joint distribution remain undetermined |
| Repeated-key / oracle-assisted attacks | Relevant if deployment publishes multiple independent evaluation-key sets under the same secret or exposes additional interfaces | Not part of the inspected one-key-generation transcript; deployment assumptions must be specified |

Accordingly, it is accurate to say that primal/dual methods are relevant baseline families for the ordinary-looking public-key component, and that related-target, ring-aware, algebraic, and hybrid methods should be investigated for the complete construction. It is not accurate to say that any one of these has been successfully applied to the complete transcript, or that the existing \(2^{93.732}\) proxy output bounds its security.

A specialist attack study should begin from the exact distribution in Part 1 and compare at least (i) the original related-target representation and (ii) the adjacent-cancellation representation with its exact correlated errors. Any Gaussian approximation, lattice embedding, or sample reduction must be justified against the discrete modular law before its cost is treated as meaningful.

## 4. Security conclusions and publication language

### Conclusions supported now

1. The implementation generates one ternary secret, one ordinary public-key relation, and fourteen evaluation-key relations sharing the same secret and its square.
2. The adjacent-level target cancellation is an exact algebraic identity. The transformed masks are jointly uniform, while the transformed errors have the explicitly derived banded dependence.
3. The bounded SageMath run is reproducible evidence for a *scalar unstructured-LWE screening proxy* under its stated rough profile. Its candidate output is \(\log_2(\mathrm{rop})=93.732\) for the two reported attacks.
4. The correctness tests establish the tested arithmetic relations and sampler supports. The toy candidate-filter experiments establish only their reported tiny-parameter observations.

### Conclusions not supported now

- No concrete security level for the RNS-BFV construction.
- No proof or reduction from standard Ring-LWE, LWE, or a related-target assumption.
- No claim that the evaluation key is harmless merely because it is public.
- No claim that fourteen evaluation-key levels are fourteen independent standard RLWE samples.
- No claim that the transformed thirteen equations are independent or have iid Gaussian errors.
- No 128-bit security claim, no security lower bound, and no assertion of post-quantum security at a specified level.
- No production-readiness claim based on the correctness tests or the scalar proxy.

### Recommended manuscript statement

> The public evaluation key comprises fourteen related-target equations sharing the secret and its negacyclic square. We derive an exact adjacent-level transformation that cancels the square target and yields thirteen equations with jointly uniform masks and a banded, correlated discrete error vector. This characterization is an algebraic description, not a security reduction or a demonstrated attack. A bounded unstructured-LWE proxy was evaluated separately, but it does not model the ring structure or the evaluation-key transcript. We therefore make no concrete scheme-level security claim; a ring-aware joint cryptanalysis and independent specialist review remain necessary.

### Decision and next research gate

For the current paper, retain the implementation and correctness contributions, report the scalar proxy only with its limitations, and label the cryptographic security assessment unresolved. Before claiming a concrete security level or presenting this as a security-validated FHE scheme, require an independent reviewer to assess the exact joint transcript, ring structure, secret distribution, correlated errors, and any additional deployment interfaces. Any new evaluation-key publication under the same secret must trigger a fresh transcript-level analysis.

This is the current defensible boundary between what has been derived, what has been experimentally checked, and what remains an open cryptanalytic question.


---

## 5. Computational search for short modular target-cancellation relations

A SageMath 10.10 experiment was added as `scripts/search_evalkey_short_relations.sage.py` and executed in GitHub Actions run [#595](https://github.com/jbenavidesj/lattice-fhe-ppml/actions/runs/43362037142). It constructs the exact 14-dimensional integer kernel lattice
\[
\Lambda=\{w\in\mathbb Z^{14}:\sum_{j=0}^{13}w_jB^j=0\pmod Q\}
\]
and applies exact-integer LLL with \(\delta=0.99\). The basis determinant is checked to equal \(Q\), and every output row is verified against the modular relation.

### Observed result

The three shortest reported rows have \(\ell_1\)-norm 65,537 and are adjacent-level relations, equivalent up to sign and level position to \(( -B,1)\). The next LLL row has
\[
\|w\|_1=108,404,\qquad \|w\|_2^2=2,019,592,708,
\qquad \|w\|_\infty=28,350.
\]
It therefore has a larger worst-case support bound \(2\|w\|_1=216,808\) than the adjacent relation's 131,074, but a smaller coefficient-variance proxy \(\|w\|_2^2\) than the adjacent relation's 4,294,967,297. This is a real trade-off between worst-case support and second moment; neither metric alone establishes a more useful attack sample.

No LLL-reduced row in this run improves on the adjacent relation in \(\ell_1\)-norm. The experiment is a search within one reduced basis, not an exhaustive enumeration of all short lattice vectors and not a proof that no shorter vector exists. LLL output also depends on the chosen basis and reduction parameters.

### Interpretation and limits

The result gives no secret-recovery algorithm, no distinguisher, and no security estimate. The linear combinations are deterministic functions of one public transcript and are not independent samples. A lower \(\ell_2^2\) value may motivate a follow-up analysis of the exact weighted discrete error law, but it does not justify replacing that law by an iid Gaussian with the same variance. Any further attack experiment must model the coefficient weights, negacyclic ring operations, modular wraparound, and dependencies among multiple derived equations.

The SageMath workflow run completed successfully, including the relation search and artifact upload. The full output is preserved in the `sage-lwe-proxy-diagnostic` workflow artifact for run #595.


## 6. Exact one-coefficient weighted-error distribution

For the adjacent vector \((-B,1,0,\ldots,0)\) and the rank-6 LLL vector
\[
w=(16395,-2246,11538,-2352,-15966,-4494,13649,15421,21740,-8852,532,11216,-2,11264),
\]
we computed the exact marginal distribution of one coefficient of \(E_w=\sum_jw_je_j\), using the exact eta=2 law. Each eta=2 variable is represented as \(\operatorname{Binomial}(4,1/2)-2\); integer dynamic programming therefore gives exact counts, not a Gaussian approximation. Both vectors were verified to cancel \(\sum_jw_jB^j\) modulo \(Q\).

| Statistic | Adjacent vector | Rank-6 vector |
|---|---:|---:|
| \(\|w\|_1\) | 65,537 | 135,667 |
| \(\|w\|_2^2=\operatorname{Var}(E_w)\) | 4,294,967,297 | 1,915,654,407 |
| Exact support radius | 131,074 | 271,334 |
| Central 99% quantile | 131,073 | 111,528 |
| Central 99.9% quantile | 131,074 | 140,667 |
| Central 99.99% quantile | 131,074 | 164,076 |

The rank-6 vector has lower variance and a narrower central 99% interval, but substantially wider support and worse 99.9% and 99.99% central quantiles. Its distribution is therefore not uniformly better: it has a more concentrated centre and heavier far tails. For example, the exact probability \(\Pr[|E_w|>131074]\) is zero for the adjacent vector and approximately 0.0022724649 for the rank-6 vector. The adjacent vector's support bound is exact and attained only at its extreme outcomes.

This demonstrates why variance alone is inadequate for assessing a discrete error distribution. The exact PMF is a one-coefficient marginal for one fixed linear combination. It does not give a security estimate, does not model the joint distribution across all thirteen transformed equations, and does not establish that a lattice attack can exploit this vector. The cross-equation dependence inherited from the original fourteen errors must be retained in any attack analysis.

The reproducible implementation is `scripts/audit_evalkey_weighted_error_distribution.py`; it is run by the SageMath workflow and its output is uploaded as `evalkey-weighted-error-distribution.txt`.


## 7. Joint law of all thirteen adjacent-cancellation errors

For one fixed polynomial coefficient position, write the fourteen independent eta=2 errors as
\[
e=(e_0,\ldots,e_{13})^T,\qquad z=De,
\]
where \(D\in\mathbb Z^{13\times14}\) has entries \(D_{j,j}=-B\) and \(D_{j,j+1}=1\). The exact covariance matrix is
\[
C=DD^T=
\begin{pmatrix}
B^2+1&-B&0&\cdots&0\\
-B&B^2+1&-B&\ddots&\vdots\\
0&-B&B^2+1&\ddots&0\\
\vdots&\ddots&\ddots&\ddots&-B\\
0&\cdots&0&-B&B^2+1
\end{pmatrix}.
\]
It is strictly diagonally dominant, with margin \((B-1)^2=4,294,836,225>0\), hence positive definite. Its exact determinant, obtained by the continuant recurrence \(d_0=1\), \(d_1=B^2+1\), \(d_n=(B^2+1)d_{n-1}-B^2d_{n-2}\), is
\[
\det C=
169230328049705647537258792534764699379076729544064679608111008719715824544689093686379525903645691337158953059330845948510209.
\]
The nonzero adjacent off-diagonal entries prove that neighboring transformed errors are statistically dependent; zero non-adjacent covariance does not imply mutual independence of all thirteen coordinates.

The full one-coefficient joint characteristic function is available exactly in factorized form. Since an eta=2 variable has characteristic function \(\varphi_X(u)=\cos^4(u/2)\), for \(t\in\mathbb R^{13}\),
\[
\varphi_z(t)=\prod_{k=0}^{13}\cos^4\!\left(\frac{(D^Tt)_k}{2}\right),
\]
where \((D^Tt)_0=-Bt_0\), \((D^Tt)_k=t_{k-1}-Bt_k\) for \(1\le k\le12\), and \((D^Tt)_{13}=t_{12}\). This is the exact discrete joint law in characteristic-function form, not a Gaussian approximation. Under independent coefficient sampling, the coefficient-position vectors are independent before any ring multiplication or other polynomial transformation is applied.

The reproducible audit is `scripts/audit_evalkey_joint_error_covariance.py`. It checks the exact integer covariance entries, determinant recurrence, strict diagonal-dominance margin, and prints the characteristic-function factorization. This is a distributional characterization of the derived errors; it does not by itself give an attack, distinguisher, secret-recovery method, or security estimate.


## 8. Exhaustive toy-ring candidate-filter comparison

The script `scripts/audit_evalkey_toy_secret_filtering.py` exhaustively enumerates all ternary secrets in two deliberately small negacyclic rings. It generates synthetic public evaluation-key equations with the exact eta=2 coefficient sampler and checks candidate residuals against the original error support \([-2,2]\). It then applies the adjacent target-cancellation equations with the necessary worst-case difference support \([-2(B+1),2(B+1)]\), using \(B=4\).

| Toy experiment | Trials | Original survivors (total) | Transformed survivors (total) | Trials with extra transformed candidates |
|---|---:|---:|---:|---:|
| \(N=2,q=257,L=2\) | 20 | 20 | 23 | 2 |
| \(N=8,q=65537,L=14\) | 10 | 10 | 10 | 0 |

In the first experiment, two trials admit additional candidates after transformation: one has two transformed survivors and one has three, while each original-equation filter has exactly one survivor. In the second experiment, all ten trials have exactly one survivor under both filters. In every trial, the planted secret survives both filters and the original candidate set is a subset of the transformed candidate set, as required by the algebraic implication.

This is a useful negative control: eliminating the shared \(s^2\) target and replacing the original residual constraints with wider difference-error bounds can lose filtering information. The small-ring ambiguity is not evidence of a weakness in the real parameter set; the scaled toy experiment's uniqueness is not evidence of security either. These are exhaustive candidate counts only for the stated toy parameters, not a scalable recovery algorithm, attack-cost estimate, or security proof.

The CI step is `Exhaustively compare toy-ring secret candidate filters`; its output is uploaded as `evalkey-toy-secret-filtering.txt`.


## 9. Exact joint original/transformed candidate constraints

The earlier toy comparison replaced the original evaluation-key residual tests with the coordinatewise support bound for adjacent differences. That is a deliberately conservative rectangular relaxation: it preserves the planted secret but can admit additional candidates. It does not use the exact joint support induced by the shared original errors.

A new exhaustive audit, scripts/audit_evalkey_joint_candidate_filter.py, compares three filters on the same synthetic transcript, including the ordinary public-key sample:

1. **Original:** require the public-key residual and every original evaluation-key residual to lie in the exact eta=2 support [-2,2].
2. **Coarse transformed:** require the public-key residual, the first original evaluation-key residual, and each adjacent difference to lie in the coordinatewise support box [-2(B+1),2(B+1)].
3. **Exact joint transformed:** pin the first error vector e_0 using the first original evaluation-key equation, then use each transformed residual z_j=e_{j+1}-B e_j to reconstruct the same next error vector by
\[
e_{j+1}=z_j+B e_j\pmod q,
\]
taking centered representatives. The test rejects as soon as any reconstructed coefficient leaves [-2,2]. For the stated toy moduli, the transformed support radius is strictly below q/2, so centered representatives are unambiguous.

This recurrence is important: the thirteen transformed errors are not thirteen independent draws. Once e_0 is fixed, the entire error sequence is determined by the transformed residuals. Therefore the exact joint transformed support test plus the first original equation is algebraically equivalent to checking all original evaluation-key residuals. It does not add information to the transcript and does not create an attack; it is an alternative exact way to enforce the same constraints. By contrast, the coarse rectangular bound forgets the shared-error recurrence and can retain false candidates.

### Exhaustive toy results

The audit exhaustively enumerates all 3^N ternary secrets for each trial:

| Configuration | Trials | Mean original survivors | Mean exact-joint survivors | Mean coarse survivors | Extra coarse candidates |
|---|---:|---:|---:|---:|---:|
| N=2, q=23, B=4, L=2 | 40 | 1.000 | 1.000 | 1.250 | 10 total |
| N=5, q=65537, B=16, L=6 | 10 | 1.000 | 1.000 | 1.000 | 0 |

For every trial, the original and exact-joint candidate sets were identical, and the planted secret survived. In the small-ring case, the coarse filter retained ten extra candidates across 40 trials (some trials retained two, three, or four candidates). In the medium toy case, all three filters retained only the planted candidate in every trial.

These results confirm the set-equivalence of the exact recurrence in the tested toy instances and illustrate the information loss caused by replacing the joint support with a coordinatewise box. They do not demonstrate scalable secret recovery: the largest search space here is only 3^5=243, and all candidates are enumerated. The medium toy's unique candidate is not evidence of production security.

### Validation correction for workflow run #617

Inspection of the downloaded artifact and SageMath job log for run #617 revealed that three Python audit steps in the SageMath container invoked python, which is not installed there. Those commands failed with "python: not found"; because the shell pipeline did not enable pipefail, the subsequent tee exit status masked the failures and the overall job was incorrectly reported as successful. The corresponding three artifact files were empty. The scalar LWE proxy and SageMath LLL relation search did run, but run #617 is **not** valid evidence that the weighted-error, covariance, or earlier toy-filter scripts passed in that container.

The workflow has therefore been corrected to invoke these scripts with sage -python, capture and propagate each Sage script's exit status explicitly (without a masking tee pipeline), and include the new exact-joint candidate-filter audit. The next CI run must be checked step-by-step and its artifact contents inspected before recording these audits as passed.
