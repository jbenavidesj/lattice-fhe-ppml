# Independent review package — Paper 1

This document is a checklist for external technical review. It is not evidence that review has occurred.

## Review A: correctness and noise analysis

Please independently verify:
1. The centered representative convention for each ciphertext component.
2. The auxiliary NTT/CRT product bound, including the strict inequality guaranteeing unique integer reconstruction.
3. The BFV quotient/carry decomposition and every scale-rounding term.
4. The coefficient norm inequalities under negacyclic multiplication.
5. The gadget digit bound and key-switch error bound.
6. The final strict comparison with the decoding margin.
7. Every implicit assumption: sampler support, independence, modulus conditions, and plaintext representative.

Required outcome: written derivation or exact corrections. Do not merely rerun the audit script; review the mathematics independently.

## Review B: cryptographic security

Please assess the exact joint public transcript:
- One conventional public-key sample with ternary secret and eta=2 error.
- Fourteen evaluation-key equations b_j+a_j*s=B^j*s^2+e_j mod Q.
- Actual four-prime Q, N=8192, t=65537, B=2^16, L=14.
- Exact secret and error distributions.

Questions:
1. Which attacks apply to the joint transcript?
2. Can the relation s^2 and ternary constraint be exploited algebraically?
3. Do adjacent-level cancellations produce useful equations after exact centered-lift analysis?
4. Which lattice-estimator models are justified, and what do they omit?
5. What additional samples or interfaces materially change the attack surface?
6. What security claim, if any, is supportable?

Required outcome: written threat-model assessment, applicable attack families, assumptions, and justified bounds—or an explicit statement that no defensible estimate is currently available.

## Review C: implementation and side channels

Inspect secret-dependent branches and memory accesses; sampler and entropy source; temporary copies, object lifetime and zeroization; CRT/NTT overflow and parameter misuse; compiler/target-feature assumptions; error handling and malformed parameters.

Required outcome: concrete findings and a reproducible test/review record.

## Evidence handling

Record reviewer identity/affiliation only with permission, review date, commit hash, files/sections reviewed, exact findings, and resolution status. Never describe an internal self-check or automated CI run as independent review.