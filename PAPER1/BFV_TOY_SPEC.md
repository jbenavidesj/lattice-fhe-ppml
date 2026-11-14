# Tiny-ring BFV model: mathematical contract and correctness proof

## Scope

This is a deterministic, tiny-ring correctness model for one leveled BFV multiplication followed by gadget relinearization. It is separate from the four-lane, N=8192 RNS arithmetic prototype. It is not production cryptography, does not establish RLWE security, and must never protect real data.

## Parameters and rings

The toy ring is
`R_q = (Z/qZ)[X]/(X^N+1)`,
with `N=8`, `q=1099511627873`, and plaintext modulus `t=17`. The modulus satisfies `q ≡ 1 (mod 2N)`. Set
`Delta = floor(q/t) = 64677154580`
and
`r = q - t*Delta = 13`,
so `q=t*Delta+r`.

The plaintext ring is `R_t = (Z/tZ)[X]/(X^N+1)`. Ciphertext coefficients are stored canonically modulo q; the multiplication routine chooses the centered integer representative in `(-q/2,q/2)` for each input ciphertext component before forming integer tensor products.

## Demonstration distributions and encryption

The secret `s`, ephemeral `u`, and errors `e,e1,e2` have coefficients in `{-1,0,1}`, encoded modulo q. All sampling is deterministic and test-only.

The public key is `(b,a)`, with `b=-(a*s+e) mod q`. Encryption returns
- `c0 = b*u + e1 + Delta*m (mod q)`
- `c1 = a*u + e2 (mod q)`.

For the integer phase of the centered input lifts, write
`x = c0_hat + c1_hat*s`.
Modulo q,
`x = Delta*m + epsilon (mod q)`, where
`epsilon = e1 + e2*s - e*u`.
Because the secret and all error polynomials are ternary and negacyclic convolution obeys
`||a*b||_infinity <= ||a||_infinity ||b||_1`,
we have
`||epsilon||_infinity <= 1 + N + N = 17`.

## Decryption

Decryption computes the centered representative of `c0+c1*s mod q`, multiplies each coefficient by `t/q`, rounds to nearest integer (ties away from zero), and reduces modulo t. This is the convention implemented by the toy module.

## Multiplication: essential lift convention

For each input ciphertext component, take its centered integer coefficient lift. Form the three tensor components over the integer negacyclic ring `Z[X]/(X^N+1)`:
- `U0 = c0_hat*d0_hat`
- `U1 = c0_hat*d1_hat + c1_hat*d0_hat`
- `U2 = c1_hat*d1_hat`.

Then compute `Wk = round(t*Uk/q) mod q`, coefficientwise, with ties away from zero. The quotient information in the integer tensor products MUST be retained until after scale-and-round. Reducing `Uk` modulo q before scaling is a different operation and is not the multiplication implemented here.

Write each rounding residual as
`rho_k = Wk - (t/q)*Uk`,
so `||rho_k||_infinity <= 1/2`. The unrelinearized phase is therefore
`W0 + W1*s + W2*s^2 = (t/q)*x1*x2 + rho0 + rho1*s + rho2*s^2`
as an integer-lift identity, modulo the ciphertext modulus.

## Full one-multiplication noise bound

The following is a deterministic worst-case bound for the exact toy distributions and lift convention above; it is not a probabilistic estimate.

For each input ciphertext, its centered components satisfy
`||c0_hat||_infinity, ||c1_hat||_infinity <= q/2`.
Since `||s||_1 <= N`,
`||x||_infinity <= q(1+N)/2`.
There is an integer polynomial k such that
`x = Delta*m + epsilon + q*k`.
Using `q=t*Delta+r`, rewrite this exactly as
`x = Delta*m_tilde + epsilon_tilde`,
where
`m_tilde = m + t*k` and `epsilon_tilde = epsilon + r*k`.

The preceding bounds imply
`||k||_infinity <= 5`,
`||m_tilde||_infinity <= 16 + 17*5 = 101`,
and
`||epsilon_tilde||_infinity <= 17 + 13*5 = 82`.

Let `m12` be the centered coefficient representative of the plaintext product `m_tilde1*m_tilde2 mod t), so `||m12||_infinity <= 8`. Define the integer polynomial H by
`m_tilde1*m_tilde2 = m12 + t*H`.
Then
`||m_tilde1*m_tilde2||_infinity <= N*101^2 = 81608`
and
`||H||_infinity <= ceil((81608+8)/17) = 4801).

Expanding the scaled product and using `t*Delta=q-r` gives
`(t*Delta^2/q)*(m12+t*H) - Delta*m12
 = q*H - r*H - (Delta*r/q)*(m12+t*H)`.
The `q*H` term vanishes modulo q. The remaining deterministic multiplication-error terms are bounded by:
- plaintext quotient term: `r*||H||_infinity <= 62413`;
- scale bias: `(Delta*r/q)*81608`;
- cross terms: `(2*t*Delta/q)*N*101*82`;
- product of input errors: `(t/q)*N*82^2`.

The three scale-and-round residuals contribute at most
`(1/2)*(1+||s||_1+||s^2||_1) <= (1/2)*(1+N+N^2) = 36.5`.

## Relinearization and key-switch error

For base `B=2`, the gadget has `L=ceil(log_B(q))=41` levels. Each evaluation-key error coefficient has absolute value at most 1, and each unsigned digit coefficient is at most `B-1`. Thus
`||e_ks||_infinity <= L*N*(B-1) = 328`.

Adding the quotient, scale-bias, cross, product-error, rounding, and key-switch terms gives the exact-rational bound
`||E_total||_infinity <= 257695.6176455859...`.

The decryption condition for phase `Delta*m12 + E_total` is
`||E_total||_infinity < q/(2t) - (r/t)*||m12||_infinity`.
For `||m12||_infinity <= 8`, the right-hand side is
`32338577284.2647...`.
Therefore the deterministic one-multiplication bound is strictly below the decoding margin for these toy parameters.

This proof covers one multiplication and one relinearization only. It does not prove arbitrary multiplicative depth, security, constant-time execution, or correctness for the N=8192 RNS candidates.

## Executable validation

- Rust tests compare multiplication decryption with plaintext negacyclic multiplication for a fixed vector and 64 deterministic seeds.
- Relinearization tests compare two-component and three-component decryption for gadget bases 2, 4, and 16 over 16 deterministic seeds per base.
- `scripts/audit_toy_bfv_noise.py` recomputes the conservative bound using exact rational arithmetic and fails if it does not fit inside the decoding margin.
- CI runs this audit alongside the existing arithmetic tests.

## Explicit limitations

The toy sampler is deterministic and non-cryptographic. No RLWE estimator, secure randomness, Gaussian sampler, production relinearization design, constant-time audit, or N=8192 RNS BFV integration is claimed. The bound is a correctness proof for this finite toy model, not a security argument or an IEEE-ready validation of the full scheme.
