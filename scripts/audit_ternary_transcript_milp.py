#!/usr/bin/env python3
"""Exact MILP encoding of tiny shared-secret BFV evaluation-key transcripts.

SciPy/HiGHS is used only as a finite-domain solver for tiny rings. Every
ternary coefficient is represented by two binary indicators; products are
linearized exactly. The optional mod-2 square constraints are redundant.
The complete solver survivor set is compared with independent exhaustive
enumeration. This is a toy correctness experiment, not a scalable attack.
"""
from itertools import product
from random import Random

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix, vstack

SIGNS = (1, -1)


def negacyclic_mul(a, b, q):
    n = len(a)
    out = [0] * n
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            k = i + j
            out[k if k < n else k - n] += x * y * (1 if k < n else -1)
    return [x % q for x in out]


def centered(x, q):
    x %= q
    return x - q if x > q // 2 else x


def make_transcript(n, q, base, levels, seed):
    rng = Random(seed)
    secret = [rng.choice((-1, 0, 1)) for _ in range(n)]
    square = negacyclic_mul(secret, secret, q)
    masks, bodies = [], []
    for level in range(levels + 1):
        a = [rng.randrange(q) for _ in range(n)]
        e = [sum(rng.randrange(2) for _ in range(4)) - 2 for _ in range(n)]
        target = [0] * n if level == 0 else [
            pow(base, level - 1, q) * x % q for x in square
        ]
        a_secret = negacyclic_mul(a, secret, q)
        b = [(target[k] - a_secret[k] + e[k]) % q for k in range(n)]
        masks.append(a)
        bodies.append(b)
    return secret, masks, bodies


def exhaustive_survivors(n, q, base, levels, masks, bodies):
    survivors = set()
    for candidate in product((-1, 0, 1), repeat=n):
        square = negacyclic_mul(candidate, candidate, q)
        valid = True
        for level in range(levels + 1):
            a_secret = negacyclic_mul(masks[level], candidate, q)
            target = [0] * n if level == 0 else [
                pow(base, level - 1, q) * x % q for x in square
            ]
            for k in range(n):
                err = centered(bodies[level][k] + a_secret[k] - target[k], q)
                if abs(err) > 2:
                    valid = False
                    break
            if not valid:
                break
        if valid:
            survivors.add(tuple(candidate))
    return survivors


class LinearModel:
    def __init__(self):
        self.names, self.lower, self.upper, self.integrality = [], [], [], []
        self.rows = []

    def var(self, name, lo, hi):
        idx = len(self.names)
        self.names.append(name)
        self.lower.append(lo)
        self.upper.append(hi)
        self.integrality.append(1)
        return idx

    def constraint(self, coefficients, lo, hi):
        self.rows.append((coefficients, lo, hi))

    def matrix(self):
        mat = lil_matrix((len(self.rows), len(self.names)), dtype=float)
        lows, highs = [], []
        for r, (coeffs, lo, hi) in enumerate(self.rows):
            for c, value in coeffs.items():
                if value:
                    mat[r, c] = value
            lows.append(lo)
            highs.append(hi)
        return mat.tocsr(), np.asarray(lows), np.asarray(highs)


def square_coefficient(model, n, k, products):
    coeff = {}
    for i in range(n):
        for j in range(n):
            raw = i + j
            folded = raw if raw < n else raw - n
            if folded != k:
                continue
            sign = 1 if raw < n else -1
            for si, sj, multiplier in (
                (1, 1, 1), (-1, -1, 1), (1, -1, -1), (-1, 1, -1)
            ):
                p = products[(i, j, si, sj)]
                coeff[p] = coeff.get(p, 0) + sign * multiplier
    return coeff


