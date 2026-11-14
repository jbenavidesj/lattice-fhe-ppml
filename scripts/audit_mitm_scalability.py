#!/usr/bin/env python3
"""Transparent asymptotic/resource projection for the toy ternary MITM join.

This script performs no production-size search. It reports exact enumeration
counts and heuristic expected-join projections under independent uniform
residues. The latter are not attack estimates or security bounds.
"""
import math

ETA = 2
WIDTH = 2 * ETA + 1
Q_TOY = 11
Q_PAPER1 = 421249165630599354127590185589164472945208468246547404789529362433
DIMENSIONS = (8, 16, 32, 64, 128, 256, 512, 1024, 8192)


def projection(n, q, eta=ETA):
    width = 2 * eta + 1
    if q <= width:
        raise ValueError("Need q > 2*eta+1 for this heuristic ratio.")
    log2_three = math.log2(3)
    log2_width = math.log2(width)
    log2_q_over_width = math.log2(q / width)

    # Each half has 3^(N/2) assignments. Both halves are materialized.
    log2_half_entries = (n / 2) * log2_three
    log2_total_secret_space = n * log2_three
    # Uniform/independent-residue heuristic for k selected coordinates.
    k_for_expected_join_below_one = math.ceil(
        log2_total_secret_space / log2_q_over_width
    )
    k = min(n, max(1, k_for_expected_join_below_one))
    log2_expected_joined = (
        log2_total_secret_space - k * log2_q_over_width
    )
    log2_probe_work = log2_half_entries + k * log2_width

    # Payload-only lower bound: both half tables store N residues each.
    # Each residue is conservatively counted as ceil(log2(q)/8) bytes.
    residue_bytes = math.ceil(q.bit_length() / 8)
    log2_payload_bytes = (
        1 + log2_half_entries + math.log2(n) + math.log2(residue_bytes)
    )
    return {
        "n": n,
        "q_bits": q.bit_length(),
        "k": k,
        "log2_half_entries": log2_half_entries,
        "log2_secret_space": log2_total_secret_space,
        "log2_probes": log2_probe_work,
        "log2_expected_joined": log2_expected_joined,
        "log2_payload_bytes": log2_payload_bytes,
        "residue_bytes": residue_bytes,
    }


def fmt(x):
    return f"{x:.1f}"


def main():
    print("MITM scalability projection; eta=2; width=5")
    print("No large search is run. Entries are exact counts; joins use an independence heuristic.")
    print("N | qbits | k* | log2(half entries) | log2(probes) | log2(expected joins) | log2(payload bytes)")
    for n in DIMENSIONS:
        toy = projection(n, Q_TOY)
        paper = projection(n, Q_PAPER1)
        print(
            f"{n} | {paper['q_bits']} | {paper['k']} | "
            f"{fmt(paper['log2_half_entries'])} | {fmt(paper['log2_probes'])} | "
            f"{fmt(paper['log2_expected_joined'])} | {fmt(paper['log2_payload_bytes'])}"
        )
        assert paper["log2_half_entries"] == n / 2 * math.log2(3)
        assert paper["k"] <= n
        assert paper["log2_expected_joined"] <= 0
        assert toy["k"] <= n

    n = 8192
    p = projection(n, Q_PAPER1)
    print(
        f"Paper1 N=8192: split table entries per side=3^4096; "
        f"log2(entries)={fmt(p['log2_half_entries'])}; "
        f"selected k={p['k']}; log2(probe work)={fmt(p['log2_probes'])}; "
        f"log2(payload-only bytes)={fmt(p['log2_payload_bytes'])}."
    )
    print("Interpretation: the half-table itself is already infeasible; selected-coordinate filtering does not remove this exponential storage/build term.")
    print("Caveat: expected-join formula assumes uniform independent residues and ignores ring/constraint correlations; it is a heuristic workload model, not a theorem.")


if __name__ == "__main__":
    main()
