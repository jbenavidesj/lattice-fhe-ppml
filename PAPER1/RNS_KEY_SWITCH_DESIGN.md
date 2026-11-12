# RNS-BFV relinearization: key-generation contract

## Purpose and scope

This document specifies the next cryptographic construction required to turn the existing N=8192, four-lane RNS arithmetic prototype into an experimental BFV key-switching implementation. It is a design contract, not evidence that secure evaluation-key generation has been implemented.

The current `RnsEvalKeyDigit` is only a pair of RNS polynomials; it does not generate keys. The test suite now includes a deterministic sparse fixture with nonzero errors and a nontrivial secret. This validates the algebraic phase identity for that fixture, not secure sampling or production key generation.

## Ring and basis

Let
[
R_Q = (\mathbb Z/Q\mathbb Z)[X]/(X^N+1),\qquad
Q=\prod_{i=0}^{3}q_i,\qquad N=8192.
]
The four RNS lanes represent the same element of (R_Q). All key equations below are equations in (R_Q), not four unrelated equations with independently sampled secrets.

Let (s\in R_Q) be the secret polynomial and let (B\ge2) be the gadget base. For each digit index (j\in\{0,\ldots,L-1\}), define (g_j=B^j\bmod Q), where (L) is chosen so that (B^L\ge Q).

## Evaluation-key relation and sign convention

For each digit, sample:
- (a_j\leftarrow R_Q) uniformly (using a cryptographically secure, unbiased sampler);
- a small error polynomial (e_j\leftarrow\chi^N), using a fully specified error distribution and sampler.

Set
[
b_j=g_js^2-a_js+e_j\pmod Q.
]
Then the required relation is
[
\boxed{b_j+a_js=g_js^2+e_j\pmod Q.}
]

The plus sign in the relation is deliberate and must match the implementation's accumulation convention:
[
c'_0=c_0+\sum_j d_jb_j,\qquad
c'_1=c_1+\sum_j d_ja_j.
]
If the signed convention changes, both key generation and accumulation must change together.

## Gadget decomposition contract

For every centered coefficient (x\in(-Q/2,Q/2]), compute signed digits (d_j\in\mathbb Z) such that
[
x=\sum_{j=0}^{L-1}d_jB^j
]
as an exact integer identity, not merely as four independent residue decompositions. The current reference decomposition uses the sign of (x) and base-(B) digits of (|x|), so (|d_j|\le B-1). The same integer digit polynomial must be encoded into every RNS lane.

The current implementation reconstructs centered coefficients with exact CRT and is therefore a correctness oracle, not a fast decomposition algorithm.

## Key-switch phase identity

Write (c_2=\sum_jd_jB^j\pmod Q). With the relation above,
[
\begin{aligned}
c'_0+c'_1s
&=c_0+c_1s+\sum_jd_j(b_j+a_js)\\
&=c_0+c_1s+c_2s^2+\sum_jd_je_j\pmod Q.
\end{aligned}
]
Thus the additional key-switch error is
[
e_{\rm ks}=\sum_jd_je_j.
]

For negacyclic multiplication, \\(\|uv\|_\infty\le\|u\|_\infty\|v\|_1\\). If every digit has coefficient bound (D\) and every error polynomial satisfies (\|e_j\|_1\le E_1), then
[
\boxed{\|e_{\rm ks}\|_\infty\le LDE_1.}
]
For the current unsigned-magnitude digit convention, (D=B-1). This is a deterministic bound conditional on the stated error norm; a Gaussian sampler requires either a hard truncation bound or a probabilistic tail bound with an explicit failure probability.

## RNS implementation requirements

