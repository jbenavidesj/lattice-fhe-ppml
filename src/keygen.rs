//! Candidate RNS-BFV key generation using the operating-system CSPRNG.
//!
//! Experimental construction only; not security-reviewed.

use crate::rns::{RnsEvalKeyDigit, RnsPoly};
use crate::{mul_mod, MODULI};
use getrandom::getrandom;

pub const RNS_DEGREE: usize = 8192;
pub const DEFAULT_GADGET_BASE: u64 = 1 << 16;

#[derive(Debug)]
pub enum KeyGenError { Entropy(getrandom::Error), Arithmetic(&'static str) }
impl From<getrandom::Error> for KeyGenError { fn from(e: getrandom::Error) -> Self { Self::Entropy(e) } }
impl From<&'static str> for KeyGenError { fn from(e: &'static str) -> Self { Self::Arithmetic(e) } }

#[derive(Debug)]
pub struct RnsSecretKey(RnsPoly);
impl RnsSecretKey {
    pub(crate) fn as_poly(&self) -> &RnsPoly { &self.0 }
}

impl Drop for RnsSecretKey {
    fn drop(&mut self) { self.0.zeroize(); }
}

#[derive(Debug)]
pub struct RnsEvaluationKey { pub digits: Vec<RnsEvalKeyDigit>, pub gadget_base: u64 }

/// Generate a ternary secret and centered-binomial-error relinearization key.
/// For each j: b_j = B^j*s^2 - a_j*s + e_j (mod Q).
/// This candidate has no RLWE estimate, side-channel review, or zeroization guarantee.
pub fn generate_relinearization_key() -> Result<(RnsSecretKey, RnsEvaluationKey), KeyGenError> {
    generate_relinearization_key_with_base(DEFAULT_GADGET_BASE)
}

pub fn generate_relinearization_key_with_base(base: u64) -> Result<(RnsSecretKey, RnsEvaluationKey), KeyGenError> {
    if base < 2 { return Err(KeyGenError::Arithmetic("gadget base must be >= 2")); }
    let secret = encode_signed(&sample_ternary(RNS_DEGREE)?)?;
    let secret_squared = secret.negacyclic_mul(&secret)?;
    let levels = RnsPoly::gadget_levels(base)?;
    let mut digits = Vec::with_capacity(levels);
    let mut factors = [1u64; 4];
    for _ in 0..levels {
        let a = sample_uniform_rq(RNS_DEGREE)?;
        let error = encode_signed(&sample_centered_binomial_eta2(RNS_DEGREE)?)?;
        let a_times_s = a.negacyclic_mul(&secret)?;
        let target = scalar_mul_lanes(&secret_squared, factors)?;
        let b = target.add(&negate(&a_times_s)?)?.add(&error)?;
        digits.push(RnsEvalKeyDigit { a, b });
        for (i, factor) in factors.iter_mut().enumerate() {
            *factor = mul_mod(*factor, base % MODULI[i], MODULI[i]);
        }
    }
    Ok((RnsSecretKey(secret), RnsEvaluationKey { digits, gadget_base: base }))
}

fn random_u64() -> Result<u64, KeyGenError> {
    let mut bytes = [0u8; 8]; getrandom(&mut bytes)?; Ok(u64::from_le_bytes(bytes))
}

/// Unbiased sample in [0,q) using 64-bit rejection sampling.
fn sample_uniform_mod_q(q: u64) -> Result<u64, KeyGenError> {
    if q < 2 { return Err(KeyGenError::Arithmetic("modulus must be >= 2")); }
    let range = 1u128 << 64;
    let limit = (range / q as u128) * q as u128;
    loop { let x = random_u64()? as u128; if x < limit { return Ok((x % q as u128) as u64); } }
}

fn sample_uniform_rq(n: usize) -> Result<RnsPoly, KeyGenError> {
    let mut lanes: [Vec<u64>; 4] = std::array::from_fn(|_| Vec::with_capacity(n));
    for (i, lane) in lanes.iter_mut().enumerate() {
        for _ in 0..n { lane.push(sample_uniform_mod_q(MODULI[i])?); }
    }
    Ok(RnsPoly::from_lanes(lanes)?)
}

