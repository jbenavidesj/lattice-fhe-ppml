# Mathematical Variance Bounds & Hardware Emulation Parameters

This document establishes the formal algebraic constraints, homogeneous noise-budget boundaries, and architectural parameters under which the multiplicative depth expansion and latency improvements (detailed in Paper 1) are modeled for the **RNS-BFV** scheme.

## 1. Modular Parameter Selection
To ensure strict compliance with Number Theoretic Transform (NTT) execution loops and constant-time asymmetric modular reduction (`AsymRed`), the prime moduli $q_i$ and cyclotomic polynomial degree $n$ are tightly bound over $R_q = \mathbb{Z}_q[X] / \langle X^n + 1 \rangle$:
- **Ring Dimension ($n$):** $4096 / 8192$ (Power of 2 supporting radix-2 NTT butterflies)
- **Ciphertext Modulus ($\log q$):** $109 / 218$ bits (Decomposed via coprime pseudo-Mersenne primes $q_i = 2^w - \delta_i$, where $0 < \delta_i < 2^{w/2}$ and $w = 64$)
- **Plaintext Modulus ($t$):** Prime integer co-prime to $q$
- **Error Distribution ($\chi$):** Discrete Gaussian distribution with standard deviation $\sigma = 3.2$

## 2. Homogeneous Noise Growth & Variance Bounds
In standard RNS-BFV implementations, homomorphic multiplication followed by Barrett or Montgomery reduction leaves intermediate residues in $[0, 2q_i)$, introducing rounding variance during Fast Base Conversion and immediate relinearization.

By enforcing canonical residues strictly within $[0, q_i - 1]$ via constant-time bitwise masking (`AsymRed`) coupled with **Lazy Relinearization**, the framework eliminates intermediate rounding drift. Both variance bounds share identical algebraic dimensions:

- **Baseline Reference (Standard Reduction + Immediate Relinearization):**
  $$\text{Var}(\mathbf{e}_{\text{std}}) \approx C_1 \cdot n \cdot \sigma^2 \cdot t^2 + V_{\text{relin}}$$

- **Proposed Architecture (Canonical Asymmetric Reduction + Lazy Relinearization):**
  $$\text{Var}(\mathbf{e}_{\text{asym}}) \approx \alpha \cdot \left( C_1 \cdot n \cdot \sigma^2 \cdot t^2 \right) + V_{\text{relin\_lazy}}$$

Where $C_1$ denotes the canonical embedding expansion constant of the cyclotomic ring and $\alpha \in (0, 1)$ represents the empirical RNS rounding suppression factor (targeted at $\alpha \approx 0.66$).

## 3. Separation of Performance Metrics
To maintain analytical precision across theoretical and hardware benchmarks, algebraic capacity and execution speed are evaluated independently:

- **Bootstrapping Frequency Reduction ($\approx 33.8\%$ – $34.0\%$):** Driven by noise-budget preservation. With a total noise budget $B = \log_2(q) - \log_2(t)$, consuming $\approx 34\%$ less noise variance per multiplicative layer increases the maximum multiplicative depth $L = \lfloor B / b_{\text{layer}} \rfloor$ by a factor of $\approx 1.51\times$, proportionally reducing bootstrapping calls in deep circuits.
- **NTT & Modular Reduction Speedup ($\approx 34.2\%$):** Driven by microarchitectural instruction reduction. Replacing 128-bit Barrett/Montgomery multiplications with bit-shifts and small-$\delta_i$ additions reduces CPU clock cycles per NTT butterfly operation.

## 4. Emulation Environment & Verification Flags
Hardware-software co-design safety evaluations target deterministic execution environments:
- **Architecture Target:** Intel Xeon Scalable Processors (Gold/Platinum topologies)
- **Instruction Vector Extensions:** AVX-512F, AVX-512DQ (Enforcing constant-time execution flows via `_mm512_add_epi64`, `_mm512_srli_epi64`, and bitwise masking without secret-dependent branches)
- **Kernel Directives:** Memory isolation via restricted execution pools to mitigate instruction-cache profiling and microarchitectural timing leakages.
