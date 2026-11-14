# Evaluation-key constraints in a split-secret MITM join

## Scope

This note analyzes whether the evaluation-key equations can be used as independent filters in the existing toy meet-in-the-middle (MITM) implementation. It is a correctness analysis, not an attack or security claim.

## Split and expansion

Work in (R_Q=\mathbb Z_Q[X]/(X^N+1)), with even (N), and split a ternary candidate as

[
s=u+X^{N/2}v,
]

where (u) and (v) are supported on the first (N/2) coefficients. The public-key phase equation is linear in (s), so for a fixed public polynomial (a),

[
as=au+aX^{N/2}v.
]

This is the separability used by the existing two-list join.

The evaluation-key phase equation contains (s^2). Its expansion is

[
s^2=u^2+2X^{N/2}uv+X^Nv^2
=u^2+2X^{N/2}uv-v^2
pmod{X^N+1}.
]

The mixed term (2X^{N/2}uv) depends on both halves. Thus the evaluation-key residual

[
b_j+a_js-B^js^2
]

cannot be represented as a sum of a left-only contribution and a right-only contribution without explicitly accounting for the cross term.

## Consequence for the current prototype

The current implementation uses the public-key linear residual to retrieve candidate pairs. It then verifies the full public-key residual and every evaluation-key residual. This is sound as a candidate filter: it may retrieve extra pairs, but the full equations reject false positives. The equality check against exhaustive enumeration is the relevant correctness test for the toy instances.

It would be incorrect to independently hash a left-half and right-half evaluation-key contribution while omitting the mixed term. Such an implementation could discard the planted secret or report an incomplete candidate set.

## Safe next experiments

1. Derive a split representation of the mixed product (uv) and measure the cost of carrying its contribution into the join.
2. Explore partial evaluation-key checks only after public-key pairs have been joined; measure whether this reduces later verification cost (not list size).
3. Compare all candidate sets against exhaustive enumeration for every tested toy instance.
4. Report memory, bucket-size distributions, false-pair counts, and wall-clock measurements separately.

## Limitations

The existing toy parameters and experiments do not establish an attack on the production parameters. The list size remains (3^{N/2}), and no production-scale complexity improvement or cryptographic weakness is claimed.
