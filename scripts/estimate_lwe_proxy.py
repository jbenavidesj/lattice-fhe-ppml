#!/usr/bin/env sage -python
"""
Diagnostic unstructured-LWE proxy for the Paper 1 power-of-two RLWE candidate.

This is NOT a ring-LWE estimator or a security certificate. It compares:
  (A) the candidate: n=8192, q=the exact four-prime product, ternary secret,
      centered-binomial eta=2 error (standard deviation 1);
  (B) an HE Standard v2 reference: n=8192, q=2^214, ternary secret,
      discrete-Gaussian error with standard deviation 3.19.

Each case is estimated with m=N (one flattened RLWE sample as an LWE proxy)
and m=infinity (the estimator's conservative unlimited-sample setting).
Evaluation-key samples are NOT modelled as ordinary LWE samples because their
target contains s^2; a separate analysis is required for that exposure.

Reproducible environment:
  git clone https://github.com/malb/lattice-estimator
  cd lattice-estimator
  git checkout 7d59f866655362ea8eab803dbc833710c2bc362a
  sage -pip install -e .
  sage -python /path/to/scripts/estimate_lwe_proxy.py

Record the full stdout, Sage version, exact estimator commit, and cost model.
Do not report the output as a Ring-LWE security level.
"""
from pathlib import Path
import subprocess

from sage.all import log, oo
from sage.env import SAGE_VERSION
import estimator
from estimator import LWE, ND

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
            "Cannot verify estimator checkout: install from the pinned Git repository "
            "rather than an unversioned package."
        )
    actual = subprocess.check_output(
        ["git", "-C", str(package_root), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != ESTIMATOR_COMMIT:
        raise SystemExit(
            f"Wrong lattice-estimator commit: expected {ESTIMATOR_COMMIT}, got {actual}"
        )
    print(f"lattice-estimator commit: {actual}")
    print(f"SageMath version: {SAGE_VERSION}")


def estimate_case(label, q, error_distribution, sample_count):
    params = LWE.Parameters(
        n=N,
        q=q,
        Xs=ND.Ternary,
        Xe=error_distribution,
        m=sample_count,
        tag=f"{label}; m={sample_count}",
    )
    print(f"\n[{label}] n={N}; q={q}; m={sample_count}")
    results = LWE.estimate(params, quiet=True)
    finite_costs = []
    for attack, cost in sorted(results.items()):
        rop = cost.rop
        if rop == oo:
            print(f"{attack}: no finite estimate; details={cost}")
            continue
        bits = float(log(rop, 2))
        finite_costs.append(bits)
        print(f"{attack}: log2(rop)={bits:.4f}; details={cost}")
    if finite_costs:
        print(f"minimum estimated attack cost: {min(finite_costs):.4f} bits")
    else:
        print("No finite attack cost returned; investigate estimator coverage.")


def main():
    verify_estimator_checkout()
    print("WARNING: unstructured-LWE heuristic only; not a ring-LWE certificate.")
    print("Evaluation-key samples are not modelled in this diagnostic.")
    for sample_count in (N, oo):
        estimate_case(
            "Paper1 candidate, eta=2 centered-binomial",
            Q_CANDIDATE,
            ND.CenteredBinomial(ETA),
            sample_count,
        )
        estimate_case(
            "HE Standard v2 comparison, Gaussian sigma=3.19",
            Q_HES_V2,
            ND.DiscreteGaussian(3.19),
            sample_count,
        )


if __name__ == "__main__":
    main()
