#!/usr/bin/env python3
"""Deterministic parameter-grid audit for the toy MITM cost-model selector."""
import importlib.util
from pathlib import Path

path = Path(__file__).with_name("toy_evalkey_mitm.py")
spec = importlib.util.spec_from_file_location("toy_evalkey_mitm", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

cases = 0
for q in (11, 17, 31, 97):
    for eta in (0, 1, 2, 3):
        if q <= 2 * eta:
            continue
        for n in (4, 6, 8, 10, 12):
            result = module.choose_coordinates(
                n, q=q, eta=eta, candidate_ks=range(1, min(n, 5) + 1)
            )
            k = result["k"]
            width = 2 * eta + 1
            expected_probes = 3 ** (n // 2) * width ** k
            expected_hits = 3 ** n * (width / q) ** k
            assert result["estimated_probes"] == expected_probes
            assert abs(result["estimated_joined_pairs"] - expected_hits) < 1e-9
            assert 1 <= k <= min(n, 5)
            cases += 1

# The default parameters must preserve the established choices.
assert [module.choose_coordinates(n)["k"] for n in (4, 6, 8)] == [1, 2, 2]
print(f"MITM selector parameter-grid audit passed: {cases} cases; default choices preserved.")
