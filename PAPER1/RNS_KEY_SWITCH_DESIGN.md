# RNS-BFV relinearization: key-generation contract

## Purpose and scope

This document specifies the next cryptographic construction required to turn the existing N=8192, four-lane RNS arithmetic prototype into an experimental BFV key-switching implementation. It is a design contract, not evidence that secure evaluation-key generation has been implemented.

The current `RnsEvalKeyDigit` is only a pair of RNS polynomials. The current phase-preservation test uses a synthetic error-free key and does not validate this construction.

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
