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

Expanding \(x_i=\Delta M_i+E_i\), and using \(Q=t\Delta+r\), the difference between the main scaled plaintext term and \(\Delta m_{12}\), modulo \(Q\), is bounded by
\[
rH_0+\frac{\Delta r}{Q}P_0
+2NM_0E_1+\frac{t}{Q}NE_1^2.
\]
The three scale-rounding residuals contribute at most
\\[
\\tfrac12(1+\\|s\\|_1+\\|s^2\\|_1)
\\le\\tfrac12(1+N+N^2)=33\\,558\\,528.5.
\\]

## 4. Relinearization error

The evaluation-key relation is
\[
b_j+a_js=B^js^2+e_j\pmod Q.
\]
The centered signed gadget digits obey \(\|d_j\|_\infty\le B-1\), and each \(\eta=2\) key error has
\[
\|e_j\|_1\le2N.
\]
Thus
\[
\|e_{\rm ks}\|_\infty
\le L(B-1)2N
=15\,032\,156\,160.
\]

## 5. Combined bound and decoding margin

The exact-rational audit in \`scripts/audit_rns_bfv_noise.py\` adds the quotient/carry, scale-bias, cross, input-error-product, scale-rounding, and key-switch terms. It obtains
\[
\boxed{\|E_{\rm total}\|_\infty
\le91\,700\,891\,552\,753\,113\,897
<9.18\times10^{19}.}
\]

The strict decoding margin for the centered plaintext representative is
\[
\frac{Q}{2t}-\frac{r\lfloor t/2\rfloor}{t}
\approx3.2138270414\times10^{60}.
\]
Therefore the deterministic one-multiplication error bound is strictly below the BFV decoding margin by more than 40 decimal orders of magnitude for this specified parameter instance and bounded distributions.

## 6. Assumptions and limits

- The bound applies to the current \(\eta=2\) bounded error samplers and ternary secret/ephemeral samplers.
- It assumes the generated evaluation-key digits satisfy the documented phase relation; the implementation tests that relation coefficientwise.
- It proves one multiplication followed by one relinearization, not arbitrary multiplicative depth.
- It is a correctness statement only. It does not establish RLWE hardness, a security level, resistance to side channels, constant-time behavior, or suitability for production.
- The exact auxiliary-NTT integer product and BigInt CRT/rounding path is a correctness reference, not an optimized implementation.

The executable rational audit is part of CI and fails if the strict decoding inequality or exact auxiliary CRT range condition does not hold.
