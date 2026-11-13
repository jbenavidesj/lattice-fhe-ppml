# Split-secret square identity audit

## Purpose

This audit independently checks the quadratic term coupling the two halves in a split-secret meet-in-the-middle (MITM) decomposition. It is an algebraic differential test, not an attack, security estimate, or performance benchmark.

## Identity

In (R_q=\mathbb Z_q[X]/(X^N+1)), for even (N=2m), write
[
s=u+X^m v.
]
Then
[
s^2=u^2+2X^muv+X^{2m}v^2
=u^2+2X^muv-v^2
pmod{X^N+1}.
]

The implementation computes (u^2), (uv), and (v^2), shifts the cross product by (X^m) with negacyclic wraparound, and compares the result against direct multiplication of (s).

## Test coverage

The deterministic script checks moduli (q=11) and (q=65537), even degrees (N=4,6,8,10,12,16), ternary and unrestricted ring elements, and four evaluation-key gadget factors per case. It performs 6,000 square-identity checks and 24,000 residual comparisons.

## Interpretation

A passing audit verifies the split expansion on the tested cases. It does not make the evaluation-key equation separable: the mixed product (uv) still depends on both halves. This is a correctness prerequisite for a future cross-term-aware join, not evidence of a faster join or a cryptographic attack.

## Reproduction

```bash
python scripts/audit_split_secret_square.py
```