A correct implementation must ensure:
1. The same secret (s), error (e_j), and uniform (a_j) are represented consistently across all four lanes.
2. Sampling is unbiased modulo each (q_i); do not independently sample four unrelated (a_{j,i}) and then treat them as one uniform element unless the construction explicitly proves equivalence.
3. The target (g_js^2) is computed in the common ring and reduced into each lane.
4. The key relation is checked by an independent test oracle after CRT reconstruction on small instances.
5. The accumulated phase is checked for nonzero errors and nontrivial secrets, with independent polynomial arithmetic.
6. The implementation distinguishes a deterministic test RNG from an operating-system-backed cryptographic RNG.
7. No constant-time, side-channel, or RLWE-security claim is made without separate audits.

## Why the current code is not yet a secure key generator

The repository currently stores evaluation-key pairs and applies gadget accumulation. Its tests use synthetic algebraic keys (including an error-free construction) to verify phase algebra. There is no production key-generation routine, no cryptographically secure sampler, no specified \\(\chi\\) distribution, and no security estimate. Therefore the current RNS relinearization code must remain labelled as an arithmetic/reference operation.

## Acceptance tests for the next implementation

- Small-ring deterministic test: independently sample (s,a_j,e_j), construct (b_j), and verify each key equation.
- RNS consistency test: reconstruct each lane's key equation and compare against a single BigInt reference equation.
- Nonzero-error phase test: verify the exact phase difference equals \\(\sum_jd_je_j\\) modulo (Q).
- Bound test: check observed coefficient infinity norm is at most the deterministic bound for bounded errors.
- Negative tests: reject wrong digit count, mismatched dimensions, noncanonical lane values, and incorrect gadget base.
- Security separation: test RNG is explicitly named and documented as deterministic; production API must require a CSPRNG source.

Passing these tests would validate the implementation contract, not prove RLWE security or constant-time behavior.


## Implemented deterministic test fixture (not production key generation)

The RNS test suite now contains a deterministic sparse fixture that builds evaluation-key digits with nonzero signed error polynomials and a nontrivial sparse secret. It constructs each digit using
```
b_j = B^j*s^2 - a_j*s + e_j  (mod Q)
```
and checks, after the actual RNS relinearization routine, that the output phase differs from the input three-component phase by exactly
```
sum_j d_j*e_j  (mod Q).
```

The fixture's `a_j` and `e_j` values are fixed sparse patterns, not samples from a cryptographic distribution. This test therefore checks the algebraic key-switch identity and its implementation path only. It does not establish uniformity, RLWE security, error-distribution suitability, or production key-generation readiness. A companion assertion checks the observed centered coefficient infinity norm against the conditional bound `L(B-1) max_j ||e_j||_1`; the bound is valid only when the stated per-error l1 bound holds.


## Illustrative deterministic envelope for the current RNS candidates

This is a parameterized *error-contribution calculation*, not a choice of a production error distribution.

For the four candidate moduli, the aggregate modulus is exactly
`Q = 421249165630599354127590185589164472945208468246547404789529362433`
with 218 bits. With `t=65537`, `B=2^16`, and `L=14` (the smallest integer for which `B^L >= Q`), suppose only for the purpose of a deterministic envelope that every coefficient of every evaluation-key error satisfies `|e_{j,k}| <= 1`. Then `||e_j||_1 <= N = 8192), and

```
||e_ks||_infinity <= L * (B - 1) * N
                    = 7,516,078,080.
```

The isolated half-plaintext-spacing threshold is `floor(Q/(2t)) =
3213827041446811374701238884822043066856954607676178378545931`.
The ratio of that threshold to the above key-switch contribution bound is approximately `4.28e50` (about 168.2 bits).

**Interpretation limit:** this comparison only shows that this hypothetical bounded key-switch error term is small relative to the isolated BFV rounding threshold. It does not establish the complete decryption condition after BFV multiplication: input noise, multiplication cross terms, scale-rounding residuals, plaintext carries/lifts, and all other error terms must be included in one rigorous bound. Nor does the coefficient-support assumption specify a sampler or establish RLWE security. The current deterministic sparse test uses a smaller fixture-specific `E_1 <= 3`; the `E_1 <= 8192` calculation is a conservative envelope for a future coefficientwise ternary error, not evidence that such an error sampler is implemented.
