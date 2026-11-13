#!/usr/bin/env sage -python
"""
Preliminary, bounded-cost unstructured-LWE proxy for Paper 1.

This first-pass diagnostic deliberately uses the estimator's documented
LWE.estimate.rough() profile and m=N only. That profile evaluates uSVP and
dual-hybrid estimates, avoiding the full default attack sweep (notably BKW,
BDD variants, and Arora-GB) that exceeded the previous CI time budget.

This is NOT a Ring-LWE estimator or a security certificate. It also does not
model evaluation-key samples whose target contains s^2. A successful run
provides a screening comparison only; it is not a final security estimate.

Pinned environment:
  lattice-estimator commit 7d59f866655362ea8eab803dbc833710c2bc362a
  SageMath version is printed at runtime.
"""
from pathlib import Path
import subprocess

from sage.all import log, oo
from sage.env import SAGE_VERSION
import estimator
from estimator import LWE, ND
from estimator.conf import red_cost_model, red_shape_model

ESTIMATOR_COMMIT = "7d59f866655362ea8eab803dbc833710c2bc362a"
N = 8192
Q_CANDIDATE = 421249165630599354127590185589164472945208468246547404789529362433
ETA = 2
Q_HES_V2 = 2**214


def verify_estimator_checkout():
    package_root = Path(estimator.__file__).resolve().parent.parent
    git_dir = package_root / ".git"
    if not git_dir.exists():
        raise SystemExit(
            "Cannot verify estimator checkout: install from the pinned Git repository."
        )
    actual = subprocess.check_output(
        ["git", "-C", str(package_root), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != ESTIMATOR_COMMIT:
        raise SystemExit(
            f"Wrong lattice-estimator commit: expected {ESTIMATOR_COMMIT}, got {actual}"
        )
    print(f"lattice-estimator commit: {actual}", flush=True)
    print(f"SageMath version: {SAGE_VERSION}", flush=True)
    print(f"reduction cost model: {red_cost_model}", flush=True)
    print(f"reduction shape model: {red_shape_model}", flush=True)


def estimate_case(label, q, error_distribution):
    params = LWE.Parameters(
        n=N,
        q=q,
        Xs=ND.Ternary,
        Xe=error_distribution,
        m=N,
        tag=f"{label}; rough profile; m=N",
    )
    print(f"\n[{label}] n={N}; q={q}; m={N}; profile=rough", flush=True)
    # The documented rough profile limits the attack sweep to uSVP and
    # dual-hybrid. It is a preliminary screen, not the full default estimator.
    results = LWE.estimate.rough(
        params, jobs=1, catch_exceptions=True, quiet=False
    )
    finite_costs = []
    for attack, cost in sorted(results.items()):
        rop = cost.get("rop", oo)
        if rop == oo:
            print(f"{attack}: no finite estimate; details={cost!r}", flush=True)
            continue
        bits = float(log(rop, 2))
        finite_costs.append(bits)
        print(f"{attack}: log2(rop)={bits:.4f}; details={cost!r}", flush=True)
    if finite_costs:
        print(
            f"minimum rough estimated attack cost: {min(finite_costs):.4f} bits",
            flush=True,
        )
    else:
        print("No finite rough attack cost returned.", flush=True)


def main():
    verify_estimator_checkout()
    print(
        "WARNING: preliminary unstructured-LWE rough profile only; "
        "not a Ring-LWE certificate.",
        flush=True,
    )
    print("Evaluation-key samples are not modelled.", flush=True)
    estimate_case(
        "Paper1 candidate, eta=2 centered-binomial",
        Q_CANDIDATE,
        ND.CenteredBinomial(ETA),
    )
    estimate_case(
        "HE Standard v2 comparison, Gaussian sigma=3.19",
        Q_HES_V2,
        ND.DiscreteGaussian(3.19),
    )


if __name__ == "__main__":
    main()
