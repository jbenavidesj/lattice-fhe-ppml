#!/usr/bin/env sage -python
"""
Diagnostic unstructured-LWE proxy for the Paper 1 power-of-two RLWE candidate.

This is NOT a ring-LWE estimator and its output must not be labelled the
scheme's security level. It is a reproducible baseline under the HE Standard
heuristic that estimates the corresponding unstructured LWE instance.
Run in an environment with SageMath and malb/lattice-estimator installed:
    sage -python scripts/estimate_lwe_proxy.py
Record the estimator commit, Sage version, full stdout, and cost model.
"""
from math import log2
from sage.all import oo
from estimator import LWE, ND

N = 8192
Q = 421249165630599354127590185589164472945208468246547404789529362433
ETA = 2

params = LWE.Parameters(
    n=N,
    q=Q,
    Xs=ND.Ternary,
    Xe=ND.CenteredBinomial(ETA),
    m=oo,
    tag="Paper1-RLWE-to-unstructured-LWE diagnostic only",
)

print(f"n={N}")
print(f"q={Q}")
print("secret=coefficientwise ternary {-1,0,1}")
print(f"error=centered-binomial eta={ETA}, coefficient stddev=1")
print("WARNING: this is an unstructured-LWE proxy, not a ring-LWE certificate.")
results = LWE.estimate(params)
for attack, cost in results.items():
    try:
        bits = log2(float(cost.rop))
    except (AttributeError, TypeError, ValueError, OverflowError):
        bits = float("inf")
    print(f"{attack}: log2(rop)={bits:.3f}; details={cost}")
