use criterion::{black_box, criterion_group, criterion_main, Criterion};
use paper1_rns_bfv::{asymred, MODULI};

fn arithmetic_benchmarks(c: &mut Criterion) {
    let q = MODULI[0];
    let delta = 16_793_599u64;
    let inputs: Vec<u128> = (0..20_000u128)
        .map(|i| {
            (i.wrapping_mul(0x9e3779b97f4a7c15u128) ^ (i << 61))
                % ((q as u128) * (q as u128))
        })
        .collect();

    c.bench_function("asymred_candidate_q1", |b| {
        b.iter(|| {
            for &z in &inputs {
                black_box(asymred(black_box(z), q, 55, delta).unwrap());
            }
        })
    });

    c.bench_function("u128_remainder_baseline_q1", |b| {
        b.iter(|| {
            for &z in &inputs {
                black_box(black_box(z) % q as u128);
            }
        })
    });
}

criterion_group!(benches, arithmetic_benchmarks);
criterion_main!(benches);
