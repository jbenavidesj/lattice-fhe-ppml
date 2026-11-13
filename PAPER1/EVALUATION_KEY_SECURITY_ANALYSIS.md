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

### Correct interpretation of the transformed samples

The map from \((a_0,\ldots,a_{L-1})\) to \((a_1-Ba_0,\ldots,a_{L-1}-Ba_{L-2})\) is a surjective linear map over \(R_Q\): its matrix has a unit coefficient on each successive pivot. Therefore the transformed coefficient vector is jointly uniform. This does not make the errors independent, and the transformed transcript is a deterministic function of the original transcript. The transformation is a cryptanalytic viewpoint, not additional leakage beyond the published key.
## Ternary-secret structure in the square

Let \(s(X)=\sum_{i=0}^{N-1}s_iX^i\), with independent \(s_i\in\{-1,0,1\}\), and compute the negacyclic square in \(\mathbb Z[X]/(X^N+1)\). Reducing its coefficients modulo 2 removes signs and all cross-term pairs, because every off-diagonal product appears twice:
\[s(X)^2\equiv\sum_{i=0}^{N-1}s_i^2X^{2i}\equiv\sum_{i=0}^{N-1}s_iX^{2i}\pmod 2.\]
For even N, reducing exponents modulo \(X^N+1\) (which is \(X^N-1\) over \(\mathbb F_2\)) gives
\[ [X^{2r+1}]s^2\equiv0\pmod2,\qquad [X^{2r}]s^2\equiv s_r\pmod2,\quad 0\le r<N/2,\]
where coefficient indices are interpreted in the negacyclic ring and the displayed even-index identity uses \(s_r^2\equiv s_r\pmod2\).

For N=8192 this means every odd-index coefficient of the integer negacyclic square is even, and the parity of its even-index coefficients reveals the parity (zero versus nonzero) of the first 4096 secret coefficients. This is a genuine algebraic property of the target polynomial, not yet a key-recovery attack: the public evaluation-key equations expose the target only mixed with the unknown term \(-a_js\) and modular noise. A practical attack would still need to extract these parities from the joint public transcript.

### Attack relevance and caveats

- The parity statement is over the integer coefficient representation of the ternary secret and its negacyclic square. It is not automatically observable from an RNS residue without a justified centered-lift reconstruction.
- Since Q is odd, reducing a residue modulo Q and then reducing that residue modulo 2 is not a valid substitute for recovering the intended integer representative. Any proposed parity test must account for modular wraparound.
- The even-index parity relation covers only the first N/2 secret coefficients in this chosen coefficient ordering; it does not directly reveal the remaining half.
- This constraint can be used as a target in algebraic or hybrid cryptanalysis, but no complexity reduction or exploitable distinguisher is established here.

A separate exact implementation test should verify this identity on many sampled ternary secrets and on the same CRT centered-lift convention used by the evaluation-key generator before this observation is used in any attack code.