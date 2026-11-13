# One-multiplication correctness bound for the N=8192 RNS-BFV path

## Scope

This is a deterministic correctness bound for **one ciphertext multiplication followed by one gadget relinearization**, using the exact integer-lift multiplication and rounding conventions implemented in \`src/rns.rs\` and \`src/keygen.rs\`. It is not a security estimate, a multiplicative-depth theorem, or a constant-time claim.

The parameter instance is:
- \(N=8192\), \(R=\mathbb Z[X]/(X^N+1)\);
- \(Q=\prod_i q_i\), with the four configured RNS primes, \(\log_2 Q\approx218\);
- \(t=65537\), \(\Delta=\lfloor Q/t\rfloor\), and \(r=Q-t\Delta=2539\);
- ternary secret and ephemeral coefficients in \(\{-1,0,1\}\);
- public-key and encryption errors sampled from centered-binomial \(\eta=2\), support \([-2,2]\);
- gadget base \(B=2^{16}\), \(L=14\) digits.

The auxiliary nine-prime NTT/CRT basis used by the integer tensor-product routine has a 468-bit product \(P\). For any *single* product of two centered input polynomials, each coefficient has absolute value at most
\[
N(Q/2)^2.
\]
The centered CRT reconstruction is therefore unique when
\[
P>2N(Q/2)^2=NQ^2/2,
\]
which the Rust unit test checks as \(2P>NQ^2\). An important implementation detail is that the cross component is **not** reconstructed as one combined convolution: \`src/rns.rs\` computes \(\hat c_0\hat d_1\) and \(\hat c_1\hat d_0\) in two separate exact auxiliary-CRT calls, reconstructs each signed product independently under this bound, and only then adds their \`BigInt\` coefficient vectors. Thus the single-product CRT bound is sufficient for all three tensor components. The subsequent addition is exact integer arithmetic and does not require a larger auxiliary CRT modulus.

## 1. Input encryption error

The public key and encryption equations are
\[
b=-as+e,\qquad
c_0=bu+e_1+\Delta m,\qquad
c_1=au+e_2 \pmod Q.
\]
The decryption phase is
\[
c_0+c_1s=\Delta m+\epsilon\pmod Q,\qquad
\epsilon=eu+e_1+e_2s.
\]
Using the negacyclic convolution inequality
\[
\|fg\|_\infty\le\|f\|_\infty\|g\|_1,
\]
and \(\|s\|_1,\|u\|_1\le N\), we obtain
\[
\|\epsilon\|_\infty
\le 2N+2+2N=4N+2=32770=:E_0.
\]

## 2. Centered-lift quotient bounds

For each input ciphertext, let \(\hat c_0,\hat c_1\) be the coefficientwise centered integer lifts of its two components, and define
\[
x=\hat c_0+\hat c_1s.
\]
Since every centered ciphertext coefficient has magnitude at most \(Q/2\),
\[
\|x\|_\infty\le\frac{Q(N+1)}2.
\]
There is an integer polynomial \(k\) such that
\[
x=\Delta m+\epsilon+Qk,
\]
where the input plaintext coefficients use representatives in \([0,t-1]\). Hence
\[
\|k\|_\infty
\le\frac{N+1}{2}+\frac{\Delta(t-1)+E_0}{Q}
<4097.5.
\]
Because \(k\) has integer coefficients,
\[
\|k\|_\infty\le K=4097.
\]

Use \(Q=t\Delta+r\) to rewrite the phase exactly as
\[
x=\Delta M+E,\qquad M=m+tk,\quad E=\epsilon+rk.
\]
Therefore
\[
\|M\|_\infty\le(t-1)+tK
=268\,570\,625=:M_0,
\]
\[
\|E\|_\infty\le E_0+rK
=10\,435\,053=:E_1.
\]

## 3. Integer tensor product and scale-and-round

The implementation lifts all four input ciphertext components to centered integers, forms the three integer negacyclic tensor products
\[
U_0=\hat c_0\hat d_0,\quad
U_1=\hat c_0\hat d_1+\hat c_1\hat d_0,\quad
U_2=\hat c_1\hat d_1,
\]
and then applies coefficientwise
\[
W_j=\operatorname{round}(tU_j/Q).
\]
The auxiliary NTT/CRT basis recovers these integer \(U_j\) coefficients exactly; it does not first discard multiples of \(Q\).

For each component write
\[
W_j=(t/Q)U_j+\rho_j,\qquad
\|\rho_j\|_\infty\le\tfrac12.
\]
The unrelinearized phase is thus
\[
W_0+W_1s+W_2s^2
=(t/Q)x_1x_2+\rho_0+\rho_1s+\rho_2s^2.
\]

Let \(M_1M_2=m_{12}+tH\), where \(m_{12}\) is the coefficientwise centered representative of the plaintext product modulo \(t\). Then
\[
\|M_1M_2\|_\infty\le NM_0^2
=590\,890\,439\,580\,800\,000\,000=:P_0,
\]
\[
\|m_{12}\|_\infty\le\lfloor t/2\rfloor=32768,
\]
and consequently
\[
\|H\|_\infty
\le\left\lceil\frac{P_0+32768}{t}\right\rceil
=9\,016\,135\,001\,309\,185=:H_0.
\]

Expanding \(x_i=\Delta M_i+E_i\), the unrounded phase is
\[
\frac{t}{Q}x_1x_2
=\frac{t\Delta^2}{Q}M_1M_2
+\frac{t\Delta}{Q}(M_1E_2+M_2E_1)
+\frac{t}{Q}E_1E_2.
\]
Since \(t\Delta=Q-r\) and \(M_1M_2=m_{12}+tH\), the first term differs from \(\Delta m_{12}\) by
\[
\frac{t\Delta^2}{Q}(m_{12}+tH)-\Delta m_{12}
=\Delta tH-\frac{\Delta r}{Q}M_1M_2
\equiv-rH-\frac{\Delta r}{Q}M_1M_2\pmod Q.
\]
Here \(\Delta tH=(Q-r)H\equiv-rH\pmod Q\). Applying the coefficientwise negacyclic-product bound and \(t\Delta/Q<1\), the absolute error contribution is at most
\[
rH_0+\frac{\Delta r}{Q}P_0
+2NM_0E_1+\frac{t}{Q}NE_1^2.
\]
The three scale-rounding residuals contribute at most
\[
\frac12(1+\|s\|_1+\|s^2\|_1)
\le\frac12(1+N+N^2)=33\,558\,528.5.
\]

## 4. Relinearization error

The evaluation-key relation is
\[
b_j+a_js=B^js^2+e_j\pmod Q.
\]
The centered signed gadget digits obey \(\|d_j\|_\infty\le B-1\), and each \(\eta=2\) key error has
\[
\|e_j\|_1\le2N.
\]
For clarity, let \(\widehat c_2\) be the centered integer lift of the third tensor component. The implementation's signed digit decomposition satisfies the exact coefficientwise integer identity
\[
\widehat c_2=\sum_{j=0}^{L-1}B^j d_j,
\qquad \|d_j\|_\infty\le B-1.
\]
Multiplying each evaluation-key relation by \(d_j\) and summing gives the relinearized phase congruence
\[
W_0+W_1s+\sum_jd_j(b_j+a_js)
\equiv W_0+W_1s+\widehat c_2s^2+\sum_jd_je_j\pmod Q.
\]
This is a congruence in \(R_Q\), not an equality of unreduced integer lifts. It identifies the additional integer error polynomial as \(e_{\rm ks}=\sum_jd_je_j\). Since every key-error coefficient lies in \([-2,2]\), \(\|e_j\|_1\le2N\), and the negacyclic convolution inequality gives
\[
\|e_{\rm ks}\|_\infty
\le\sum_{j=0}^{L-1}\|d_j\|_\infty\|e_j\|_1
\le L(B-1)2N
=15\,032\,156\,160.
\]
The exact integer digit identity is what permits the gadget target terms to recombine to \(\widehat c_2s^2\) modulo \(Q\); the bound applies to the unreduced error polynomial. The final decoding-margin comparison is made with this chosen lift of the error, and its strict bound is far below \(Q/2\), so no ambiguity from choosing a different representative can affect the decoding conclusion.

## 5. Combined bound and decoding margin

The exact-rational audit in \`scripts/audit_rns_bfv_noise.py\` adds the quotient/carry, scale-bias, cross, input-error-product, scale-rounding, and key-switch terms. It obtains
\[
\boxed{\|E_{\rm total}\|_\infty
\le91\,700\,891\,552\,753\,113\,897
<9.18\times10^{19}.}
\]

For a centered output coefficient \(m_{12}\), decryption applies \(\operatorname{round}(t(\Delta m_{12}+E)/Q)\) and then reduces modulo \(t\). Since \(Q=t\Delta+r\),
\[
\frac{t\Delta}{Q}m_{12}
=m_{12}-\frac{r m_{12}}{Q}.
\]
Thus the distance, in phase units, to the nearest rounding boundary is bounded below by
\[
\frac{Q}{2t}-\frac{r|m_{12}|}{t}
\ge\frac{Q}{2t}-\frac{r\lfloor t/2\rfloor}{t}.
\]
The strict decoding margin for the centered plaintext representative is therefore
\[
\frac{Q}{2t}-\frac{r\lfloor t/2\rfloor}{t}
\approx3.2138270414\times10^{60}.
\]
Therefore the deterministic one-multiplication error bound is strictly below the BFV decoding margin by more than 40 decimal orders of magnitude for this specified parameter instance and bounded distributions.

## 6. Internal line-by-line review record (not an external certification)

The derivation was rechecked against the current implementations of `generate_public_key`, `encrypt_rns_bfv`, `bfv_tensor_multiply`, `bfv_scale_and_round`, `gadget_decompose_centered`, and `bfv_relinearize`. The following consistency checks hold for the stated parameter instance:

1. **Encryption phase.** The code uses (b=-as+e), (c_0=bu+e_1+\Delta m), and (c_1=au+e_2), so the terms involving (a u s) cancel and the phase error is exactly (eu+e_1+e_2s). The implemented ternary samplers give \\(\|u\|_1,\|s\|_1\\le N\\), and the eta=2 sampler has coefficient support [-2,2], validating (E_0=4N+2).
2. **Centered-lift quotient.** The centered component interval and the convolution inequality give the displayed bound on (k). Exact arithmetic gives (K_{\rm real}=4097.499984741444\ldots<4097.5), hence the integer bound (K=4097) is valid (and is close enough to the boundary that this strict inequality should remain explicit).
3. **Tensor products and CRT.** The code reconstructs each of the four input component polynomials as centered integer lifts. It computes the two cross convolutions separately, adds them as `BigInt`, and applies coefficientwise (t/Q) rounding to each of the three tensor components. The auxiliary CRT bound is therefore needed for each individual convolution, not for their subsequent exact sum.
4. **Scale-rounding residual.** The implementation rounds ties away from zero. In all cases the residual in (W_j=(t/Q)U_j+\rho_j) lies in [-1/2,1/2], so the bound (\tfrac12(1+N+N^2)) follows from (\|s\|_1\le N) and (\|s^2\|_1\le\|s\|_1^2\le N^2).
5. **Gadget decomposition.** The code decomposes the absolute value of each centered coefficient into ordinary base-(B) digits and applies the original sign to every digit. Thus the digit identity is exact over the integers and each digit has coefficient magnitude at most (B-1). Combined with \\(\|e_j\|_1\le2N\\), this validates the stated deterministic key-switch contribution.
6. **Decoding threshold.** The decoder computes coefficientwise `round(t*phase/Q)` and reduces modulo (t). For a centered plaintext coefficient (m_{12}), the exact distance-to-boundary condition is \\( |E| < Q/(2t)-r|m_{12}|/t \\), matching the margin used in the audit.

Re-evaluating the exact-rational expressions gives a total upper bound of (9.17008915527531\times10^{19}), a minimum decoding margin of (3.21382704144681\times10^{60}), and a ratio of approximately (2.8533\times10^{-41}). The arithmetic audit therefore has a very large deterministic margin for this one-operation model.

**Review disposition:** no algebraic or parameter-substitution discrepancy was found in this internal source-to-proof pass. This is not an independent mathematical review: the proof still relies on the correctness of the implemented ring/NTT multiplication, CRT basis constants, sampler behavior, and the stated centered-lift semantics. The existing unit tests and parameter audit provide implementation checks but do not replace a separately authored proof or an external reviewer. In particular, this bound does not address security of the structured evaluation-key transcript.

## 7. Assumptions and limits

- The bound applies to the current \(\eta=2\) bounded error samplers and ternary secret/ephemeral samplers.
- It assumes the generated evaluation-key digits satisfy the documented phase relation; the implementation tests that relation coefficientwise.
- It proves one multiplication followed by one relinearization, not arbitrary multiplicative depth.
- It is a correctness statement only. It does not establish RLWE hardness, a security level, resistance to side channels, constant-time behavior, or suitability for production.
- The exact auxiliary-NTT integer product and BigInt CRT/rounding path is a correctness reference, not an optimized implementation.

The executable rational audit is part of CI and fails if the strict decoding inequality or exact auxiliary CRT range condition does not hold.