/// Uniform over {-1,0,1}; rejection avoids modulo bias.
fn sample_ternary(n: usize) -> Result<Vec<i64>, KeyGenError> {
    let mut out = Vec::with_capacity(n);
    while out.len() < n {
        let mut byte = [0u8; 1]; getrandom(&mut byte)?;
        if byte[0] <= 251 { out.push((byte[0] % 3) as i64 - 1); }
    }
    Ok(out)
}

/// eta=2 centered binomial: popcount(two low bits)-popcount(two high bits).
fn sample_centered_binomial_eta2(n: usize) -> Result<Vec<i64>, KeyGenError> {
    let mut bytes = vec![0u8; n]; getrandom(&mut bytes)?;
    Ok(bytes.into_iter().map(|x| (x & 3).count_ones() as i64 - ((x >> 2) & 3).count_ones() as i64).collect())
}

fn encode_signed(values: &[i64]) -> Result<RnsPoly, KeyGenError> {
    let lanes = std::array::from_fn(|i| values.iter().map(|&x| {
        if x >= 0 { (x as u64) % MODULI[i] } else {
            let magnitude = x.unsigned_abs() % MODULI[i];
            if magnitude == 0 { 0 } else { MODULI[i] - magnitude }
        }
    }).collect());
    Ok(RnsPoly::from_lanes(lanes)?)
}

fn negate(poly: &RnsPoly) -> Result<RnsPoly, KeyGenError> {
    let lanes = std::array::from_fn(|i| poly.lanes()[i].iter().map(|&x| if x == 0 { 0 } else { MODULI[i] - x }).collect());
    Ok(RnsPoly::from_lanes(lanes)?)
}

fn scalar_mul_lanes(poly: &RnsPoly, factors: [u64; 4]) -> Result<RnsPoly, KeyGenError> {
    let lanes = std::array::from_fn(|i| poly.lanes()[i].iter().map(|&x| mul_mod(x, factors[i], MODULI[i])).collect());
    Ok(RnsPoly::from_lanes(lanes)?)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn rejection_sampler_outputs_canonical_residues() {
        for &q in &MODULI { for _ in 0..128 { assert!(sample_uniform_mod_q(q).unwrap() < q); } }
    }
    #[test] fn ternary_and_eta2_supports_are_exact() {
        let s = sample_ternary(4096).unwrap(); assert!(s.iter().all(|x| (-1..=1).contains(x)));
        let e = sample_centered_binomial_eta2(4096).unwrap(); assert!(e.iter().all(|x| (-2..=2).contains(x)));
        assert!(e.contains(&-2)); assert!(e.contains(&2));
    }
    #[test]
    fn generated_evaluation_key_satisfies_sampled_coefficient_relations() {
        let (secret, evaluation_key) = generate_relinearization_key().unwrap();
        assert_eq!(evaluation_key.gadget_base, DEFAULT_GADGET_BASE);
        assert_eq!(evaluation_key.digits.len(), RnsPoly::gadget_levels(DEFAULT_GADGET_BASE).unwrap());
        let s2 = secret.0.negacyclic_mul(&secret.0).unwrap();
        let mut factors = [1u64; 4];
        for digit in &evaluation_key.digits {
            let as_product = digit.a.negacyclic_mul(&secret.0).unwrap();
            let phase = digit.b.add(&as_product).unwrap();
            let target = scalar_mul_lanes(&s2, factors).unwrap();
            let residual = phase.add(&negate(&target).unwrap()).unwrap();
            // Exhaustively reconstruct every coefficient of every generated
            // evaluation-key digit and verify the centered error support.
            for index in 0..RNS_DEGREE {
                let value = residual.crt_reconstruct_centered_coefficient(index).unwrap();
                assert!(value >= num_bigint::BigInt::from(-2)
                    && value <= num_bigint::BigInt::from(2),
                    "sampled evaluation-key error coefficient out of eta=2 support: {value}");
            }
            for (i, factor) in factors.iter_mut().enumerate() {
                *factor = mul_mod(*factor, DEFAULT_GADGET_BASE % MODULI[i], MODULI[i]);
            }
        }
    }
    #[test] fn signed_encoding_is_consistent_across_crt_lanes() {
        let p = encode_signed(&[-2,-1,0,1,2]).unwrap();
        for i in 0..5 { assert_eq!(p.crt_reconstruct_centered_coefficient(i).unwrap(), num_bigint::BigInt::from(i as i64 - 2)); }
    }
}