def milp_survivors(n, q, base, levels, masks, bodies, parity_constraints):
    if parity_constraints and n % 2:
        raise ValueError("the paired parity identity is defined here only for even N")
    model = LinearModel()
    up, um, products = {}, {}, {}
    for i in range(n):
        up[i] = model.var(("u+", i), 0, 1)
        um[i] = model.var(("u-", i), 0, 1)
        model.constraint({up[i]: 1, um[i]: 1}, -np.inf, 1)

    for i in range(n):
        for j in range(n):
            for si in SIGNS:
                for sj in SIGNS:
                    p = model.var(("p", i, j, si, sj), 0, 1)
                    products[(i, j, si, sj)] = p
                    ui = up[i] if si == 1 else um[i]
                    uj = up[j] if sj == 1 else um[j]
                    model.constraint({p: 1, ui: -1}, -np.inf, 0)
                    model.constraint({p: 1, uj: -1}, -np.inf, 0)
                    # When i == j and si == sj, ui and uj are the
                    # same binary variable. A dict literal would silently
                    # overwrite one -1 coefficient; accumulate it as -2.
                    lower_product = {p: 1}
                    lower_product[ui] = lower_product.get(ui, 0) - 1
                    lower_product[uj] = lower_product.get(uj, 0) - 1
                    model.constraint(lower_product, -1, np.inf)

    if parity_constraints:
        for k in range(n):
            h = model.var(("parity_quotient", k), -2 * n, 2 * n)
            coeff = square_coefficient(model, n, k, products)
            coeff[h] = -2
            if k % 2 == 0:
                r = k // 2
                coeff[up[r]] = coeff.get(up[r], 0) - 1
                coeff[um[r]] = coeff.get(um[r], 0) - 1
                other = r + n // 2
                coeff[up[other]] = coeff.get(up[other], 0) - 1
                coeff[um[other]] = coeff.get(um[other], 0) - 1
            model.constraint(coeff, 0, 0)

    # One shared ternary secret and its one shared square appear at every level.
    for level in range(levels + 1):
        for k in range(n):
            row = {}
            for j in range(n):
                for i in range(n):
                    raw = i + j
                    folded = raw if raw < n else raw - n
                    if folded == k:
                        sign = 1 if raw < n else -1
                        row[up[j]] = row.get(up[j], 0) + sign * masks[level][i]
                        row[um[j]] = row.get(um[j], 0) - sign * masks[level][i]
            if level:
                factor = pow(base, level - 1, q)
                sq = square_coefficient(model, n, k, products)
                for var, value in sq.items():
                    row[var] = row.get(var, 0) - factor * value
            e = model.var(("e", level, k), -2, 2)
            quotient = model.var(("t", level, k), -(2 * n + 5), 2 * n + 5)
            row[e] = row.get(e, 0) - 1
            row[quotient] = row.get(quotient, 0) - q
            model.constraint(row, -bodies[level][k], -bodies[level][k])

    matrix, lows, highs = model.matrix()
    base_constraint = LinearConstraint(matrix, lows, highs)
    bounds = Bounds(model.lower, model.upper)
    integrality = np.asarray(model.integrality)
    survivors = set()
    max_solutions = 3 ** n + 1
    for _ in range(max_solutions):
        result = milp(
            c=np.zeros(len(model.names)),
            integrality=integrality,
            bounds=bounds,
            constraints=base_constraint,
            options={"time_limit": 30},
        )
        if result.status == 2:  # proven infeasible: enumeration is complete
            return survivors
        if not result.success:
            raise RuntimeError(
                f"HiGHS did not prove optimality/completion: "
                f"status={result.status}, message={result.message}"
            )
        # Independently audit the raw HiGHS solution before rounding or
        # adding a no-good cut. This catches numerical/integrality issues
        # and any mismatch between the MILP encoding and ring arithmetic.
        raw = result.x
        max_integrality_error = float(np.max(np.abs(raw - np.round(raw))))
        lhs = matrix @ raw
        row_violation = max(
            float(np.max(np.maximum(lows - lhs, 0))),
            float(np.max(np.maximum(lhs - highs, 0))),
        )
        if max_integrality_error > 1e-7 or row_violation > 1e-7:
            raise RuntimeError(
                "HiGHS raw solution failed independent feasibility audit: "
                f"integrality_error={max_integrality_error}, "
                f"row_violation={row_violation}"
            )

        candidate = tuple(
            int(round(raw[up[i]])) - int(round(raw[um[i]]))
            for i in range(n)
        )
        # Verify every bilinear auxiliary variable against its defining
        # binary product, then check every transcript equation directly.
        product_mismatches = []
        for (i, j, si, sj), pidx in products.items():
            ui = up[i] if si == 1 else um[i]
            uj = up[j] if sj == 1 else um[j]
            expected = int(round(raw[ui])) * int(round(raw[uj]))
            actual = int(round(raw[pidx]))
            if actual != expected:
                product_mismatches.append(((i, j, si, sj), actual, expected))
        name_to_idx = {name: idx for idx, name in enumerate(model.names)}
        equation_mismatches = []
        for level in range(levels + 1):
            for k in range(n):
                a_secret = negacyclic_mul(masks[level], candidate, q)
                square = negacyclic_mul(candidate, candidate, q)
                target = [0] * n if level == 0 else [
                    pow(base, level - 1, q) * x % q for x in square
                ]
                direct_error = centered(
                    bodies[level][k] + a_secret[k] - target[k], q
                )
                model_error = int(round(raw[name_to_idx[("e", level, k)]]))
                model_quotient = int(round(raw[name_to_idx[("t", level, k)]]))
                if direct_error != model_error:
                    equation_mismatches.append(
                        (level, k, direct_error, model_error, model_quotient)
                    )
        if product_mismatches or equation_mismatches:
            print("DEBUG raw_integrality_error=", max_integrality_error)
            print("DEBUG raw_row_violation=", row_violation)
            print("DEBUG product_mismatches=", product_mismatches[:20])
            print("DEBUG equation_mismatches=", equation_mismatches[:20])
            raise AssertionError("raw MILP solution disagrees with direct ring audit")
        if candidate in survivors:
            raise AssertionError("MILP returned a duplicate secret")
        survivors.add(candidate)

        # No-good cut: at least one coefficient must differ from this
        # ternary assignment. For a nonzero value, a mismatch is 1-u;
        # for zero, a mismatch is u+ + u-.
        block = {}
        nonzero = 0
        for i, value in enumerate(candidate):
            if value == 1:
                nonzero += 1
                block[up[i]] = -1
            elif value == -1:
                nonzero += 1
                block[um[i]] = -1
            else:
                block[up[i]] = 1
                block[um[i]] = 1
        cut = lil_matrix((1, len(model.names)), dtype=float)
        for col, value in block.items():
            cut[0, col] = value
        matrix = vstack([matrix, cut.tocsr()], format="csr")
        lows = np.append(lows, 1 - nonzero)
        highs = np.append(highs, np.inf)
        base_constraint = LinearConstraint(matrix, lows, highs)
    raise RuntimeError("solution enumeration exceeded the full ternary space")


