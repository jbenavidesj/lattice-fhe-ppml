use criterion::{
    black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput,
};
use paper1_rns_bfv::{asymred, rns::RnsPoly, MODULI};
use std::time::Duration;

const N: usize = 8192;

fn deterministic_poly(seed: u64) -> RnsPoly {
    let lanes = std::array::from_fn(|lane| {
        let q = MODULI[lane];
        (0..N)
            .map(|i| {
                let x = (i as u64)
                    .wrapping_mul(0x9e37_79b9_7f4a_7c15)
                    .wrapping_add(seed.wrapping_mul(0xbf58_476d_1ce4_e5b9))
                    .wrapping_add((lane as u64) << 32);
                x % q
            })
            .collect()
    });
    RnsPoly::from_lanes(lanes).expect("deterministic benchmark polynomial is canonical")
}

fn arithmetic_benchmarks(c: &mut Criterion) {
    let q = MODULI[0];
    let delta = 16_793_599u64;
    let inputs: Vec<u128> = (0..20_000u128)
        .map(|i| {
            (i.wrapping_mul(0x9e37_79b9_7f4a_7c15u128) ^ (i << 61))
                % ((q as u128) * (q as u128))
        })
        .collect();

    c.bench_function("asymred_candidate_q1_20k", |b| {
        b.iter(|| {
            for &z in &inputs {
                black_box(asymred(black_box(z), q, 55, delta).unwrap());
            }
        })
    });

    c.bench_function("u128_remainder_baseline_q1_20k", |b| {
        b.iter(|| {
            for &z in &inputs {
                black_box(black_box(z) % q as u128);
            }
        })
    });

    let lhs = deterministic_poly(1);
    let rhs = deterministic_poly(2);
    let mut rns_group = c.benchmark_group("rns_ntt_negacyclic_multiplication");
    rns_group.throughput(Throughput::Elements(N as u64));
    rns_group.bench_function(BenchmarkId::new("N8192_four_lanes", N), |b| {
        b.iter(|| black_box(black_box(&lhs).negacyclic_mul(black_box(&rhs)).unwrap()))
    });
    rns_group.finish();

    let c0 = deterministic_poly(3);
    let c1 = deterministic_poly(4);
    let d0 = deterministic_poly(5);
    let d1 = deterministic_poly(6);
    let mut tensor_group = c.benchmark_group("bfv_tensor_multiplication_exact_reference");
    tensor_group.sample_size(10);
    tensor_group.measurement_time(Duration::from_secs(10));
    tensor_group.throughput(Throughput::Elements(N as u64));
    tensor_group.bench_function(BenchmarkId::new("N8192_t65537", N), |b| {
        b.iter(|| {
            black_box(
                RnsPoly::bfv_tensor_multiply(
                    black_box(&c0),
                    black_box(&c1),
                    black_box(&d0),
                    black_box(&d1),
                    65_537,
                )
                .unwrap(),
            )
        })
    });
    tensor_group.finish();
}

criterion_group!(benches, arithmetic_benchmarks);
criterion_main!(benches);
