//! Residue-number-system polynomial representation over the four candidate q_i.
//! CRT reconstruction is exact. Basis extension uses the centered CRT representative,
//! a semantic distinction required by signed polynomial arithmetic.
use num_bigint::{BigInt, BigUint, Sign};
use crate::{ntt::negacyclic_ntt_mul, pow_mod, sub_mod, MODULI, ROOTS};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RnsPoly {
    lanes: [Vec<u64>; 4],
}

impl RnsPoly {
    pub fn from_lanes(lanes: [Vec<u64>; 4]) -> Result<Self, &'static str> {
        let n = lanes[0].len();
        if n == 0 || lanes.iter().any(|lane| lane.len() != n) {
            return Err("all RNS lanes must have the same nonzero length");
        }
        for (i, lane) in lanes.iter().enumerate() {
            if lane.iter().any(|&x| x >= MODULI[i]) {
                return Err("coefficient is not canonical for its modulus");
            }
        }
        Ok(Self { lanes })
    }

    pub fn lanes(&self) -> &[Vec<u64>; 4] { &self.lanes }

    pub fn add(&self, rhs: &Self) -> Result<Self, &'static str> {
        if self.lanes[0].len() != rhs.lanes[0].len() {
            return Err("RNS polynomial dimensions differ");
        }
        let lanes = std::array::from_fn(|i| {
            self.lanes[i].iter().zip(&rhs.lanes[i])
                .map(|(&a, &b)| crate::add_mod(a, b, MODULI[i])).collect()
        });
        Ok(Self { lanes })
    }

    /// Reconstruct one coefficient in the canonical interval [0,Q), exactly.
    /// Assumes the configured q_i are pairwise coprime primes.
    pub fn crt_reconstruct_coefficient(&self, index: usize) -> Result<BigUint, &'static str> {
        if index >= self.lanes[0].len() { return Err("coefficient index out of range"); }
        let mut x = BigUint::from(0u8);
        let mut product = BigUint::from(1u8);
        for (i, &q) in MODULI.iter().enumerate() {
            let x_mod = low_u64(&(&x % q));
            let product_mod = low_u64(&(&product % q));
            let inverse = pow_mod(product_mod, q - 2, q);
            let correction = crate::mul_mod(sub_mod(self.lanes[i][index], x_mod, q), inverse, q);
            x += &product * BigUint::from(correction);
            product *= BigUint::from(q);
        }
        Ok(x)
    }

    /// Return the signed centered representative in (-Q/2,Q/2].
    pub fn crt_reconstruct_centered_coefficient(&self, index: usize) -> Result<BigInt, &'static str> {
        let x = self.crt_reconstruct_coefficient(index)?;
        let q_product = MODULI.iter().fold(BigUint::from(1u8), |p, &q| p * BigUint::from(q));
        if (&x << 1usize) > q_product {
            Ok(BigInt::from_biguint(Sign::Plus, x) - BigInt::from_biguint(Sign::Plus, q_product))
        } else {
            Ok(BigInt::from_biguint(Sign::Plus, x))
        }
    }

    /// Exact centered basis extension: reconstruct each coefficient as its signed
    /// representative modulo Q, then reduce that integer into every target modulus.
    /// This is exact extension, not an approximate fast base-conversion algorithm.
    pub fn basis_extend_centered(&self, target_moduli: &[u64]) -> Result<Vec<Vec<u64>>, &'static str> {
        if target_moduli.is_empty() || target_moduli.iter().any(|&q| q < 2) {
            return Err("target basis must contain moduli >= 2");
        }
        let mut output = vec![Vec::with_capacity(self.lanes[0].len()); target_moduli.len()];
        for index in 0..self.lanes[0].len() {
            let signed = self.crt_reconstruct_centered_coefficient(index)?;
            for (lane, &q) in output.iter_mut().zip(target_moduli) {
                let residue = (&signed % BigInt::from(q) + BigInt::from(q)) % BigInt::from(q);
                lane.push(low_u64(&residue.to_biguint().ok_or("negative residue after normalization")?));
            }
        }
        Ok(output)
    }

    /// Negacyclic multiplication by NTT in each residue field. Candidate roots are fixed for N=8192.
    pub fn negacyclic_mul(&self, rhs: &Self) -> Result<Self, &'static str> {
        if self.lanes[0].len() != rhs.lanes[0].len() {
            return Err("RNS polynomial dimensions differ");
        }
        let n = self.lanes[0].len();
        if !n.is_power_of_two() || n != 8192 {
            return Err("candidate roots in this crate are specified for N=8192");
        }
        let lanes = std::array::from_fn(|i| {
            negacyclic_ntt_mul(&self.lanes[i], &rhs.lanes[i], MODULI[i], ROOTS[i])
        });
        Ok(Self { lanes })
    }
}

fn low_u64(x: &BigUint) -> u64 { x.to_u64_digits().first().copied().unwrap_or(0) }

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn four_lane_addition_is_canonical() {
        let a = RnsPoly::from_lanes(std::array::from_fn(|i| vec![MODULI[i]-1, 1])).unwrap();
        let b = RnsPoly::from_lanes(std::array::from_fn(|i| vec![2, MODULI[i]-1])).unwrap();
        let c = a.add(&b).unwrap();
        for (i, lane) in c.lanes().iter().enumerate() {
            assert_eq!(lane, &vec![1, 0]);
            assert!(lane.iter().all(|&x| x < MODULI[i]));
        }
    }

    #[test]
    fn crt_reconstructs_values_beyond_u128() {
        let value = (BigUint::from(1u8) << 200usize) + BigUint::from(987654321u64);
        let lanes = std::array::from_fn(|i| {
            let q = MODULI[i];
            vec![low_u64(&(&value % q))]
        });
        let rns = RnsPoly::from_lanes(lanes).unwrap();
        assert_eq!(rns.crt_reconstruct_coefficient(0).unwrap(), value);
    }

    #[test]
    fn centered_crt_and_basis_extension_preserve_signed_value() {
        let signed = BigInt::from(-1234567890123456789i128);
        let lanes = std::array::from_fn(|i| {
            let q = MODULI[i];
            let r = (&signed % BigInt::from(q) + BigInt::from(q)) % BigInt::from(q);
            vec![low_u64(&r.to_biguint().unwrap())]
        });
        let rns = RnsPoly::from_lanes(lanes).unwrap();
        assert_eq!(rns.crt_reconstruct_centered_coefficient(0).unwrap(), signed);
        let targets = [65537u64, 1000000007u64];
        let extended = rns.basis_extend_centered(&targets).unwrap();
        for (i, &q) in targets.iter().enumerate() {
            let expected = (&signed % BigInt::from(q) + BigInt::from(q)) % BigInt::from(q);
            assert_eq!(extended[i][0], low_u64(&expected.to_biguint().unwrap()));
        }
    }

    #[test]
    fn rejects_mismatched_lanes() {
        let bad = [vec![0, 1], vec![0], vec![0, 1], vec![0, 1]];
        assert!(RnsPoly::from_lanes(bad).is_err());
    }
}