def run_case(n, seed, q=257, base=4, levels=2):
    planted, masks, bodies = make_transcript(n, q, base, levels, seed)
    exhaustive = exhaustive_survivors(n, q, base, levels, masks, bodies)
    without_parity = milp_survivors(
        n, q, base, levels, masks, bodies, parity_constraints=False
    )
    with_parity = milp_survivors(
        n, q, base, levels, masks, bodies, parity_constraints=True
    )
    assert tuple(planted) in exhaustive
    if without_parity != exhaustive:
        print(f"DEBUG N={n}, q={q}, seed={seed}: exhaustive={len(exhaustive)}, MILP={len(without_parity)}")
        print("DEBUG missing_from_MILP=", sorted(exhaustive - without_parity))
        extras = sorted(without_parity - exhaustive)
        print("DEBUG extra_from_MILP=", extras)
        for candidate in extras:
            sq = negacyclic_mul(candidate, candidate, q)
            residuals = []
            for lev in range(levels + 1):
                aa = negacyclic_mul(masks[lev], candidate, q)
                target = [0] * n if lev == 0 else [
                    pow(base, lev - 1, q) * x % q for x in sq
                ]
                residuals.append([
                    centered(bodies[lev][k] + aa[k] - target[k], q)
                    for k in range(n)
                ])
            print("DEBUG candidate_residuals=", candidate, residuals)
        raise AssertionError((n, seed, "MILP/exhaustive mismatch"))
    if with_parity != exhaustive:
        print(f"DEBUG parity N={n}, q={q}, seed={seed}: exhaustive={len(exhaustive)}, MILP={len(with_parity)}")
        print("DEBUG parity_missing=", sorted(exhaustive - with_parity))
        print("DEBUG parity_extra=", sorted(with_parity - exhaustive))
        raise AssertionError((n, seed, "parity model changed survivors"))
    print(
        f"N={n}; q={q}; B={base}; levels={levels}; seed={seed}; "
        f"exhaustive={len(exhaustive)}; "
        f"MILP_no_parity={len(without_parity)}; "
        f"MILP_with_parity={len(with_parity)}; exact_sets_equal=PASS"
    )


def main():
    print("Exact ternary-transcript MILP vs exhaustive oracle; q=257, B=4, levels=2")
    print("All errors have exact CBD_eta2 support [-2,2]; probabilities are not used for feasibility.")
    for n in (2, 4):
        for seed in range(4):
            run_case(n, seed)
    print("Ambiguity-stress cases: smaller odd q, non-unique survivor sets expected")
    run_case(2, seed=0, q=7, base=4, levels=0)
    run_case(4, seed=0, q=7, base=4, levels=1)
    print("All toy MILP/exhaustive and redundant-parity checks: PASS")
    print("Toy feasibility only; no production attack or security estimate.")


if __name__ == "__main__":
    main()
