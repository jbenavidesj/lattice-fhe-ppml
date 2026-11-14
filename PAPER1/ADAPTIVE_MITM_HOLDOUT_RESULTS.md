# Held-out adaptive MITM selector experiment

## Protocol

The selector model and weight lambda=4 were frozen before this evaluation. The held-out instances use seed 0xC0FFEE, disjoint from the earlier development seed 0xBF2. Parameters are q=11, eta=2, B=3, three evaluation-key levels, and N in {4,6,8}. Ten held-out instances were generated per degree. For each instance, every fixed k in {1,2,3,4} was measured twice on the same instance; every MITM candidate set was compared exactly with exhaustive enumeration.

## Results

| N | Selector k | Fastest fixed k on held-out set | Median regret | k=1 median | k=2 median | k=3 median | k=4 median | Exact comparisons |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 1 | 1 | 1.000 | 0.000294 s | 0.000369 s | 0.001055 s | 0.004944 s | 40/40 |
| 6 | 2 | 2 | 1.000 | 0.001937 s | 0.001761 s | 0.003451 s | 0.014835 s | 40/40 |
| 8 | 2 | 2 | 1.000 | 0.015855 s | 0.011515 s | 0.014119 s | 0.046520 s | 40/40 |

Median regret is the ratio of the median runtime for the frozen selector's k to the lowest median runtime among fixed k values on this held-out set. A value of 1.000 means the selector matched the best median among the tested choices in this particular sample. It does not mean it chose the fastest k on every individual instance.

## Validation

CI run #434 (run ID 43345625418) completed successfully on commit b3a21b0330b55af39a14d7be8e945be7fbf351ca. The Python audit reported the parameter-grid formula audit passed 80 cases, and the held-out selector experiment passed. The Rust job also passed unit tests, formatting, Clippy, and benchmark-target compilation.

## Interpretation and limitations

The frozen selector matched the best fixed-k median for all three tested degrees on this held-out sample, with median regret 1.000. This is encouraging but narrow evidence: only ten instances per degree, one modulus, one error radius, three small even degrees, and a single CI environment. Runtime medians at this scale are sensitive to interpreter and host noise. The experiment does not establish generalization across q or eta, does not validate a production-degree selector, and is not a cryptanalytic attack or security result. A larger independently generated study with raw per-instance timings and uncertainty intervals is required before making a broad predictive claim.